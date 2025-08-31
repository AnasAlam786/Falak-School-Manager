from flask import session, request, jsonify, Blueprint
from sqlalchemy import or_

from src.model import StudentsDB, StudentSessions
from src import db

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required


update_conflict_verification_api_bp = Blueprint('update_conflict_verification_api_bp', __name__)


@update_conflict_verification_api_bp.route('/api/update_conflict_verification', methods=["POST"])
@login_required
@permission_required('update_student')
def verify_update_conflicts():
    """
    Expects a JSON array of {field, value} from the verified Pydantic output
    and also expects 'student_id' to exclude the current student from checks.
    Checks:
      - Global unique: AADHAAR, PEN, APAAR (across school, excluding self)
      - School unique: SR, ADMISSION_NO (within school, excluding self)
      - Session unique: class/section/roll within current session (StudentSessions), excluding self
    """

    body = request.get_json() or {}
    verified_items = body.get('verifiedData', [])
    student_id = body.get('student_id')

    if not student_id:
        return jsonify({'message': 'Missing student id'}), 400

    school_id = session.get('school_id')
    current_session_id = session.get('session_id')

    # Map values for quick lookup
    values = {item['field']: str(item['value']).strip() for item in verified_items}

    # ----------------------------
    # 1. Global-Session Unique Check: AADHAAR, PEN, APAAR
    # ----------------------------
    session_unique_fields = ['AADHAAR', 'PEN', 'APAAR']
    session_filters = []
    for field in session_unique_fields:
        val = values.get(field)
        if val:
            session_filters.append(getattr(StudentsDB, field) == val)


    if session_filters:
        existing = (
            db.session.query(StudentsDB)
            .join(StudentSessions, StudentsDB.id == StudentSessions.student_id)
            .filter(
                StudentsDB.school_id == school_id,
                StudentSessions.session_id == current_session_id,
                StudentsDB.id != student_id,
                or_(*session_filters)
            )
            .first()
        )
        if existing:
            print(existing)
            conflicting_fields = []
            for field in session_unique_fields:
                val = values.get(field)
                if val and getattr(existing, field) == val:
                    conflicting_fields.append(field)

            return jsonify({
                'message': f"Conflict in session for field(s): {', '.join(conflicting_fields)} with student '{existing.STUDENTS_NAME}'"
            }), 409


    # Global unique (excluding self)
    for field in ['AADHAAR', 'PEN', 'APAAR']:
        val = values.get(field)
        if val:
            existing = (
                db.session.query(StudentsDB.STUDENTS_NAME)
                .join(StudentSessions, StudentsDB.id == StudentSessions.student_id)
                .filter(
                    StudentsDB.school_id == school_id,
                    StudentSessions.session_id == current_session_id,
                    getattr(StudentsDB, field) == val,
                    StudentsDB.id != student_id,
                )
                .first()
            )
            if existing:
                detailed_message = (
                    f"Another student '{existing.STUDENTS_NAME}' already exists in this school in this session"
                    f"with the same {field}. "
                )
                return jsonify({'message': detailed_message}), 409



    # ----------------------------
    # 2. School-wide Unique Check: SR, ADMISSION_NO
    # ----------------------------
    school_unique_fields = ['SR', 'ADMISSION_NO']
    school_filters = []
    for field in school_unique_fields:
        val = values.get(field)
        print(val)
        if not val or val == "":
            return jsonify({'message': f'{field} is required'}), 400
        school_filters.append(getattr(StudentsDB, field) == val)

    if school_filters:
        existing = (
            db.session.query(StudentsDB)
            .filter(
                StudentsDB.school_id == school_id,
                StudentsDB.id != student_id,
                or_(*school_filters)
            )
            .first()
        )
        if existing:
            print(student_id)
            print(existing)
            conflicting_fields = []
            for field in school_unique_fields:
                val = values.get(field)
                if val and getattr(existing, field) == val:
                    conflicting_fields.append(field)

            return jsonify({
                'message': f"Conflict in school for field(s): {', '.join(conflicting_fields)} with student '{existing.STUDENTS_NAME}' \nAdmission number: {existing.ADMISSION_NO}, SR: {existing.SR}"
            }), 409

    # ----------------------------
    # 3. Session-Scoped Roll No Check: CLASS, Section, ROLL
    # ----------------------------
    class_id = values.get('CLASS')
    section = values.get('Section')
    roll = values.get('ROLL')

    if not all([class_id, section, roll]):
        return jsonify({'message': 'CLASS, Section, and ROLL are required'}), 400

    existing_roll = (
        db.session.query(StudentsDB)
        .join(StudentSessions, StudentsDB.id == StudentSessions.student_id)
        .filter(
            StudentsDB.school_id == school_id,
            StudentSessions.session_id == current_session_id,
            StudentSessions.class_id == class_id,
            StudentSessions.Section == section,
            StudentSessions.ROLL == roll,
            StudentsDB.id != student_id,
        )
        .first()
    )

    if existing_roll:
        return jsonify({
            'message': f"Another student '{existing_roll.STUDENTS_NAME}' already has the same CLASS, Section, and ROLL in this session.\nAdmission number: {existing_roll.ADMISSION_NO}\nSR: {existing_roll.SR}"
        }), 409

    return jsonify({'message': 'No conflicts found'}), 200

