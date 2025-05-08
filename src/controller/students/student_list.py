# src/controller/student_list.py

from flask import render_template, session, url_for, redirect, Blueprint
from sqlalchemy import func

from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin

from src import db

student_list_bp = Blueprint( 'student_list_bp',   __name__)

@student_list_bp.route('/student_list', methods=['GET', 'POST'])
def student_list():

    if 'email' not in session:
        return redirect(url_for('login_bp.login'))

    school_id = session['school_id']
    current_session = session['session_id']
    user_id = session["user_id"]

    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()
    class_ids = [cls.id for cls in classes]


    # build your query
    data = db.session.query(
        StudentsDB.id,
        StudentsDB.STUDENTS_NAME,
        func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY').label('dob'),
        StudentsDB.AADHAAR,
        StudentsDB.FATHERS_NAME,
        StudentsDB.PEN,
        StudentsDB.IMAGE,
        StudentsDB.PHONE,
        StudentsDB.Free_Scheme,
        StudentSessions.ROLL,
        ClassData.CLASS,
        ClassData.Section,
    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData,    StudentSessions.class_id == ClassData.id
    ).filter(
        StudentsDB.school_id    == school_id,
        StudentSessions.session_id == current_session,
        ClassData.id.in_(class_ids)
    ).order_by(
        ClassData.id.asc(),
        ClassData.Section.asc(),
        StudentSessions.ROLL.asc()
    ).all()

    return render_template('student_list.html',
                           data=data,
                           classes=classes)