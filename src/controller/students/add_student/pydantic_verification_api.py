# src/controller/verify_admission_api.py

from flask import session, request, jsonify, Blueprint
from pydantic import ValidationError

from src.controller.students.utils.admission_form_schema import (PersonalInfoModel, AcademicInfoModel, 
                                           GuardianInfoModel, ContactInfoModel, 
                                           AdditionalInfoModel)
from src.model.ClassData import ClassData
from src import db

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
    errors = []

    models = {
        "PersonalInfo": PersonalInfoModel,
        "AcademicInfo": AcademicInfoModel,
        "GuardianInfo": GuardianInfoModel,
        "ContactInfo": ContactInfoModel,
        "AdditionalInfo": AdditionalInfoModel,
    }

    for section, model in models.items():
        try:
            instance = model(**grouped_data[section])
            verified_data.extend(instance.verified_model_dump())
        except ValidationError as e:
            errors.extend([
                {
                    "field": err["loc"][0],
                    "message": err["msg"]
                } for err in e.errors()
            ])

    if errors:
        return jsonify({"message": "Validation failed", "errors": errors}), 400
    
    if data.get('student_status') == "new":
        if data.get("Admission_Class") != data.get("CLASS"):
            return jsonify({"message": "For new students, Admission Class must be same as Current Class."}), 400

    if data.get('student_status') == "old":

        adm_id = data.get("Admission_Class")
        cur_id = data.get("CLASS")
        if adm_id is None or cur_id is None:
            return jsonify({"message": "Admission_Class and CLASS are required for existing students."}), 400

        try:
            adm_id_int = int(adm_id)
            cur_id_int = int(cur_id)
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid class identifiers provided."}), 400

        # Now fetch only the display_order scalar values
        adm_order = db.session.query(ClassData.display_order).filter(ClassData.id == adm_id_int).scalar()
        cur_order = db.session.query(ClassData.display_order).filter(ClassData.id == cur_id_int).scalar()

        adm_order = adm_order if adm_order is not None else 0
        cur_order = cur_order if cur_order is not None else 0

        # admission display_order must be strictly less than current class display_order
        if not (adm_order < cur_order):
            return jsonify({"message": "For existing students, Admission class must be of lower display order than Current class."}), 400




    return jsonify({"message": "Admission details are valid", "verifiedData": verified_data}), 200