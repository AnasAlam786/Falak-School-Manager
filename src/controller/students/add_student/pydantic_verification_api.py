# src/controller/verify_admission_api.py

from flask import session, request, jsonify, Blueprint
from sqlalchemy import or_
from pydantic import ValidationError

from src.controller.students.utils.admission_form_schema import (PersonalInfoModel, AcademicInfoModel, 
                                           GuardianInfoModel, ContactInfoModel, 
                                           AdditionalInfoModel)

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

from collections import defaultdict


pydantic_verification_api_bp = Blueprint( 'pydantic_verification_bp',   __name__)


@pydantic_verification_api_bp.route('/api/pydantic_verification', methods=["POST"])
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
        print(e.errors())
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
   
    try:
        guardian_data = GuardianInfoModel(**grouped_data['GuardianInfo'])
        verified_data.extend(guardian_data.verified_model_dump())
    except ValidationError as e:
        print(e.errors())
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
    
    try:
        contact_data = ContactInfoModel(**grouped_data['ContactInfo'])
        verified_data.extend(contact_data.verified_model_dump())
    except ValidationError as e:
        print(e.errors())
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
    
    try:
        additional_data = AdditionalInfoModel(**grouped_data['AdditionalInfo'])
        verified_data.extend(additional_data.verified_model_dump())
    except ValidationError as e:
        print(e.errors())
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field" : error_field}), 400
    
    
    return jsonify({'message': 'Admission details are valid.', "verifiedData" : verified_data}), 200

