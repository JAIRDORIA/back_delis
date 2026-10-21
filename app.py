from flask import Flask
from flask_mysqldb import MySQL
from routes import cargarRuta
from config import config
from flask_jwt_extended import JWTManager
import os
from flask_cors import CORS
from routes.usuarios import auth_bp
from utils.db import PoolMySQL, init_pool

app = Flask(__name__)
app.config.from_object(config)

app.register_blueprint(auth_bp)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS","PATCH"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Authorization"]
)

jwt = JWTManager(app)


mysql = MySQL(app)
if os.getenv("DB_POOL_ENABLED", "1") != "0":
    # Pool de conexiones por proceso (ver utils/db.py). DB_POOL_ENABLED=0
    # devuelve el comportamiento original de Flask-MySQLdb.
    app.mysql = PoolMySQL(mysql)
    init_pool(app)
else:
    app.mysql = mysql
cargarRuta(app)


if __name__ == '__main__':
    app.run(debug=True, port=4000, host='0.0.0.0')
