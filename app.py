# app.py
from flask import Flask
from flask_mysqldb import MySQL
from routes import cargarRuta
from config import config

app = Flask(__name__)
app.config.from_object(config)

mysql = MySQL(app)
app.mysql = mysql
cargarRuta(app)
app.run(debug=True, port=4000, host='0.0.0.0')  