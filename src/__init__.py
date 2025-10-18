# src/__init__.py
import os
from dotenv import load_dotenv

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis

# ——— Instantiate extensions here ———
load_dotenv()

db = SQLAlchemy()
r = None  # we’ll initialize Redis later inside create_app()


def create_app():
    global r
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

    # ——— Setup Redis Cloud connection ———
    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        username=os.getenv('REDIS_USERNAME', 'default'),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True
    )

        # Test connection (optional)
    try:
        r.ping()
        print("✅ Connected to Redis Cloud successfully.")
    except redis.exceptions.ConnectionError as e:
        print("❌ Redis connection failed:", e)

    # ——— Register blueprints ———
    from .controller import register_blueprints
    register_blueprints(app)

    return app
