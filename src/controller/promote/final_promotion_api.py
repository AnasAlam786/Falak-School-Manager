# src/controller/final_promotion_api.py

from flask import session,  request, jsonify, Blueprint
from sqlalchemy import func

from src import db
from src.model import StudentSessions
from src.model import ClassData

import datetime

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

final_promotion_api_bp = Blueprint('final_promotion_api_bp',   __name__)

@final_promotion_api_bp.route('/final_promotion_api', methods=["POST"])
@login_required
@permission_required('promote_student')
def final_promotion_api():

    

    #get the number of classes in the school


    try:
        school_id = session.get("school_id")
        current_session = int(session["session_id"])
    except (KeyError, ValueError):
        return jsonify({"message": "Session data is missing or corrupted. Please logout and login again!"}), 500
        

    class_len = db.session.query(func.count(ClassData.id)).filter(ClassData.school_id == school_id).scalar()
    
    if class_len is None:
        return jsonify({"message": "Class data not found for the school."}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON payload"}), 400

    required_fields = ["student_id", "promoted_roll", "promoted_date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required parameter: {field}"}), 400

        
    try:
        student_id = int(data.get('student_id'))
        promoted_roll = int(data.get('promoted_roll'))
    except (TypeError, ValueError):
        return jsonify({"message": "Student or the promoted roll no is not valid!"}), 404
    

    
    promoted_date = data.get('promoted_date')
    if promoted_date:
        try:
            promoted_date = datetime.datetime.strptime(promoted_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid promotion date format. Use 'year-month-day'."}), 400
    else:
        return jsonify({"message": "Please enter promotion date."}), 400



    due_amount_input = data.get('due_amount')
    due_amount = None
    if due_amount_input:
        try:
            due_amount = float(due_amount_input)  # Using float to handle decimal values
        except ValueError:
            return jsonify({"message": "Invalid due amount."}), 400
        

        
    #check if the student exist in previous session.
    student = StudentSessions.query.filter_by(student_id = student_id,
                                              session_id = current_session-1).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    
    class_to_promote = student.class_id + 1

    if class_to_promote > class_len:
        return jsonify({"message": "Student cannot be promoted; maximum class reached."}), 400



    # If an entry exists, reject the request immediately
    already_promoted  = StudentSessions.query.filter_by(
        student_id=student_id,
        session_id=current_session
    ).first()
    if already_promoted:
        return jsonify({"message": "Student already has an entry in this session, promotion not allowed!"}), 400



    # Check for existing roll number in the target class and session
    existing_roll = StudentSessions.query.filter_by(
        session_id=current_session,
        class_id=class_to_promote,
        ROLL=promoted_roll
    ).first()

    if existing_roll:
        return jsonify({"message": "This roll number is already in use in the target class and session."}), 400


    new_session = StudentSessions(
        student_id=student_id,
        session_id=current_session,
        ROLL=promoted_roll,
        class_id=class_to_promote,
        Due_Amount=due_amount,
        created_at=promoted_date
    )
    
    try:
        db.session.add(new_session)
        db.session.commit()
    except Exception as error:
        db.session.rollback()
        return jsonify({"message": "Failed to promote student due to a database error."}), 500

    return jsonify({"message" : "Student Promoted successfully"}), 200

