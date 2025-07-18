# src/controller/update/update_student_info.py

from flask import jsonify, render_template, session, Blueprint, request

from src.model.StudentsDB import StudentsDB
from src.model.ClassData import ClassData
from src.model.StudentsDB import StudentsDB
from src.model.ClassAccess import ClassAccess
from src.model.StudentSessions import StudentSessions

from src.controller.students.utils.pydantic_to_fields import pydantic_model_to_field_dicts
from src.controller.students.utils.admission_form_schema import (PersonalInfoModel, AcademicInfoModel, 
                                           GuardianInfoModel, ContactInfoModel, 
                                           AdditionalInfoModel)

from src import db

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

update_student_info_bp = Blueprint( 'update_student_info_bp',   __name__)

def fill_field_values(field_dicts, student_obj):
    for field in field_dicts:
        column_name = field.get("id")
        if hasattr(student_obj, column_name):
            value = getattr(student_obj, column_name)
            if value:
                field["value"] = value
    return field_dicts


@update_student_info_bp.route('/update_student_info', methods=["GET"])
@login_required
@permission_required('admission')
def update_student_info():
    student_id = request.args.get('id')
    user_id = session["user_id"]
    current_session = session["session_id"]

    
    
    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()
    

    class_ids = [cls.id for cls in classes]
    student = (
        db.session.query(StudentsDB)
        .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
        .join(ClassData, StudentSessions.class_id == ClassData.id)
        .filter(
            StudentsDB.id == student_id,
            StudentSessions.session_id == current_session,
            ClassData.id.in_(class_ids)
        ).first()
    )

    if not student:
        return jsonify({"message": "Student not found"}), 404


    AcademicInfo = pydantic_model_to_field_dicts(AcademicInfoModel)
    GuardianInfo = pydantic_model_to_field_dicts(GuardianInfoModel)
    AdditionalInfo = pydantic_model_to_field_dicts(AdditionalInfoModel)
    ContactInfo = pydantic_model_to_field_dicts(ContactInfoModel)
    PersonalInfo = pydantic_model_to_field_dicts(PersonalInfoModel)

    AcademicInfo = fill_field_values(AcademicInfo, student)
    GuardianInfo = fill_field_values(GuardianInfo, student)
    AdditionalInfo = fill_field_values(AdditionalInfo, student)
    ContactInfo = fill_field_values(ContactInfo, student)
    PersonalInfo = fill_field_values(PersonalInfo, student)




    classes_dict = {str(cls.id): cls.CLASS for cls in classes}
    for academic_inputfield in AcademicInfo:
        if academic_inputfield["id"] == "CLASS":
            academic_inputfield["options"] = {"": "Select Class", **classes_dict}
            break

    return render_template('edit_student.html', PersonalInfo=PersonalInfo, AcademicInfo=AcademicInfo,
                           GuardianInfo=GuardianInfo, ContactInfo=ContactInfo, AdditionalInfo=AdditionalInfo, student=student)


    