# src/controller/tc.py

from flask import render_template, session, url_for, redirect, Blueprint

from src.model import ClassData
from src import db

tc_bp = Blueprint( 'tc_bp',   __name__)

@tc_bp.route('/tc', methods=['GET'])
def tc():
    
    if "email" not in session:
        return redirect(url_for('login_bp.login'))
    
    school_id = session["school_id"]

    classes = db.session.query(ClassData.id, ClassData.CLASS)\
        .filter_by(school_id=school_id
        ).order_by(ClassData.id).all()

    return render_template('tc.html', classes=classes)
