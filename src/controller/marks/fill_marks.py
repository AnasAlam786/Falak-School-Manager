# src/controller/marks/fill_marks.py

from flask import render_template, session, url_for, redirect, request, jsonify, Blueprint


from src.model import StudentsDB, StudentSessions, ClassData, StudentsMarks, TeachersLogin
from src.model.ClassAccess import ClassAccess
from src import db

from bs4 import BeautifulSoup
from ..auth.login_required import login_required

fill_marks_bp = Blueprint( 'fill_marks_bp',   __name__)


@fill_marks_bp.route('/fill_marks', methods=["GET", "POST"])
@login_required
def fill_marks():
    
    user_id = session["user_id"]
    school_id = session["school_id"]

    classes = (
        db.session.query(ClassData.id, ClassData.CLASS)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .join(TeachersLogin, TeachersLogin.id == ClassAccess.staff_id)
        .filter(TeachersLogin.id == user_id)
        .order_by(ClassData.id.asc())
        .all()
    )
    
    data = None

    if request.method == "POST":
        payload = request.json

        SUBJECT =  payload.get('subject')
        class_id = payload.get('class')
        EXAM = payload.get('exam')
        current_session_id = session["session_id"]


        data = db.session.query(
                            StudentsMarks.id, StudentsDB.STUDENTS_NAME, 
                            ClassData.CLASS, StudentSessions.ROLL, 
                            getattr(StudentsMarks, EXAM), StudentsMarks.Subject
                        ).join(
                            StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                        ).join(
                            ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                        ).join(
                            StudentsMarks, StudentsMarks.student_id == StudentsDB.id
                        ).filter(
                            StudentsMarks.Subject == SUBJECT,
                            ClassData.id == class_id,
                            StudentsDB.school_id == school_id,
                            StudentSessions.session_id == current_session_id
                        ).order_by(
                            StudentSessions.ROLL
                        ).all()


        html = render_template('fill_marks.html', data=data, EXAM=EXAM, classes=classes)
        soup=BeautifulSoup(html,"lxml")
        content=soup.body.find('div',{'id':'marksTable'}).decode_contents()

        return jsonify({"html":str(content)})
        
    return render_template('fill_marks.html', data=data, classes=classes)
