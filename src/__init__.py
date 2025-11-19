# src/__init__.py
import os
from dotenv import load_dotenv
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import redis

# ——— Instantiate extensions ———
load_dotenv()
db = SQLAlchemy()
r = None  # Redis instance (for other uses)
sess = Session()  # Flask-Session instance


def create_app():
    global r
    app = Flask(__name__, template_folder='view/templates', static_folder='view/static')

    # ——— Make getattr available in Jinja2 templates ———
    app.jinja_env.globals['getattr'] = getattr

    # ——— App configuration ———
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config['SECRET_KEY'] = os.getenv('SESSION_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('URI')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ——— SESSION CONFIGURATION (SERVER SIDE) ———
    app.config['SESSION_TYPE'] = 'filesystem'  # store sessions on disk
    app.config['SESSION_FILE_DIR'] = os.path.join(app.root_path, 'flask_session')  # path to store session files
    app.config['SESSION_FILE_THRESHOLD'] = 500  # max number of session files before cleanup
    app.config['SESSION_PERMANENT'] = True      # keep session until it expires
    app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 7  # 7 days
    app.config['SESSION_USE_SIGNER'] = True     # adds cryptographic signature for security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True  # set False for localhost, True for HTTPS
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True

    # Initialize Flask-Session
    sess.init_app(app)

    # ——— Initialize SQLAlchemy ———
    db.init_app(app)

    # ——— Setup Redis Cloud connection ———
    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        username=os.getenv('REDIS_USERNAME', 'default'),
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True
    )

    try:
        # r.ping()
        print("✅ Connected to Redis Cloud successfully.")
    except redis.exceptions.ConnectionError as e:
        print("❌ Redis connection failed:", e)

    # ——— Register blueprints ———
    from .controller import register_blueprints
    register_blueprints(app)

    return app
