# src/controller/update/update_student_image.py


from flask import session, Blueprint, request, jsonify

from src.model.Schools import Schools
from src.model.StudentsDB import StudentsDB
from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions

from src import db

from src.controller.students.utils.upload_image import upload_image, delete_image, move_image
from src.controller.students.utils.admission_form_schema import (
    PersonalInfoModel, AcademicInfoModel, GuardianInfoModel, ContactInfoModel, AdditionalInfoModel
)
from pydantic import ValidationError
from sqlalchemy import or_, and_
from collections import defaultdict

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

final_student_update_api_bp = Blueprint( 'final_student_update_api_bp',   __name__)

@final_student_update_api_bp.route('/api/final_student_update_api', methods=["POST"])
@login_required
@permission_required('admission')
def final_student_update_api():
    user_id = session["user_id"]
    school_id = session["school_id"]
    data = request.json
    student_id = data.get("student_id")
    image_status = data.get("image_status")
    image = data.get("image", None)
    form_data = data.get("formData", None)

    if not student_id:
        return jsonify({"message": "Missing student id"}), 400
    if not image_status:
        return jsonify({"message": "Missing image status"}), 400
    if not form_data:
        return jsonify({"message": "Missing form data"}), 400

    student = db.session.query(StudentsDB).filter_by(id=student_id).first()
    school = db.session.query(Schools).filter_by(id=school_id).first()
    if not student:
        return jsonify({"message": "Student not found"}), 404
    if not school:
        return jsonify({"message": "School not found"}), 404

    # --- Parse and group form data ---
    grouped_data = defaultdict(dict)
    groups = ["PersonalInfo", "AcademicInfo", "GuardianInfo", "ContactInfo", "AdditionalInfo"]
    for field_name, field_value in form_data.items():
        if '-' in field_name:
            section, field = field_name.split('-', 1)
            if section in groups:
                grouped_data[section][field] = field_value

    # --- Validate using pydantic models ---
    verified_data = []
    try:
        personal_data = PersonalInfoModel(**grouped_data['PersonalInfo'])
        verified_data.extend(personal_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field": error_field}), 400
    try:
        academic_data = AcademicInfoModel(**grouped_data['AcademicInfo'])
        verified_data.extend(academic_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field": error_field}), 400
    try:
        guardian_data = GuardianInfoModel(**grouped_data['GuardianInfo'])
        verified_data.extend(guardian_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field": error_field}), 400
    try:
        contact_data = ContactInfoModel(**grouped_data['ContactInfo'])
        verified_data.extend(contact_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field": error_field}), 400
    try:
        additional_data = AdditionalInfoModel(**grouped_data['AdditionalInfo'])
        verified_data.extend(additional_data.verified_model_dump())
    except ValidationError as e:
        error_field = e.errors()[0]["loc"][0]
        clean_field_name = error_field.title().replace("_", " ")
        return jsonify({'message': f"Please enter valid {clean_field_name}", "field": error_field}), 400

    # --- Uniqueness checks (excluding current student) ---
    pen = apaar = aadhaar = sr = admission_no = class_id = section = roll = None
    for item in verified_data:
        if item["field"] == "PEN": pen = item["value"]
        if item["field"] == "APAAR": apaar = item["value"]
        if item["field"] == "AADHAAR": aadhaar = item["value"]
        if item["field"] == "SR": sr = item["value"]
        if item["field"] == "ADMISSION_NO": admission_no = item["value"]
        if item["field"] == "CLASS": class_id = item["value"]
        if item["field"] == "Section": section = item["value"]
        if item["field"] == "ROLL": roll = item["value"]

    global_conflict_conditions = []
    school_conflict_conditions = []
    if pen: global_conflict_conditions.append(and_(StudentsDB.PEN == pen, StudentsDB.id != student_id))
    if apaar: global_conflict_conditions.append(and_(StudentsDB.APAAR == apaar, StudentsDB.id != student_id))
    if aadhaar: global_conflict_conditions.append(and_(StudentsDB.AADHAAR == aadhaar, StudentsDB.id != student_id))
    if sr: school_conflict_conditions.append(and_(StudentsDB.SR == sr, StudentsDB.id != student_id))
    if admission_no: school_conflict_conditions.append(and_(StudentsDB.ADMISSION_NO == admission_no, StudentsDB.id != student_id))

    if global_conflict_conditions:
        global_conflict = StudentsDB.query.filter(
            StudentsDB.school_id == school_id,
            or_(*global_conflict_conditions)
        ).first()
        if global_conflict:
            return jsonify({'message': 'Either PEN, APAAR, or AADHAAR is already in use.'}), 400
    if school_conflict_conditions:
        school_conflict = StudentsDB.query.filter(
            StudentsDB.school_id == school_id,
            or_(*school_conflict_conditions)
        ).first()
        if school_conflict:
            return jsonify({'message': 'SR or Admission no already exists.'}), 400
    # Check current-session/class/section/roll uniqueness (excluding current student)
    if not class_id or not section or not roll:
        return jsonify({'message': 'Missing Class, Section, or ROLL for session check.'}), 400
    session_conflict = (
        StudentSessions.query
        .join(StudentsDB, StudentSessions.student_id == StudentsDB.id)
        .filter(
            StudentsDB.school_id == school_id,
            StudentSessions.session_id == session["session_id"],
            StudentSessions.class_id == class_id,
            StudentSessions.Section == section,
            StudentSessions.ROLL == roll,
            StudentSessions.student_id != student_id
        )
        .first()
    )
    if session_conflict:
        return jsonify({'message': 'This class/section/roll is already assigned in the current session.'}), 400

    # --- Update student fields ---
    StudentDB_colums = {column.name for column in StudentsDB.__table__.columns}
    StudentsSession_colums = {column.name for column in StudentSessions.__table__.columns}
    StudentDB_data = {key: value for key, value in {**grouped_data['PersonalInfo'], **grouped_data['AcademicInfo'], **grouped_data['GuardianInfo'], **grouped_data['ContactInfo'], **grouped_data['AdditionalInfo']}.items() if key in StudentDB_colums}
    StudentsSession_data = {key: value for key, value in {**grouped_data['PersonalInfo'], **grouped_data['AcademicInfo'], **grouped_data['GuardianInfo'], **grouped_data['ContactInfo'], **grouped_data['AdditionalInfo']}.items() if key in StudentsSession_colums}
    # Update StudentsDB
    for key, value in StudentDB_data.items():
        setattr(student, key, value)
    # Update StudentSessions (current session/class/section)
    student_session = StudentSessions.query.filter_by(student_id=student_id, session_id=session["session_id"]).first()
    if student_session:
        for key, value in StudentsSession_data.items():
            setattr(student_session, key, value)
    # --- Handle image update as before ---
    deleted_images_folder_id = "1e8iHskcj2Vtv_Mg_Mtp4BzdHocuhLd_f"
    try:
        if image_status == "updated" and image:
            encoded_image = image.split(",")[1]
            folder_id = school.students_image_folder_id
            image_id = upload_image(encoded_image, student.ADMISSION_NO, folder_id)
            if student.IMAGE:
                move_image(student.IMAGE, deleted_images_folder_id, rename=str(student.id))
            student.IMAGE = image_id
        elif image_status == "removed" and student.IMAGE and not image:
            old_image_id = student.IMAGE
            student.IMAGE = None
            move_image(old_image_id, deleted_images_folder_id, rename=str(student.id))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Image handling error: {e}"}), 400
    return jsonify({"message": "Student information updated successfully"}), 200
   