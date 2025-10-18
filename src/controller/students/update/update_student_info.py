# src/controller/update/update_student_info.py

from flask import jsonify, render_template, session, Blueprint, request

from sqlalchemy.orm import aliased
from datetime import date, datetime

from src.model.RTEInfo import RTEInfo
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

def fill_field_values(field_dicts, student_data):
    for field in field_dicts:
        column_name = field.get("id")
        if column_name in student_data:
            value = student_data[column_name]
            if value:
                field["value"] = value
    return field_dicts


@update_student_info_bp.route('/update_student_info', methods=["GET"])
@login_required
@permission_required('update_student')
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

    AdmissionClass = aliased(ClassData)
    CurrentClass = aliased(ClassData)

    student = (
        db.session.query(StudentsDB, StudentSessions, RTEInfo)
        .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
        .join(AdmissionClass, StudentsDB.Admission_Class == AdmissionClass.id)
        .join(CurrentClass, StudentSessions.class_id == CurrentClass.id)
        .outerjoin(RTEInfo, RTEInfo.student_id == StudentsDB.id)
        .filter(
            StudentsDB.id == student_id,
            StudentSessions.session_id == current_session,
            CurrentClass.id.in_(class_ids)
        )
        .first()
    )

    if student:
        student_db, student_session, rte_info = student
        print(
            {**student_db.__dict__, **student_session.__dict__, **(rte_info.__dict__ if rte_info else {})}
        )
    else:
        print("No student found.")


    if not student:
        return jsonify({"message": "Student not found"}), 404

    studentDB, sessionDB, rte_info = student
    student_data = {}

    # Add StudentSessions data
    student_data.update({
        f"{col.name}": getattr(sessionDB, col.name)
        for col in sessionDB.__table__.columns
    })

    # Add studentDB data
    student_data.update({
        f"{col.name}": getattr(studentDB, col.name)
        for col in studentDB.__table__.columns
    })

    # Add rte_info data
    if rte_info:
        student_data.update({
            f"{col.name}": getattr(rte_info, col.name)
            for col in rte_info.__table__.columns
        })

    student_data.update({
        "id": studentDB.id,
    })

    

    AcademicInfo = pydantic_model_to_field_dicts(AcademicInfoModel)
    GuardianInfo = pydantic_model_to_field_dicts(GuardianInfoModel)
    AdditionalInfo = pydantic_model_to_field_dicts(AdditionalInfoModel)
    ContactInfo = pydantic_model_to_field_dicts(ContactInfoModel)
    PersonalInfo = pydantic_model_to_field_dicts(PersonalInfoModel)

    AcademicInfo = fill_field_values(AcademicInfo, student_data)
    GuardianInfo = fill_field_values(GuardianInfo, student_data)
    AdditionalInfo = fill_field_values(AdditionalInfo, student_data)
    ContactInfo = fill_field_values(ContactInfo, student_data)
    PersonalInfo = fill_field_values(PersonalInfo, student_data)



    classes_dict = {str(cls.id): cls.CLASS for cls in classes}
    
    admission_session_select = {}
    for year in session["all_sessions"]:
        year = int(year)
        admission_session_select[year] = f"{year}-{year+1}"

    for academic_inputfield in AcademicInfo:
        if academic_inputfield["id"] == "CLASS":
            academic_inputfield["options"] = {"": "Select Class", **classes_dict}
            academic_inputfield["value"] = student_data.get("class_id")
            academic_inputfield["disabled"] = True

        if academic_inputfield["id"] == "Admission_Class":
            academic_inputfield["options"] = {"": "Select Class", **classes_dict}
            academic_inputfield["value"] = student_data.get("Admission_Class")

        if academic_inputfield["id"] == "admission_session_id":
            academic_inputfield["options"] = {"": "Select admission session", **admission_session_select}
            academic_inputfield["disabled"] = True

        if academic_inputfield["id"] == "ADMISSION_DATE":
            try:
                academic_inputfield["value"] = academic_inputfield["value"].strftime('%d-%m-%Y') 
            except: pass

    # Ensure DOB in PersonalInfo (if present as a date/datetime) is formatted to Indian date string dd-mm-YYYY
    for PersonalInfo_field in PersonalInfo:
        if PersonalInfo_field["id"] == "DOB":
            try:
                PersonalInfo_field["value"] = PersonalInfo_field.get("value").strftime('%d-%m-%Y')
            except: pass


    return render_template('edit_student.html', PersonalInfo=PersonalInfo, AcademicInfo=AcademicInfo,
                           GuardianInfo=GuardianInfo, ContactInfo=ContactInfo, AdditionalInfo=AdditionalInfo, student=student_data)