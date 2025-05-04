# src/__init__.py

import os
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail




# ——— Instantiate extensions here ———
load_dotenv()
db   = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # make getattr available in Jinja2 templates
    app.jinja_env.globals['getattr'] = getattr

    # ——— App configuration ———
    app.config['SECRET_KEY']                = os.getenv('SESSION_KEY')
    app.config['SQLALCHEMY_DATABASE_URI']   = os.getenv('URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Flask-Mail setup
    app.config['MAIL_SERVER']       = 'smtp.gmail.com'
    app.config['MAIL_PORT']         = 587
    app.config['MAIL_USE_TLS']      = True
    app.config['MAIL_USERNAME']     = os.getenv('EMAIL')
    app.config['MAIL_PASSWORD']     = os.getenv('PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL')
    
    from .controller import register_blueprints
    register_blueprints(app)

    # ——— Initialize extensions ———
    db.init_app(app)
    mail.init_app(app)

    return app
