# src/controller/tc.py

from flask import render_template, session, url_for, redirect, Blueprint

from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin
from src import db

tc_bp = Blueprint( 'tc_bp',   __name__)

@tc_bp.route('/tc', methods=['GET'])
def tc():
    
    if "email" not in session:
        return redirect(url_for('login_bp.login'))
    
    user_id = session["user_id"]

    classes = (
        db.session.query(ClassData.id, ClassData.CLASS)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .join(TeachersLogin, TeachersLogin.id == ClassAccess.staff_id)
        .filter(TeachersLogin.id == user_id)
        .order_by(ClassData.id.asc())
        .all()
    )

    return render_template('tc.html', classes=classes)
