# src/controller/generate_tc_form_api.py

from flask import render_template, session, request, Blueprint, jsonify
from sqlalchemy import func

from src.model import StudentsDB
from src.model import ClassData
from src.model import StudentsMarks
from src.model import StudentSessions
from src import db

from datetime import datetime

generate_tc_form_api_bp = Blueprint( 'generate_tc_form_api_bp',   __name__)

@generate_tc_form_api_bp.route('/generate_tc_form_api', methods=['POST'])
def generate_tc_form_api():

    if "email" not in session:
        return jsonify({"message": "You are not authorised to access this API. Login required!"})

    data = request.json

    student_id = data.get('student_id')
    leaving_reason = data.get('leaving_reason')
    classes = session["classes"]
    current_session_id = session["session_id"]


    student_marks = db.session.query(
        StudentsMarks.Subject,
        StudentsMarks.FA1,
        StudentsMarks.SA1,
        StudentsMarks.FA2,
        StudentsMarks.SA2
    ).filter(
        StudentsMarks.student_id == student_id
    ).all()

    results = []
    grading_subjects = []

    for subject, fa1, sa1, fa2, sa2 in student_marks:
        if subject == "Craft":
            continue

        total = 0
        is_grading = False

        for mark in [fa1, sa1, fa2, sa2]:
            try:
                total += int(mark)
            except:
                total = mark  # save grade value (e.g., 'A')
                is_grading = True
                break

        entry = {'subject': subject, 'total': total}

        if is_grading:
            grading_subjects.append(entry)
        else:
            results.append(entry)

    results.extend(grading_subjects)

    student = db.session.query(
        StudentsDB.STUDENTS_NAME, StudentsDB.AADHAAR,StudentsDB.SR,
        StudentsDB.FATHERS_NAME, StudentsDB.MOTHERS_NAME, StudentsDB.PHONE,
        StudentsDB.ADMISSION_NO, StudentsDB.ADDRESS, StudentsDB.HEIGHT,
        StudentsDB.WEIGHT, StudentsDB.Caste_Type, StudentsDB.RELIGION,
        StudentsDB.ADMISSION_DATE, StudentsDB.SR, StudentsDB.IMAGE,
        StudentsDB.GENDER, StudentsDB.PEN, StudentsDB.HEIGHT,StudentsDB.WEIGHT,
        StudentsDB.APAAR, StudentsDB.Attendance,
        func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY').label('DOB'),

        ClassData.CLASS,
        ClassData.id.label("class_id"),
        StudentSessions.ROLL

    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
    ).join(
        ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
    ).filter(
        StudentsDB.id == student_id,
        StudentSessions.session_id == current_session_id
    ).first()

    class_id = student.class_id

    if class_id + 1 > len(classes):
        promoted_class = "9th"
    else:
        # Get the next class name based on the class_id
        promoted_class = db.session.query(ClassData.CLASS).filter_by(id=class_id + 1).scalar()

    working_days = 214
    general_conduct = "Very Good"
    school_logo = '1WGhnlEn8v3Xl1KGaPs2iyyaIWQzKBL3w'
    current_date = datetime.now().strftime("%d-%m-%Y")

    html = render_template('pdf-components/tcform.html', 
                            working_days = working_days, student=student, results=results,
                            general_conduct = general_conduct, school_logo = school_logo,
                            current_date = current_date, leaving_reason=leaving_reason,
                            promoted_class = promoted_class)
    
    return jsonify({"html":str(html)})


