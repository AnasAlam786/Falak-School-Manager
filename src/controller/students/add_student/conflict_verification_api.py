# src\controller\students\add_student\conflict_verification_api.py

from flask import session, request, jsonify, Blueprint
from sqlalchemy import or_

from src.model import ClassData, StudentsDB, StudentSessions

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required



conflict_verification_api_bp = Blueprint( 'conflict_verification_api_bp',   __name__)


@conflict_verification_api_bp.route('/api/conflict_verification', methods=["POST"])
@login_required
@permission_required('admission')
def verify_admission():

    data = request.get_json()

    school_id = session.get('school_id')
    current_session_id = session.get('session_id')

    # Check global conflicts for unique IDs
    for item in data:
        if item["field"] == "PEN":
            pen = item["value"]

        if item["field"] == "APAAR":
            apaar = item["value"]

        if item["field"] == "AADHAAR":
            aadhaar = item["value"]

        if item["field"] == "SR":
            sr = item["value"]

        if item["field"] == "ADMISSION_NO":
            admission_no = item["value"]

        if item["field"] == "CLASS":
            class_id = item["value"]

        if item["field"] == "Section":
            section = item["value"]

        if item["field"] == "ROLL":
            roll = item["value"]

    # print(f"Received data for conflict verification: {data}")

    global_conflict_conditions = []
    school_conflict_conditions = []

    if pen:
        global_conflict_conditions.append(StudentsDB.PEN == pen)
    if apaar:
        global_conflict_conditions.append(StudentsDB.APAAR == apaar)
    # if aadhaar:    Not working because of encryption
    #     global_conflict_conditions.append(StudentsDB.AADHAAR == aadhaar)
    
    if sr:
        school_conflict_conditions.append(StudentsDB.SR == sr)
    else:  return jsonify({'message': 'Please enter SR properly!'}), 400
    if admission_no:
        school_conflict_conditions.append(StudentsDB.ADMISSION_NO == admission_no)
    else: return jsonify({'message': 'Please enter Admission Number properly!'}), 400

    

    if len(global_conflict_conditions)>0:        
        global_conflict = (
            StudentsDB.query
            .join(StudentSessions, StudentsDB.id == StudentSessions.student_id)
            .filter(
                StudentsDB.school_id == school_id,
                StudentSessions.session_id == current_session_id,
                # StudentsDB.is_active == True,
                or_(*global_conflict_conditions)
            )
            .first()
        )

        
        if global_conflict:
            
            conflict_fields = []

            if pen and global_conflict.PEN == pen:
                conflict_fields.append('PEN')
            if apaar and global_conflict.APAAR == apaar:
                conflict_fields.append('APAAR')
            # if aadhaar and global_conflict.AADHAAR == aadhaar:
            #     conflict_fields.append('AADHAAR')

            detailed_message = (
                    f"Student '{global_conflict.STUDENTS_NAME}' (admission number: {global_conflict.ADMISSION_NO}), (SR: {global_conflict.SR}) already exists in this school"
                    f"with the same {', '.join(conflict_fields)}. "
                )

            return jsonify({
                'message': detailed_message,
                'conflicting_fields': conflict_fields,
                'conflicting_student': global_conflict.STUDENTS_NAME
            }), 400
        

    school_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(*school_conflict_conditions)
    ).first()

    if school_conflict:
        conflict_fields = []
        if sr and school_conflict.SR == sr:
            conflict_fields.append('SR')
        if admission_no and school_conflict.ADMISSION_NO == admission_no:
            conflict_fields.append('Admission number')

        if conflict_fields:
            conflict_list = ', '.join(conflict_fields)
            return jsonify({
                'message': (
                    f"The following field(s) already exist for student "
                    f"'{school_conflict.STUDENTS_NAME}': {conflict_list}. "
                    "Please provide unique values."
                ),
                'conflicting_fields': conflict_fields,
                'conflicting_student': school_conflict.STUDENTS_NAME
            }), 400

    # Ensure class_id, Section, ROLL exist in request
    if not class_id or not section or not roll:
        return jsonify({'message': 'Missing Class, Section, or ROLL for session check.'}), 400

    # Check current-session conflict
    session_conflict = (
        StudentSessions.query
        .join(StudentsDB, StudentSessions.student_id == StudentsDB.id)
        .filter(
            StudentsDB.school_id == school_id,
            # StudentsDB.is_active == True,
            StudentSessions.session_id == current_session_id,
            StudentSessions.class_id == class_id,
            StudentSessions.Section == section,
            StudentSessions.ROLL == roll
        )
        .first()
    )
    if session_conflict:
        return jsonify({'message': f'This class/section/roll is already assigned to {session_conflict.student_name}, admission number: {session_conflict.admission_no} in the current session.'}), 400

    # If class_id is provided, fetch class name
    return jsonify({'message': 'Admission details are valid.'}), 200

