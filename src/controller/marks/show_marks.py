# src/controller/show_marks.py

from flask import render_template, session, url_for, redirect, Blueprint

show_marks_bp = Blueprint('show_marks_bp',   __name__)

@show_marks_bp.route('/marks', methods=["GET"])
def report_card():
    if "email" not in session:
        return redirect(url_for('login_bp.login')) 
    
    Data = None

    return render_template('show_marks.html', Data=Data)
    
