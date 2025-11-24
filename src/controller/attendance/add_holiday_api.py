# src/controller/get_fee.py

from flask import request, Blueprint

from src.controller.permissions import permission_required

from src.controller.permissions.permission_required import permission_required
from src.controller.auth.login_required import login_required
from src.model.AttendanceHolidays import AttendanceHolidays
from src import db


add_holiday_api_bp = Blueprint( 'add_holiday_api_bp',   __name__)


@add_holiday_api_bp.route('/api/add_holiday', methods=["POST"])
@login_required
@permission_required('add_holiday')
def add_holiday():
    holiday_name = request.form.get('holiday_name')
    start_date   = request.form.get('start_date')
    end_date     = request.form.get('end_date')
    apply_to     = request.form.get('apply_to')   # "all" or class.id

    if not holiday_name or not start_date or not end_date:
        return {"error": "Missing required fields"}, 400

    if apply_to == "all" or apply_to is None:
        class_id = None   # or logic for “all”
    else:
        class_id = int(apply_to)

    # Save to database
    # holiday = AttendanceHolidays(name=holiday_name, start=start_date, end=end_date, class_id=class_id)
    # db.session.add(holiday)
    # db.session.commit()

    return {"success": True, "message": "Holiday added successfully"}
