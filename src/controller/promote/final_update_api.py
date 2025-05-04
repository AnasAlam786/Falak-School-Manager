# src/controller/final_update_api.py

from flask import session,  request, jsonify, Blueprint

from src import db
from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

import datetime


final_update_api_bp = Blueprint('final_update_api_bp',   __name__)


@final_update_api_bp.route('/final_update_api', methods=["POST"])
def final_update_api():

    current_session = session.get("session_id")

    data = request.json

    student_session_ID = data.get('student_session_ID')
    promoted_roll = data.get('promoted_roll')
    promoted_date = data.get('promoted_date')

    due_amount_input = data.get('due_amount')
    due_amount = None
    if due_amount_input:
        try:
            due_amount = int(due_amount_input)  # Using float to handle decimal values
        except ValueError:
            return jsonify({"message": "Invalid due amount."}), 400


    if not student_session_ID or not promoted_roll or not promoted_date:
        return jsonify({"message": "Missing required parameters."}), 400

    student_session = StudentSessions.query.filter_by(id = student_session_ID).first()
    if not student_session:
        return jsonify({"message": "Student not promoted, Try promoting again!"}), 404

    # Check for existing roll number in the target class and session
    conflict = db.session.query(
        StudentsDB.STUDENTS_NAME,
        ClassData.CLASS
        ).join(
            StudentSessions, StudentSessions.student_id == StudentsDB.id
        ).join(
            ClassData, StudentSessions.class_id == ClassData.id
        ).filter(
            StudentSessions.session_id == current_session,
            StudentSessions.class_id == student_session.class_id,
            StudentSessions.ROLL == promoted_roll,
            StudentSessions.id != student_session.id
        ).first()

    if conflict:
        print(f"This roll number is already in use: {conflict}")
        return jsonify({
            "message": f"This roll number is already in use in the target class and session, by {conflict.STUDENTS_NAME} in class {conflict.CLASS}"
        }), 400


    try:
        student_session_ID = int(student_session_ID)
        promoted_roll = int(promoted_roll)
        promoted_date = datetime.datetime.strptime(promoted_date, "%Y-%m-%d").date()

    except (ValueError, TypeError):
        return jsonify({"message": "Invalid parameter format."}), 400

    # Update the StudentSessions table with the new roll number and date
    try:
        if student_session:
            student_session.ROLL = promoted_roll
            student_session.created_at = promoted_date
            student_session.Due_Amount = due_amount  # Optional field
            db.session.commit()
            return jsonify({"message": "Student record updated successfully."}), 200
        else:
            return jsonify({"message": "Student session not found."}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error updating student record."}), 500

