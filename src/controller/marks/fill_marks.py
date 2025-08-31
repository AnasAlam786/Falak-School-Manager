# src/controller/marks/fill_marks.py

from flask import render_template, session, url_for, redirect, request, jsonify, Blueprint


from src.model import Exams, StudentsDB, StudentSessions, ClassData, StudentsMarks, StudentsMarks_duplicate, Subjects, TeachersLogin
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

    class_ids = [row.id for row in classes]

        
    subjects = (
        db.session.query(Subjects.subject, Subjects.display_order)
        .filter(
            Subjects.school_id == school_id,
            Subjects.is_active == True,
            Subjects.class_id.in_(class_ids)
        )
        .order_by(Subjects.display_order.asc())
        .all()
    )

    unique_subjects = []

    for subject in subjects:
        if subject.subject not in unique_subjects:
            unique_subjects.append(subject.subject)


    exams =  db.session.query(Exams.exam_name, Exams.id).filter_by(school_id=school_id).order_by(Exams.display_order.asc()).all()
    
    data = None

    if request.method == "POST":
        payload = request.json

        subject_name =  payload.get('subject')
        class_id = payload.get('class')
        exam_id = payload.get('exam')
        current_session_id = session["session_id"]


        marks_data = (
            db.session.query(
                StudentsMarks_duplicate.id.label('id'),
                StudentsMarks_duplicate.score,          # Student's mark (can be None)
                StudentsDB.STUDENTS_NAME,               # Name of the student
                StudentsDB.GENDER,
                StudentsDB.id.label('student_id'), 
                StudentSessions.ROLL,                   # Roll number
                ClassData.CLASS,                        # Class name or number
                Exams.id.label('exam_id'),
                Exams.exam_name,                        # e.g., "Mid Term"
                Exams.weightage,                        # Max marks for the exam
                Subjects.subject,                       # e.g., "Math", "English"
                Subjects.evaluation_type,                # e.g., "numeric" or "grading"
                Subjects.id.label('subject_id')
            )

            # Join student with their session info
            .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)

            # Join session info with class info
            .join(ClassData, StudentSessions.class_id == ClassData.id)

            # Join exam details — fixed value (one exam at a time) it create the colum with same values in all the table like FA1
            .join(Exams, Exams.id == exam_id)

            # Join subject details — fixed value (one subject at a time) it create the colum with same values in all the table like English
            .join(Subjects, (Subjects.subject == subject_name) & (Subjects.class_id == class_id))

            # Outer join: get marks only if they exist
            .outerjoin(
                StudentsMarks_duplicate,
                (StudentsMarks_duplicate.student_id == StudentsDB.id) &
                (StudentsMarks_duplicate.exam_id == exam_id) &
                (StudentsMarks_duplicate.subject_id == Subjects.id)
            )

            # Filter by class, school, and session
            .filter(
                ClassData.id == class_id,
                StudentsDB.school_id == school_id,
                StudentSessions.session_id == current_session_id
            )

            # Sort by roll number
            .order_by(StudentSessions.ROLL)

            .all()
        )


        html = render_template('fill_marks.html', data=marks_data, EXAM=None, classes=None)
        soup=BeautifulSoup(html,"lxml")
        content=soup.body.find('div',{'id':'marksTable'}).decode_contents()

        return jsonify({"html":str(content)})
        
    return render_template('fill_marks.html', data=data, classes=classes, exams = exams, subjects = unique_subjects)
