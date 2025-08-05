# src/controller/verify_admission_api.py

from flask import session, request, jsonify, Blueprint
from sqlalchemy import or_
from pydantic import ValidationError

from src.model import ClassData, StudentsDB, StudentSessions

from src.controller.students.utils.admission_form_schema import (PersonalInfoModel, AcademicInfoModel, 
                                           GuardianInfoModel, ContactInfoModel, 
                                           AdditionalInfoModel)

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

from collections import defaultdict


verify_admission_api_bp = Blueprint( 'verify_admission_api_bp',   __name__)


@verify_admission_api_bp.route('/verify_admission_api', methods=["POST"])
@login_required
@permission_required('admission')
def verify_admission():

    data = request.get_json()
    grouped_data = defaultdict(dict)


    groups = ["PersonalInfo", "AcademicInfo", "GuardianInfo", "ContactInfo", "AdditionalInfo"]

    for field_name, field_value in data.items():
        if '-' in field_name:
            section, field = field_name.split('-', 1)
            if section in groups:
                grouped_data[section][field] = field_value


    
    verified_data = []

    try:
        personal_data = PersonalInfoModel(**grouped_data['PersonalInfo'])
        verified_data.extend(personal_data.verified_model_dump())
    except ValidationError as e:
        print(e.errors())
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
    
    try:
        academic_data = AcademicInfoModel(**grouped_data['AcademicInfo'])
        verified_data.extend(academic_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
   
    try:
        guardian_data = GuardianInfoModel(**grouped_data['GuardianInfo'])
        verified_data.extend(guardian_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
    
    try:
        contact_data = ContactInfoModel(**grouped_data['ContactInfo'])
        verified_data.extend(contact_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
    
    try:
        additional_data = AdditionalInfoModel(**grouped_data['AdditionalInfo'])
        verified_data.extend(additional_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
    
    

    school_id = session.get('school_id')
    current_session_id = session.get('session_id')

    # Check global conflicts for unique IDs

    for item in verified_data:
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

        if item["field"] == "ADMISSION_DATE":
            admission_date = item["value"]
            print("Admission Date:", admission_date)
            print(type(admission_date))



    global_conflict_conditions = []
    school_conflict_conditions = []

    if pen:
        global_conflict_conditions.append(StudentsDB.PEN == pen)
    if apaar:
        global_conflict_conditions.append(StudentsDB.APAAR == apaar)
    if aadhaar:
        global_conflict_conditions.append(StudentsDB.AADHAAR == aadhaar)
    
    if sr:
        school_conflict_conditions.append(StudentsDB.SR == sr)
    if admission_no:
        school_conflict_conditions.append(StudentsDB.ADMISSION_NO == admission_no)



    global_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(*global_conflict_conditions)
    ).first()

    if global_conflict:
        return jsonify({'message': 'Either PEN, APAAR, or AADHAAR is already in use.'}), 400
    

    school_conflict = StudentsDB.query.filter(
        StudentsDB.school_id == school_id,
        or_(*school_conflict_conditions)
    ).first()

    if school_conflict:
        return jsonify({'message': 'SR or Admission no already exists.'}), 400

    # Ensure class_id, Section, ROLL exist in request
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

    # If class_id is provided, fetch class name
    class_name = ClassData.query.filter_by(id=class_id).first()
    return jsonify({'message': 'Admission details are valid.', "verifiedData" : verified_data, "className": class_name.CLASS}), 200

