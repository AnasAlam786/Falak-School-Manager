# src/controller/get_new_roll_api.py

from flask import session, request, jsonify, Blueprint
from sqlalchemy import select, func

from src.model import StudentsDB
from src.model import StudentSessions
from src import db

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

get_new_roll_api_bp = Blueprint( 'get_new_roll_api_bp',   __name__)


@get_new_roll_api_bp.route('/get_new_roll_api', methods=["POST"])
@login_required
@permission_required('admission')
def get_new_roll_api():
    data = request.json
    class_id = data.get('class_id')
    school_id = session["school_id"]
    current_session = session["session_id"]

    # Build subquery to calculate the next available roll number in the next class
    next_roll_query = (
        select(func.coalesce(func.max(StudentSessions.ROLL), 0) + 1)
        .join(StudentsDB, StudentsDB.id == StudentSessions.student_id)
        .where(
            StudentSessions.class_id   == class_id,
            StudentSessions.session_id == current_session,
            StudentsDB.school_id       == school_id
        )
    )
    # next_roll now holds the next available roll (1 if none exist)
    try:
        next_roll: int = db.session.execute(next_roll_query).scalar_one()
    except Exception as e:
        return jsonify({"message": e}), 404


    return jsonify({ "next_roll": next_roll })

