# src/__init__.py

import os
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


# ——— Instantiate extensions here ———
load_dotenv()

db = SQLAlchemy()


def create_app():
    app = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # make getattr available in Jinja2 templates
    app.jinja_env.globals['getattr'] = getattr

    # ——— App configuration ———
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config['SECRET_KEY'] = os.getenv('SESSION_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ——— Initialize extensions ———
    db.init_app(app)

    # ——— Register blueprints ———
    from .controller import register_blueprints
    register_blueprints(app)

    return app
