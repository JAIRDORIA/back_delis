from flask import Flask
from flask_mysqldb import MySQL
from routes import cargarRuta
from config import config
from flask_jwt_extended import JWTManager
import os
from flask_cors import CORS
from routes.usuarios import auth_bp
from flasgger import Swagger # 1. Importar Flasgger

app = Flask(__name__)
app.config.from_object(config)
app.register_blueprint(auth_bp)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

# 2. Configurar Swagger para que use tu archivo swagger.json
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

# Inicializar Swagger apuntando al archivo swagger.json que tienes en la raíz
swagger = Swagger(app, config=swagger_config, template_file='swagger.json') 

CORS(app)
jwt = JWTManager(app)

mysql = MySQL(app)
app.mysql = mysql
cargarRuta(app)

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Authorization"]
)

if __name__ == '__main__':
    app.run(debug=True, port=4000, host='0.0.0.0')