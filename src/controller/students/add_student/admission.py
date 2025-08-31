# src/controller/admission.py

from flask import render_template, session, Blueprint
from sqlalchemy import func

from src.model.StudentsDB import StudentsDB
from src.model.ClassData import ClassData
from src.model.StudentsDB import StudentsDB
from src.model.ClassAccess import ClassAccess

from src import db

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

from src.controller.students.utils.pydantic_to_fields import pydantic_model_to_field_dicts
from src.controller.students.utils.admission_form_schema import (PersonalInfoModel, AcademicInfoModel, 
                                           GuardianInfoModel, ContactInfoModel, 
                                           AdditionalInfoModel)
from datetime import datetime

admission_bp = Blueprint( 'admission_bp',   __name__)



@admission_bp.route('/admission', methods=["GET", "POST"])
@login_required
@permission_required('admission')
def admission():

    
    user_id = session["user_id"]
    school_id = session["school_id"]

    
    
    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()

    classes = {str(cls.id): cls.CLASS for cls in classes}

    AcademicInfo = pydantic_model_to_field_dicts(AcademicInfoModel)
    GuardianInfo = pydantic_model_to_field_dicts(GuardianInfoModel)
    AdditionalInfo = pydantic_model_to_field_dicts(AdditionalInfoModel)
    ContactInfo = pydantic_model_to_field_dicts(ContactInfoModel)
    PersonalInfo = pydantic_model_to_field_dicts(PersonalInfoModel)

 
    #get current date
    current_session_year = str(session["session_id"])[-2:]

    max_sr, max_adm = (
        StudentsDB.query
            .with_entities(
                func.max(StudentsDB.SR).label("max_sr"),
                func.max(StudentsDB.ADMISSION_NO).label("max_adm")
            )
            .filter(
                StudentsDB.school_id == school_id,
            )
            .first()
    )

    if max_sr is None:
        max_sr = 0
    if max_adm is None or str(max_adm)[:2] != current_session_year:
        max_adm = int(current_session_year + "000")
    
    new_adm = max_adm + 1
    new_sr = max_sr + 1

    current_date = datetime.now().strftime("%Y-%m-%d")

    for academic_inputfield in AcademicInfo:
        if academic_inputfield["id"] == "CLASS":
            academic_inputfield["options"] = {"": "Select Class", **classes}
        if academic_inputfield["id"] == "ADMISSION_DATE":
            academic_inputfield["value"] = current_date
        if academic_inputfield["id"] == "ADMISSION_NO":
            academic_inputfield["value"] = new_adm
        if academic_inputfield["id"] == "SR":
            academic_inputfield["value"] = new_sr

    
    return render_template('admission.html',PersonalInfo=PersonalInfo, AcademicInfo=AcademicInfo, 
                            GuardianInfo=GuardianInfo, ContactInfo=ContactInfo, AdditionalInfo=AdditionalInfo)
    
