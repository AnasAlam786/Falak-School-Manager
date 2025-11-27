# src/controller/get_fee.py

from datetime import date, datetime
from sqlalchemy import and_, or_
from flask import session, request, jsonify, Blueprint

from src.controller.permissions.has_permission import has_permission
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
    current_date = datetime.today().date()


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
    
    if current_date != date:
        if not has_permission("mark_any_day_attendance"):
            return jsonify({"message": "Access denied. You are only authorized to record attendance for today only."}), 403


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

    total_students = len(attendance_data)
    present = absent = half_day = not_marked = 0

    for attendance in attendance_data:
        if attendance.attendance_status == "PRESENT":
            present +=1 
        elif attendance.attendance_status == "ABSENT":
            absent +=1 
        elif attendance.attendance_status == "HALF_DAY":
            half_day +=1 
        else:
            not_marked += 1

    attendance_data = [dict(row._mapping) for row in attendance_data]

    # Pack everything neatly into one variable
    attendance_summary = {
        "date": date.strftime("%A, %d %B %Y"),
        "total": total_students,
        "present": present,
        "absent": absent,
        "half_day": half_day,
        "not_marked": not_marked
    }
    
    return jsonify({"attendance_data": attendance_data, "attendance_summary": attendance_summary}), 200
