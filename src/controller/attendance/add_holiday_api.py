from flask import request, Blueprint, session, current_app
from datetime import datetime, timedelta

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required
from src.model.AttendanceHolidays import AttendanceHolidays
from src import db


add_holiday_api_bp = Blueprint('add_holiday_api_bp', __name__)


@add_holiday_api_bp.route('/api/add-holiday', methods=["POST"])
@login_required
@permission_required('mark_holiday')
def add_holiday():
    """Add holiday(s) to AttendanceHolidays. Supports date range (inclusive).

    Expects form fields: holiday_name, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), apply_to (empty for all or class id)
    """
    holiday_name = request.form.get('holiday_name')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    apply_to = request.form.get('apply_to')  # empty for entire school or class.id

    if not holiday_name or not start_date or not end_date:
        return {"error": "Missing required fields"}, 400

    # Determine class_id
    if apply_to == "" or apply_to is None:
        class_id = None
    else:
        try:
            class_id = int(apply_to)
        except Exception:
            return {"error": "Invalid class id"}, 400

    # Determine school_id: prefer session value, fall back to form (if provided)
    school_id = session.get('school_id') or request.form.get('school_id')
    if not school_id:
        return {"error": "Missing school context (school_id)"}, 400

    # Parse dates
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}, 400

    if e_date < s_date:
        return {"error": "End date must be same or after start date."}, 400

    # Create holiday rows for each date in range, avoid duplicates
    added = 0
    cur = s_date
    while cur <= e_date:
        exists = db.session.query(AttendanceHolidays).filter(
            AttendanceHolidays.school_id == str(school_id),
            AttendanceHolidays.date == cur,
            (AttendanceHolidays.class_id == class_id if class_id is not None else AttendanceHolidays.class_id.is_(None))
        ).first()

        if not exists:
            holiday = AttendanceHolidays(
                school_id=str(school_id),
                date=cur,
                name=holiday_name,
                class_id=class_id,
                created_at=datetime.utcnow()
            )
            db.session.add(holiday)
            added += 1

        cur = cur + timedelta(days=1)

    try:
        if added > 0:
            
            db.session.commit()
        else:
            # nothing new added, still return success but note 0
            db.session.rollback()
    except Exception as e:
        current_app.logger.exception('Failed to add holiday(s)')
        db.session.rollback()
        return {"error": "Database error while saving holiday."}, 500

    return {"success": True, "message": f"Added {added} holiday(s).", "added": added}
