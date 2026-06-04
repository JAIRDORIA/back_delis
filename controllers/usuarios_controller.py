from flask import jsonify , request
from  services.usuarios_servicies import listado_usuarios, registro, existe_username, eliminar, actualizar, obtener_usuario, existe_username_otro, existe_admin,  verificar_clave_maestra, cambiar_password_maestra
import re
import bcrypt
from services.usuarios_servicies import login
from jwt_config import generar_token 

def hashear_password(password_plano: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_plano.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def cntListado():
    try:
        pagina = int(request.args.get('pagina', 1))
        limite = int(request.args.get('limite', 20))

        if pagina < 1 or limite < 1:
            return jsonify({"mensaje": "pagina y limite deben ser mayores a 0"}), 400

        datos = listado_usuarios(pagina=pagina, limite=limite)
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def cntRegistro():
    #validar en la peticion(body) atributos requeridos
    requeridos = ['nombre', 'username', 'password', 'rol']

    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400
    
    #Validar que no existan campos vacios en los requeridos
    vacios = []
    for clave in request.json:
        if str(request.json[clave]).strip() == "":
            vacios.append(clave)

    if vacios:
        return jsonify({"mensaje": f"los siguientes campos no pueden estar vacios {vacios}"}), 400
    
    
    nombre   = request.json['nombre'] 
    username = request.json['username']
    password = request.json['password']
    rol      = request.json['rol']
    
    if existe_username(username):
        return jsonify({"mensaje": "El username ya existe"}), 400

    #validar campos 
    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"mensaje": "El nombre debe tener entre 3 y 100 caracteres"}), 400
    
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
       return jsonify({"mensaje": "El nombre solo puede contener letras"}), 400

    if len(username) < 4 or len(username) > 50:
        return jsonify({"mensaje": "El username debe tener entre 4 y 50 caracteres"}), 400

    if username.isdigit(): 
        return jsonify({"mensaje": "El username no puede contener solo números"}), 400

    if len(password) < 8 or len(password) > 50:
        return jsonify({"mensaje": "La contraseña debe tener entre 8 y 50 caracteres"}), 400
    
    patron_password = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]{8,128}$'

    if not re.match(patron_password, password):
        return jsonify({"mensaje": "La contraseña debe tener mayúscula, minúscula, número y carácter especial"}), 400
    
    password = hashear_password(password)
    
    if rol not in ['admin']:
        return jsonify({"mensaje": "El rol debe ser admin"}), 400
    
    p             = registro(nombre=nombre, username=username, password_hash=password, rol=rol)
    return jsonify({"mensaje":"Usuario registrado","datos":p}), 201

def cntEliminar(id):
    if not id:
        return jsonify({"mensaje": "El id es requerido"}), 400
    
    if not str(id).isdigit():
     return jsonify({"mensaje": "El id debe ser un número entero"}), 400
    
    eliminado = eliminar(id)
    
    if not eliminado:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify({"mensaje": "Usuario desactivado correctamente"}), 200

def cntActualizar(id):

    if not request.json:
        return jsonify({"mensaje": "Debe enviar datos"}), 400

    nombre   = request.json.get('nombre')
    username = request.json.get('username')
    password = request.json.get('password')
    rol      = request.json.get('rol')

    requeridos = ['nombre', 'username','rol']
    faltantes = [r for r in requeridos if not request.json.get(r)]
    if faltantes:
        return jsonify({"mensaje": f"faltan los siguientes campos {faltantes}"}), 400

    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"mensaje": "El nombre debe tener entre 3 y 100 caracteres"}), 400

    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
        return jsonify({"mensaje": "El nombre solo puede contener letras"}), 400
    
    if username.isdigit(): 
        return jsonify({"mensaje": "El username no puede contener solo números"}), 400
    
    if len(username) < 4 or len(username) > 50:
        return jsonify({"mensaje": "El username debe tener entre 4 y 50 caracteres"}), 400

    if rol not in ['admin']:
        return jsonify({"mensaje": "El rol debe ser admin"}), 400
    
    if not str(id).isdigit():
       return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    PASS_FICTICIA = '__sin_cambios__'
    password = request.json.get('password')
    password_hash = None

    if password == PASS_FICTICIA:
         password = None
         password_hash = None
    else:
        if not password:
            return jsonify({"mensaje": "La contraseña es requerida"}), 400
        patron_password = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]{8,128}$'
        if not re.match(patron_password, password):
            return jsonify({"mensaje": "La contraseña debe tener mayúscula, minúscula, número y carácter especial"}), 400
        if len(password) < 8 or len(password) > 50:
            return jsonify({"mensaje": "La contraseña debe tener entre 8 y 50 caracteres"}), 400
        password_hash = hashear_password(password)

    if existe_username_otro(username, id):
        return jsonify({"mensaje": "El username ya existe"}), 400
    
    usuario_actual = obtener_usuario(id)
    if not usuario_actual:
     return jsonify({"mensaje": "Usuario no encontrado"}), 404

    cambios = []

    if nombre is not None and nombre != usuario_actual["nombre"]:
     cambios.append("nombre")

    if username is not None and username != usuario_actual["username"]:
     cambios.append("username")

    if rol is not None and rol != usuario_actual["rol"]:
     cambios.append("rol")

    if password:
     cambios.append("password")

    if not cambios:
     return jsonify({"mensaje": "No hay cambios para actualizar"}), 400

    actualizado = actualizar(
        id=id,
        nombre=nombre,
        username=username,
        password_hash=password_hash,
        rol=rol
    )

    if not actualizado:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200

