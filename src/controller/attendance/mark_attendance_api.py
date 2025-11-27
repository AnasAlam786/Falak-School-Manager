# src/controller/get_fee.py

from datetime import datetime
from time import time
from flask import session, request, jsonify, Blueprint
from sqlalchemy import and_

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required

from src.model import StudentSessions, Attendance
from src import db

mark_attendance_api_bp = Blueprint( 'mark_attendance_api_bp',   __name__)

@mark_attendance_api_bp.route('/api/mark_attendance', methods=["POST"])
@login_required
@permission_required('attendance')
def mark_attendance_api():
    start_time = time()  # start timer
    # --- Read Inputs ---
    data = request.json
    student_session_id = data.get("student_session_id")
    status = data.get("status")
    date_str = data.get("date")
    remark = data.get("remark") or None

    current_session = session["session_id"]
    user_id = session["user_id"]

    # --- Input Validation ---
    if not student_session_id or not date_str:
        return jsonify({"message": "studentSessionID and date are required"}), 400

    # Allowed attendance statuses
    allowed_status = {"PRESENT", "ABSENT", "HALF_DAY", "LEAVE", "HOLIDAY", None}
    if status not in allowed_status:
        return jsonify({"message": "Invalid attendance status"}), 400

    # --- Date Parsing ---
    def parse_date(date_str):
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                pass
        return None

    date = parse_date(date_str)
    if date is None:
        return jsonify({"message": "Invalid date format"}), 400

    # --- Validate student session ---
    # student_session = (
    #     db.session.query(StudentSessions.id)
    #     .filter(
    #         and_(
    #             StudentSessions.id == student_session_id,
    #             StudentSessions.session_id == current_session,
    #         )
    #     ).first()
    # )
    # if not student_session:
    #     return jsonify({"message": "Invalid student session"}), 404

    # --- Check Existing Attendance ---
    attendance = Attendance.query.filter_by(
        student_session_id=student_session_id,
        date=date
    ).first()

    if not status:
        if attendance:
            db.session.delete(attendance)
            try:
                db.session.commit()
                end_time = time()  # end timer
                print(f"Attendance took {end_time - start_time:.6f} to mark")
                return jsonify({"message": "success"}), 200
            except Exception as e:
                db.session.rollback()
                print("Attendance Deletion Error:", e)
                return jsonify({"message": "Database error"}), 500

    # --- Insert or Update Attendance ---
    if attendance:
        attendance.status = status
        attendance.remark = remark
        attendance.marked_by = user_id 
    else:
        attendance = Attendance(
            student_session_id=student_session_id,
            date=date,
            status=status,
            marked_by=user_id,
            remark=remark
        )
        db.session.add(attendance)

    # --- Commit Safely ---
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Attendance Error:", e)
        return jsonify({"message": "Database error"}), 500
    
    end_time = time()  # end timer
    print(f"Attendance took {end_time - start_time:.6f} to mark")

    return jsonify({"message": "success"}), 200