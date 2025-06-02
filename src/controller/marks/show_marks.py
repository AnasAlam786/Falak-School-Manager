# src/controller/show_marks.py

from flask import render_template, session, url_for, redirect, Blueprint

from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin
from src import db

from ..auth.login_required import login_required


show_marks_bp = Blueprint('show_marks_bp',   __name__)

@show_marks_bp.route('/marks', methods=["GET"])
@login_required
def show_marks():
    

    user_id = session["user_id"]


    classes = (
        db.session.query(ClassData.id, ClassData.CLASS)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .join(TeachersLogin, TeachersLogin.id == ClassAccess.staff_id)
        .filter(TeachersLogin.id == user_id)
        .order_by(ClassData.id.asc())
        .all()
    )

    return render_template('show_marks.html', Data=None, classes = classes)
    
