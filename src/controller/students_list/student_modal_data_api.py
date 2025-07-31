# src/controller/students/student_modal_data_api.py

from flask import render_template, session, request, Blueprint, jsonify

from sqlalchemy import func, case

from src.model import StudentsDB
from src.model import ClassData
from src.model import StudentSessions

from src import db

student_modal_data_api_bp = Blueprint( 'student_modal_data_api_bp',   __name__)



@student_modal_data_api_bp.route('/student_modal_data_api', methods=["POST"])
def student_modal_data_api():
    data = request.json
    
    student_id = int(data.get('student_id'))
    phone = data.get('phone')  #replace by familyID


    student = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, StudentsDB.AADHAAR,
            StudentsDB.FATHERS_NAME, StudentsDB.MOTHERS_NAME, StudentsDB.PHONE,
            StudentsDB.ADMISSION_NO, StudentsDB.ADDRESS, StudentsDB.ADMISSION_DATE, StudentsDB.SR, StudentsDB.IMAGE,
            StudentsDB.GENDER, StudentsDB.PEN,
            func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY').label('DOB'),
            ClassData.CLASS,  # Get the class name from the ClassData table
            StudentSessions.ROLL
        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
        ).filter(
            StudentsDB.PHONE == phone,
            StudentSessions.session_id == session["session_id"],
        ).order_by(
        case(
            (StudentsDB.id == student_id, 0),  # Place the matched student_id at the top
            else_=1
        )
    ).all()

    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    content = render_template('student_modal.html', student=student)
    return jsonify({"html":str(content)})