# src/controller/promote_student.py

from flask import render_template, session, url_for, redirect, Blueprint

from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin
from src import db

promote_student_bp = Blueprint( 'promote_student_bp',   __name__)


@promote_student_bp.route('/promote_student', methods=["GET", "POST"])
def promoteStudent():
    if not "email" in session:
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
    return render_template('promote_student.html', classes=classes)# src/controller/student_list.py

