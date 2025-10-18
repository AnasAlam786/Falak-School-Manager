from flask import Blueprint, render_template, session
from src import r
import time  # <-- to measure execution time



home_bp = Blueprint( 'home_bp', __name__)

@home_bp.route('/')
def home_page():
    user_logged_in = 'user_id' in session  # or however you track logged-in users
    return render_template("home.html", user_logged_in=user_logged_in)