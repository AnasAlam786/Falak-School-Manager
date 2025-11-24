# src/controller/get_fee.py

from datetime import date, datetime
from sqlalchemy import and_, or_
from flask import session, request, jsonify, Blueprint

from src.controller.permissions import permission_required
from src.model import StudentsDB, StudentSessions, ClassData
from src import db

from src.model.Attendance import Attendance
from src.model.AttendanceHolidays import AttendanceHolidays

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required

get_attendance_data_api_bp = Blueprint( 'get_attendance_data_api_bp',   __name__)

@get_attendance_data_api_bp.route('/api/get_attendance_data', methods=["GET"])
@login_required
@permission_required('attendance')
def get_attendance_data_api():

    class_id = request.args.get("classID")
    date_str = request.args.get("date")

    current_session = session["session_id"]
    school_id = session["school_id"]


    def parse_date(date_str):
        possible_formats = [
            "%Y-%m-%d",  # HTML input format
            "%d/%m/%Y",  # Indian format 1
            "%d-%m-%Y",  # Indian format 2
        ]

        for fmt in possible_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                continue

        return None

    date = parse_date(date_str)
    if date is None:
        return jsonify({"message": "Invalid date format. Use DD/MM/YYYY or DD-MM-YYYY"}), 400
    

    holiday = AttendanceHolidays.query.filter(
        AttendanceHolidays.school_id == school_id,
        AttendanceHolidays.date == date,
        or_(
            AttendanceHolidays.class_id == class_id,
            AttendanceHolidays.class_id.is_(None)
        )
    ).first()


    if holiday:
        return jsonify({"message": "Holiday"}), 200
        
    
    # Build query
    attendance_data = (
        db.session.query(
            StudentsDB.STUDENTS_NAME,
            StudentsDB.FATHERS_NAME,
            StudentsDB.IMAGE,
            StudentsDB.PHONE,
            ClassData.CLASS,
            StudentSessions.ROLL,
            StudentSessions.id.label("student_session_id"),
            Attendance.status.label("attendance_status"),
            Attendance.remark
        )
        .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
        .join(ClassData, ClassData.id == StudentSessions.class_id)
        .outerjoin(
            Attendance,
            and_(
                Attendance.student_session_id == StudentSessions.id,
                Attendance.date == date
            )
        )
        .filter(
            StudentSessions.class_id == class_id,
            StudentSessions.session_id == current_session
        )
        .order_by(StudentSessions.ROLL.asc())
    ).all()

    attendance_data = [dict(row._mapping) for row in attendance_data]
    
    return jsonify({"message": "success", "attendance_data": attendance_data, "date": date.strftime("%d-%m-%Y")}), 200