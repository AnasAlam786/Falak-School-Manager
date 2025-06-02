# src/controller/fees/watsapp_message_api.py

from flask import session,  request, jsonify, Blueprint

from sqlalchemy.orm import aliased
from sqlalchemy import func

from src import db
from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required



watsapp_message_api_bp = Blueprint('watsapp_message_api_bp',   __name__)




@watsapp_message_api_bp.route('/api/watsapp_message', methods=["POST"])
@login_required
@permission_required('promote_student')
def watsapp_message():
    data = request.json
    student_id = data.get('student_id')

    session_id = session["session_id"]


    if not student_id:
        return jsonify({"message": "Missing student ID"}), 400
    

    student_data = db.session.query(StudentsDB
            ).join(StudentSessions, StudentSessions.student_id == StudentsDB.id
            ).join(ClassData, ClassData.id == StudentSessions.class_id
            ).join().filter(StudentsDB.id == student_id,
                     StudentSessions.session_id == session_id).first()

    if not student_data:
        return jsonify({"message": "Student not found"}), 404

    # Generate WhatsApp message
    message = f"{student_data.name}, this is a reminder about your upcoming class."

    return jsonify({"message": "WhatsApp message sent successfully"}), 200