# src/controller/promote_student.py

from flask import render_template, session, url_for, redirect, Blueprint
from src.model import ClassData

from src import db

promote_student_bp = Blueprint( 'promote_student_bp',   __name__)


@promote_student_bp.route('/promote_student', methods=["GET", "POST"])
def promoteStudent():
    if not "email" in session:
        return redirect(url_for('login_bp.login'))

    school_id = session["school_id"]
    classes = db.session.query(
        ClassData.id, ClassData.CLASS
    ).filter_by(
        school_id=school_id
    ).order_by(
        ClassData.id
    ).all()
    return render_template('promote_student.html', classes=classes)# src/controller/student_list.py

