# src/controller/promoted_student_modal_api.py

from flask import request, jsonify, Blueprint

from sqlalchemy import func
from sqlalchemy.orm import aliased

from src import db
from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required


promoted_student_modal_api_bp = Blueprint('promoted_student_modal_api_bp',   __name__)


@promoted_student_modal_api_bp.route('/promoted_student_modal_api', methods=["POST"])
@login_required
@permission_required('promote_student')
def promoted_student_modal_api():
    """
    Fetch a single student's data including promotion details based on
    the previous session data.
    
    Expected JSON payload:
    {
        "promoted_session_id": <id of record in StudentSessions table>
    }
    """

    data = request.get_json()

    # Validate input: ensure required keys exist
    if not data or "studentSessionID" not in data:
        return jsonify({"message": "Missing required parameters."}), 400
    
    try:
        promoted_session_id = int(data.get('studentSessionID'))
    except Exception as e:
        print("Invalid parameter format:", data)
        return jsonify({"message": "Invalid parameter format."}), 400
    
    try:
        #session_data = db.session.query(StudentSessions.student_id).filter_by(id=promoted_session_id).scalar()

        # Create aliases for self-join
        PromotedSession = aliased(StudentSessions)
        PreviousSession = aliased(StudentSessions)
        PreviousClass = aliased(ClassData)

        student_row = db.session.query(
            StudentsDB.id, StudentsDB.STUDENTS_NAME, StudentsDB.IMAGE, 
            StudentsDB.FATHERS_NAME, StudentsDB.PHONE,

            # Promoted (current) session
            ClassData.CLASS.label("promoted_class"),
            PromotedSession.ROLL.label("promoted_roll"),
            PromotedSession.Due_Amount.label("due_amount"),
            PromotedSession.id.label("promoted_session_id"),
            func.to_char(PromotedSession.created_at, 'YYYY-MM-DD').label("promoted_date"),

            # Previous session
            PreviousClass.CLASS.label("CLASS"),
            PreviousSession.ROLL.label("ROLL"),

        ).join(
            PromotedSession, PromotedSession.student_id == StudentsDB.id
        ).join(
            ClassData, PromotedSession.class_id == ClassData.id
        ).join(
            PreviousSession, PreviousSession.student_id == StudentsDB.id
        ).join(
            PreviousClass, PreviousSession.class_id == PreviousClass.id
        ).filter(
            PromotedSession.id == promoted_session_id,
            PreviousSession.id != promoted_session_id  # exclude the current session
        ).limit(1).first()  # get the most recent previous session only
        
    except Exception as error:
        # Log error here if you have a logger configured
        print("Error fetching student data:", error)
        return jsonify({"message": "An error occurred while fetching student data."}), 500

    if student_row is None:
        return jsonify({"message": "Student not found"}), 404

    return jsonify(student_row._asdict()), 200