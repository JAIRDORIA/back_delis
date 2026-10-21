"""
Utilidades de acceso a la base de datos.

SnackFlow usa Flask-MySQLdb con SQL crudo. Antes, cada request abría una
conexión MySQL nueva (la extensión la guardaba en `g.mysql_db` y la cerraba
en el teardown). Con el plan free de Clever Cloud (5 conexiones por usuario),
varios requests simultáneos agotaban el límite (1226).

Este módulo añade un pool de conexiones POR PROCESO:

- Cada worker de gunicorn tiene su propia cola (creada perezosamente en el
  primer request; compatible con fork, por eso NO usar `--preload`).
- `app.mysql` se reemplaza por `PoolMySQL` (proxy) para que los services
  sigan usando `current_app.mysql.connection` sin cambios.
- La conexión prestada se guarda en `g._pool_conn` (NUNCA `g.mysql_db`) para
  que el teardown de Flask-MySQLdb no la cierre. `init_pool(app)` registra
  `_liberar`, que devuelve la conexión limpia al pool al terminar el request.

Variables de entorno:
- DB_POOL_SIZE (default 2): conexiones por proceso.
- DB_POOL_TIMEOUT (default 10): segundos de espera por un slot libre.
- DB_POOL_ENABLED (default 1): "0" desactiva el pool y deja el
  comportamiento original de Flask-MySQLdb.
"""
import os
import queue
import threading
from contextlib import contextmanager

from flask import current_app, g
from MySQLdb import OperationalError


def _env_int(nombre, default):
    try:
        return int(os.getenv(nombre, str(default)))
    except (TypeError, ValueError):
        return default


_POOL_SIZE = max(1, _env_int("DB_POOL_SIZE", 2))
_POOL_TIMEOUT = _env_int("DB_POOL_TIMEOUT", 10)

_pool = None
_pool_lock = threading.Lock()
_conexiones_vivas = 0


def _get_pool():
    """Devuelve la cola del proceso, creándola perezosamente."""
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                _pool = queue.LifoQueue(maxsize=_POOL_SIZE)
    return _pool


def _nueva_conexion():
    """Reserva un slot y crea una conexión nueva.

    Usa la configuración de Flask-MySQLdb (MYSQL_HOST/USER/PASSWORD/...).
    Lanza Exception si el pool ya tiene todas sus conexiones vivas."""
    global _conexiones_vivas
    with _pool_lock:
        if _conexiones_vivas >= _POOL_SIZE:
            raise Exception(
                "No hay conexión disponible en el pool de base de datos "
                "(DB_POOL_SIZE=%s). Intenta de nuevo." % _POOL_SIZE
            )
        _conexiones_vivas += 1
    return current_app.mysql.connect


def _descartar(conn):
    """Cierra y descuenta una conexión rota."""
    global _conexiones_vivas
    try:
        conn.close()
    except Exception:
        pass
    with _pool_lock:
        _conexiones_vivas -= 1


def _adquirir():
    """Presta una conexión del pool, creándola si hay cupo.

    Si el pool está lleno, espera hasta DB_POOL_TIMEOUT segundos por un slot
    liberado. Antes de prestar, verifica con ping() que la conexión siga viva
    (ping() hace rollback implícito, lo cual es correcto porque aún no empezó
    la transacción del request)."""
    pool = _get_pool()
    conn = None

    try:
        conn = pool.get_nowait()
    except queue.Empty:
        try:
            conn = _nueva_conexion()
        except Exception:
            # Sin cupo: esperar a que otro request devuelva una conexión.
            try:
                conn = pool.get(timeout=_POOL_TIMEOUT)
            except queue.Empty:
                raise Exception(
                    "No hay conexión disponible en el pool de base de datos "
                    "(DB_POOL_SIZE=%s). Intenta de nuevo." % _POOL_SIZE
                )

    try:
        conn.ping()
    except OperationalError:
        _descartar(conn)
        conn = _nueva_conexion()

    return conn


def _liberar(exc=None):
    """teardown_appcontext: devuelve la conexión limpia al pool.

    El rollback() siempre es seguro: si el request ya hizo commit(), no hay
    nada pendiente; si solo leyó (o falló), descarta la transacción abierta y
    evita que el siguiente request herede locks o datos a medias."""
    conn = getattr(g, "_pool_conn", None)
    if conn is None:
        return

    g._pool_conn = None
    try:
        conn.rollback()
    except Exception:
        _descartar(conn)
        return

    _get_pool().put(conn)


class PoolMySQL:
    """Proxy alrededor de flask_mysqldb.MySQL.

    `connection` devuelve la conexión prestada del pool (guardada en
    `g._pool_conn`, no en `g.mysql_db`, para que el teardown de la extensión
    no la cierre). `connect` delega en la extensión real y lo usa el pool
    para crear conexiones nuevas."""

    def __init__(self, ext):
        self._ext = ext

    @property
    def connect(self):
        return self._ext.connect

    @property
    def connection(self):
        conn = getattr(g, "_pool_conn", None)
        if conn is None:
            conn = _adquirir()
            g._pool_conn = conn
        return conn


def init_pool(app):
    """Registra la devolución de la conexión al final de cada request.

    Se registra después de `MySQL(app)`; Flask ejecuta los teardowns en orden
    inverso, así que `_liberar` corre antes que el de Flask-MySQLdb y este
    último no encuentra `g.mysql_db` (no cierra nada)."""
    app.teardown_appcontext(_liberar)


@contextmanager
def cursor_ctx():
    """Context manager que abre un cursor sobre la conexión del pool y
    SIEMPRE lo cierra al salir del bloque, incluso si hay excepción.

    El commit/rollback se sigue haciendo dentro del bloque, como hasta ahora:
    cerrar el cursor NO afecta a la transacción ya confirmada."""
    c = current_app.mysql.connection.cursor()
    try:
        yield c
    finally:
        c.close()
