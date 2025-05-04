# src/controller/verify_admission_api.py

from flask import session, request, jsonify, Blueprint
from sqlalchemy import or_

from src.model import StudentsDB
from src.model import StudentSessions

from datetime import datetime

from .utils.validate_name import validate_name
from .utils.validate_length import validate_length
from .utils.validate_aadhaar import is_valid_aadhaar

verify_admission_api_bp = Blueprint( 'verify_admission_api_bp',   __name__)


@verify_admission_api_bp.route('/verify_admission', methods=["POST"])
def verify_admission():
    data = request.get_json() or {}

    school_id = session.get('school_id')
    current_session_id = session.get('session_id')

    # Normalize Aadhaar and similar fields safely
    def handle_aadhar(key):
        return data.get(key, '').replace('-', '').replace(' ', '') or None

    admission_no = data.get('ADMISSION_NO')
    SR = data.get('SR')
    PEN = data.get('PEN')
    APAAR = data.get('APAAR')
    aadhaar = handle_aadhar('AADHAAR')
    faadhar = handle_aadhar('FATHERS_AADHAR')
    maadhar = handle_aadhar('MOTHERS_AADHAR')

    # Mandatory text fields
    mandatory_names = [
        "STUDENTS_NAME", "FATHERS_NAME", "MOTHERS_NAME",
        "Caste_Type", "RELIGION", "ADDRESS", "GENDER",
        "FATHERS_OCCUPATION", "MOTHERS_OCCUPATION",
        "FATHERS_EDUCATION", "MOTHERS_EDUCATION",
        "Home_Distance", "Section"
    ]
    for name in mandatory_names:
        val = data.get(name)
        err = validate_name(val, name.replace('_', ' ').title())
        if err:
            return jsonify({'message': err}), 400

    # Optional text fields
    non_mandatory = ["Blood_Group", "Previous_School", "Email", "Free_Scheme", "Caste"]
    for name in non_mandatory:
        val = data.get(name)
        if not val:
            data[name] = None
        else:
            err = validate_name(val, name.replace('_', ' ').title())
            if err:
                return jsonify({'message': err}), 400

    # Length validations (only ValueError expected)
    try:
        validate_length(aadhaar, "AADHAAR", exact=12)
        validate_length(admission_no, "ADMISSION_NO", exact=5)
        validate_length(data.get("PIN"), "PIN", exact=6)
        validate_length(data.get("PHONE"), "Phone", exact=10)
        validate_length(SR, "SR", min_len=1)
        validate_length(data.get("CLASS"), "CLASS", min_len=1, max_len=2)
        validate_length(data.get("ROLL"), "ROLL", min_len=1)
        validate_length(data.get("Height"), "Height", min_len=2, max_len=3, allow_empty=True)
        validate_length(data.get("Weight"), "Weight", min_len=2, max_len=3, allow_empty=True)
        validate_length(APAAR or "", "APAAR", exact=12, allow_empty=True)
        validate_length(PEN or "", "PEN", exact=11, allow_empty=True)
        validate_length(data.get("ALT_MOBILE") or "", "ALT_MOBILE", exact=10, allow_empty=True)
        validate_length(faadhar, "Fathers Aadhar", exact=12, allow_empty=True)
        validate_length(maadhar, "Mothers Aadhar", exact=12, allow_empty=True)
    except Exception as e:
        return jsonify({'message': str(e)}), 400

    # Date-field parsing
    for key in ["DOB", "ADMISSION_DATE"]:
        raw = data.get(key)
        if not raw:
            return jsonify({'message': f"Missing required field: {key}"}), 400
        normalized = raw.replace('/', '-')
        parsed_date = None
        for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
            try:
                parsed_date = datetime.datetime.strptime(normalized, fmt).date()
                break
            except ValueError:
                continue
        if not parsed_date:
            return jsonify({'message': f"Invalid date format for {key}. Expected DD-MM-YYYY or YYYY-MM-DD."}), 400


    aadhaar_inputs = {
        'Student Aadhaar': aadhaar,
        'Father Aadhaar': faadhar,
        'Mother Aadhaar': maadhar
    }
    for label, number in aadhaar_inputs.items():
        if not is_valid_aadhaar(number):
            return jsonify({'message': f'{label} ({number}) is not valid'}), 400




    # Check global conflicts for unique IDs
    global_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(
            StudentsDB.PEN == PEN,
            StudentsDB.APAAR == APAAR,
            StudentsDB.AADHAAR == aadhaar
        )
    ).first()
    if global_conflict:
        return jsonify({'message': 'PEN, APAAR, or AADHAAR is already in use.'}), 400

    # Check within this school
    school_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(
            StudentsDB.SR == SR,
            StudentsDB.ADMISSION_NO == admission_no
        )
    ).first()
    if school_conflict:
        return jsonify({'message': 'SR or Admission No. already exists for this school.'}), 400

    # Ensure class_id, Section, ROLL exist in request
    class_id = data.get('CLASS')
    section = data.get('Section')
    roll = data.get('ROLL')
    if not class_id or not section or not roll:
        return jsonify({'message': 'Missing Class, Section, or ROLL for session check.'}), 400

    # Check current-session conflict
    session_conflict = (
        StudentSessions.query
        .join(StudentsDB, StudentSessions.student_id == StudentsDB.id)
        .filter(
            StudentsDB.school_id == school_id,
            StudentSessions.session_id == current_session_id,
            StudentSessions.class_id == class_id,
            StudentSessions.Section == section,
            StudentSessions.ROLL == roll
        )
        .first()
    )
    if session_conflict:
        return jsonify({'message': 'This class/section/roll is already assigned in the current session.'}), 400

    # If we reach here, all validations passed
    return jsonify({'message': 'Admission details are valid.'}), 200

