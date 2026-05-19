from flask import Flask
from flask_mysqldb import MySQL
from routes import cargarRuta
from config import config
from flask_jwt_extended import JWTManager
import os
from flask_cors import CORS
from routes.usuarios import auth_bp

app = Flask(__name__)
app.config.from_object(config)
app.register_blueprint(auth_bp)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

# 2. Configurar Swagger para que use tu archivo swagger.json

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
