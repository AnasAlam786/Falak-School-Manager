# src/controller/final_depromotion_api.py

from flask import session,  request, jsonify, Blueprint

from src import db
from src.model import StudentSessions

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required


final_depromotion_api_bp = Blueprint('final_depromotion_api_bp',   __name__)


@final_depromotion_api_bp.route('/final_depromotion_api', methods=["POST"])
@login_required
@permission_required('promote_student')
def depromote_student():
    data = request.json

    if not 'email' in session:
        return jsonify({"message": "Unauthorized access."}), 400

    if not data or "student_session_id" not in data:
        return jsonify({"message": "Missing required parameters."}), 400

    try:
        student_session_ID = int(data.get('student_session_id'))
    except Exception as e:
        print("Invalid parameter format:", data)
        return jsonify({"message": "Invalid parameter format."}), 400

    # Check if the student exists in the current session
    student_sesssion = db.session.query(StudentSessions).filter_by(id=student_session_ID).first()
    if not student_sesssion:
        return jsonify({"message": "Student not promoted, cant depromote!"}), 404

    #depromote the student by deleting the record from StudentSessions table
    db.session.delete(student_sesssion)
    db.session.commit()

    return jsonify({"message": "Student successfully depromoted"}), 200