import os
from dotenv import load_dotenv
from flask import Flask
from models import db
from routes import main


def create_app():
    app = Flask(__name__)
    load_dotenv()

    # CONNECT TO DB
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    app.register_blueprint(main)

    return app
