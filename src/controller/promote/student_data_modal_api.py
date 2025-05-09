# src/controller/student_data_modal_api.py

from flask import session,  request, jsonify, Blueprint

from sqlalchemy import func, select, literal

from src import db
from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

import datetime

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required


student_data_modal_api_bp = Blueprint('student_data_modal_api_bp',   __name__)



@student_data_modal_api_bp.route('/student_data_modal_api', methods=["POST"])
@login_required
@permission_required('promote_student')
def student_data_modal_api():
    """
    Fetch a single student's data including promotion details based on
    the previous session data.
    
    Expected JSON payload:
    {
        "studentID": <student_id>,
    }
    """
    data = request.get_json()

    # Validate input: ensure required keys exist
    if not data or "student_id" not in data:
        return jsonify({"message": "Missing required parameters."}), 400
    
    try:
        student_id = int(data.get('student_id'))
    except Exception as e:
        print("Invalid parameter format:", data)
        return jsonify({"message": "Invalid parameter format."}), 400

    # Validate session values exist and are valid integers
    try:
        school_id = session["school_id"]
        current_session_id = int(session["session_id"])
        previous_session = current_session_id - 1
    except (KeyError, ValueError):
        return jsonify({"message": "Session data is missing or corrupted. Please logout and login again!"}), 500


    current_class_id = (
        db.session.query(StudentSessions.class_id)
        .filter(StudentSessions.student_id == student_id,
                StudentSessions.session_id == previous_session)
        .scalar()
    )

    # Calculate the next class id (assumes sequential class ids)
    next_class_id = current_class_id + 1

    # Build subquery to get the next class name
    next_class_subquery = (
        select(ClassData.CLASS)
        .where(ClassData.id == next_class_id)
        .scalar_subquery()
    )

    # Build subquery to calculate the next available roll number in the next class
    next_roll_subquery = (
        select(func.coalesce(func.max(StudentSessions.ROLL), 999) + 1)
        .select_from(StudentsDB)
        .join(StudentSessions)
        .where(
            StudentSessions.class_id == next_class_id,
            StudentsDB.school_id == school_id,
            StudentSessions.session_id == int(current_session_id)
        )
        .scalar_subquery()
    )

    try:
        # Main query to retrieve student's data for the previous session
        student_query = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, 
            StudentsDB.IMAGE, StudentsDB.FATHERS_NAME, StudentsDB.PHONE,
            ClassData.CLASS,
            StudentSessions.ROLL,
            next_class_subquery.label("promoted_class"),
            next_roll_subquery.label("promoted_roll"),

            literal(datetime.date.today().strftime('%Y-%m-%d')).label("promoted_date")
        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id
        ).filter(
            StudentsDB.id == student_id,
            StudentSessions.session_id == previous_session
        )
        
        student_row = student_query.first()
        print("Student Row:", student_row)
    except Exception as error:
        # Log error here if you have a logger configured
        print("Error fetching student data:", error)
        return jsonify({"message": "An error occurred while fetching student data."}), 500

    if student_row is None:
        return jsonify({"message": "Student not found"}), 404

    # Convert SQLAlchemy row object to dictionary and return JSON response
    return jsonify(student_row._asdict()), 200
