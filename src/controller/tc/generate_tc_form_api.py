# src/controller/generate_tc_form_api.py

from flask import render_template, session, request, Blueprint, jsonify
from sqlalchemy import func

from src.model import StudentsDB
from src.model import ClassData
from src.model import StudentsMarks
from src.model import StudentSessions
from src.model import ClassAccess
from src import db

from datetime import datetime

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

generate_tc_form_api_bp = Blueprint( 'generate_tc_form_api_bp',   __name__)

@generate_tc_form_api_bp.route('/generate_tc_form_api', methods=['POST'])
@login_required
@permission_required('tc')
def generate_tc_form_api():

    data = request.get_json() or {}
    student_id = data.get('student_id')
    leaving_reason = data.get('leaving_reason', '')
    current_session_id = session.get('session_id')
    user_id = session.get('user_id')

    # Fetch allowed classes once, as id:name mapping
    classes = (
        db.session.query(ClassData.id, ClassData.CLASS)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id)
        .all()
    )
    classes_map = {cid: name for cid, name in classes}

    # Bulk load student details and marks in two queries
    student_data = (
        db.session.query(

            StudentsDB.STUDENTS_NAME, StudentsDB.AADHAAR,StudentsDB.SR,
            StudentsDB.FATHERS_NAME, StudentsDB.MOTHERS_NAME, StudentsDB.PHONE,
            StudentsDB.ADMISSION_NO, StudentsDB.ADDRESS, StudentsDB.Caste_Type, StudentsDB.RELIGION,
            StudentsDB.ADMISSION_DATE, StudentsDB.SR, StudentsDB.IMAGE,
            StudentsDB.GENDER, StudentsDB.PEN,
            StudentsDB.APAAR, 
            func.to_char(StudentsDB.DOB, 'Dy, DD Mon YYYY').label('DOB'),

            StudentSessions.Attendance,
            StudentSessions.class_id,
            StudentSessions.Height,
            StudentSessions.Weight,
            ClassData.CLASS.label('current_class')
        )
        .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
        .join(ClassData, ClassData.id == StudentSessions.class_id)
        .filter(
            StudentsDB.id == student_id,
            StudentSessions.session_id == current_session_id
        )
        .first()
    )


    if not student_data:
        return jsonify({"message": "Student not found."}), 404
    

    # Single query for all marks, skipping "Craft"
    marks = (
        db.session.query(
            StudentsMarks.Subject,
            StudentsMarks.FA1,
            StudentsMarks.SA1,
            StudentsMarks.FA2,
            StudentsMarks.SA2
        )
        .filter(
            StudentsMarks.student_id == student_id,
            StudentsMarks.Subject != 'Craft'
        )
        .all()
    )

    # Process totals and grades
    results = []
    grades = []
    for subj, fa1, sa1, fa2, sa2 in marks:
        scores = [fa1, sa1, fa2, sa2]
        # if any non-numeric, treat as grade
        if any(not str(s).isdigit() for s in scores if s is not None):
            grades.append({ 'subject': subj, 'total': next(s for s in scores if not str(s).isdigit()) })
        else:
            total = sum(int(s or 0) for s in scores)
            results.append({ 'subject': subj, 'total': total })
    results.extend(grades)

    # Determine promoted class
    current_class_id = student_data.class_id
    next_id = current_class_id + 1
    promoted_class = classes_map.get(next_id) or \
                     '9th'

    # Fixed metadata (could be moved to config)
    working_days = 214
    general_conduct = "Very Good"
    school_logo = '1WGhnlEn8v3Xl1KGaPs2iyyaIWQzKBL3w'
    current_date = datetime.now().strftime("%d-%m-%Y")

    # Render HTML directly
    html = render_template(
        'pdf-components/tcform.html',
        student=student_data,
        results=results,
        working_days=working_days,
        general_conduct=general_conduct,
        school_logo=school_logo,
        current_date=current_date,
        leaving_reason=leaving_reason,
        promoted_class=promoted_class
    )

    return jsonify({ 'html': html })
