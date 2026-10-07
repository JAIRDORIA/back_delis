"""
Utilidades de acceso a la base de datos.

SnackFlow usa Flask-MySQLdb: `MySQL(app)` deja la conexion en
`current_app.mysql.connection` y la abre por request; la extension la cierra
sola al terminar la peticion (teardown_request). El problema que causo el
`1226 - max_user_connections exceeded` no eran las conexiones, sino los
CURSORES: cada `.cursor()` abierto ocupa un hilo/conexion del lado del driver
hasta que se cierra, y muchos services solo lo cerraban en el camino feliz.

`cursor_ctx` garantiza el cierre del cursor en el `finally`, pase lo que pase
(exito, excepcion o return temprano), sin cambiar el patron de obtencion del
cursor ni la transaccion (commit/rollback se siguen haciendo donde estaban).
"""
from contextlib import contextmanager

from flask import current_app


@contextmanager
def cursor_ctx():
    """
    Context manager que abre un cursor sobre la conexion de Flask-MySQLdb y
    SIEMPRE lo cierra al salir del bloque, incluso si hay excepcion.

    Uso:
        with cursor_ctx() as c:
            c.execute(...)
            datos = c.fetchall()

    El commit/rollback se sigue haciendo dentro del bloque, como hasta ahora:
    cerrar el cursor NO afecta a la transaccion ya confirmada.
    """
    c = current_app.mysql.connection.cursor()
    try:
        yield c
    finally:
        c.close()