def obtenerUsuario(id):
    if not id:
        return jsonify({"mensaje": "El id es requerido"}), 400
    
    if not str(id).isdigit():
       return jsonify({"mensaje": "El id debe ser un número entero"}), 400

    usuario = obtener_usuario(id)

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify(usuario), 200


def login_post():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')  # Contraseña en texto plano

    if not username or not password:
        return jsonify({"error": "Faltan credenciales"}), 400

    usuario = login(username, password)
    if not usuario:
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = generar_token(usuario)
    return jsonify({
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario      # opcional, para que el front sepa el rol/nombre
    }), 200


def cntPrimerAdmin():
    """
    Registra al primer administrador del sistema.
    Solo funciona si no existe ningún admin en la BD.
    No requiere token JWT.
    """
    # 1. Verificar que no exista ya un admin
    if existe_admin():
        return jsonify({
            "mensaje": "Ya existe un administrador registrado. Use el login normal."
        }), 403
    
    # 2. Validar campos requeridos
    requeridos = ['nombre', 'username', 'password', 'rol']
    faltantes = [d for d in requeridos if d not in request.json]
    if faltantes:
        return jsonify({"mensaje": f"Faltan los siguientes campos: {faltantes}"}), 400
    
    # 3. Validar campos vacíos
    vacios = []
    for clave in requeridos:
        if str(request.json.get(clave, '')).strip() == '':
            vacios.append(clave)
    if vacios:
        return jsonify({"mensaje": f"Los siguientes campos no pueden estar vacíos: {vacios}"}), 400
    
    # 4. Obtener datos
    nombre = request.json['nombre'].strip()
    username = request.json['username'].strip()
    password = request.json['password']
    rol = request.json['rol']
    
    # 5. Validar que el rol sea admin (no permitir crear cajero en setup)
    if rol != 'admin':
        return jsonify({"mensaje": "El primer usuario debe ser administrador"}), 400
    
    # 6. Validar formato de nombre
    if len(nombre) < 3 or len(nombre) > 100:
        return jsonify({"mensaje": "El nombre debe tener entre 3 y 100 caracteres"}), 400
    
    if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$', nombre):
        return jsonify({"mensaje": "El nombre solo puede contener letras"}), 400
    
    # 7. Validar username

    if username.isdigit(): 
        return jsonify({"mensaje": "El username no puede contener solo números"}), 400
    
    if len(username) < 4 or len(username) > 50:
        return jsonify({"mensaje": "El username debe tener entre 4 y 50 caracteres"}), 400
    
    if existe_username(username):
        return jsonify({"mensaje": "El username ya existe"}), 400
    
   # 8. Validar contraseña
    if len(password) < 8 or len(password) > 50:
        return jsonify({"mensaje": "La contraseña debe tener entre 8 y 50 caracteres"}), 400

    patron_password = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]{8,50}$'
    if not re.match(patron_password, password):
       return jsonify({"mensaje": "La contraseña debe tener mayúscula, minúscula, número y carácter especial"}), 400
    
    # 9. Hashear contraseña
    password_hash = hashear_password(password)
    
    # 10. Registrar usuario
    try:
        usuario = registro(
            nombre=nombre,
            username=username,
            password_hash=password_hash,
            rol=rol
        )
        return jsonify({
            "mensaje": "Administrador inicial creado exitosamente",
            "datos": usuario
        }), 201
    except Exception as e:
        return jsonify({
            "mensaje": f"Error al crear administrador: {str(e)}"
        }), 500
    
def cntVerificarClaveMaestra():
    data = request.get_json()
    clave    = data.get('clave', '').strip()
    username = data.get('username', '').strip()

    if not clave or not username:
        return jsonify({"mensaje": "Faltan campos requeridos"}), 400

    if not existe_username(username):
        return jsonify({"mensaje": "El usuario no existe"}), 404

    if not verificar_clave_maestra(clave):
        return jsonify({"mensaje": "Clave maestra incorrecta"}), 401

    return jsonify({"valida": True}), 200


def cntCambiarPasswordMaestra():
    data = request.get_json()
    username         = data.get('username', '').strip()
    nueva_password   = data.get('nueva_password', '')

    if not username or not nueva_password:
        return jsonify({"mensaje": "Faltan campos requeridos"}), 400
    
    if len(nueva_password) < 8 or len(nueva_password) > 50:
        return jsonify({"mensaje": "La contraseña debe tener entre 8 y 50 caracteres"}), 400

    patron = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&._-])[A-Za-z\d@$!%*?&._-]{8,50}$'
    if not re.match(patron, nueva_password):
        return jsonify({"mensaje": "La contraseña debe tener mayúscula, minúscula, número y carácter especial"}), 400

    resultado = cambiar_password_maestra(username, nueva_password)
    if not resultado:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify({"mensaje": "Contraseña actualizada correctamente"}), 200