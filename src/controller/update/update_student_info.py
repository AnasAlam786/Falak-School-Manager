# src/controller/update/update_student_info.py

from flask import render_template, session, Blueprint
from sqlalchemy import func

from src.model.StudentsDB import StudentsDB
from src.model.ClassData import ClassData
from src.model.StudentsDB import StudentsDB
from src.model.ClassAccess import ClassAccess

from src import db

from ..utils.admission_fields import AdmissionFields
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required
from datetime import datetime

update_student_info_bp = Blueprint( 'update_student_info_bp',   __name__)

@update_student_info_bp.route('/update_student_info', methods=["GET", "POST"])
@login_required
@permission_required('admission')
def update_student_info():

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
    AdmissionFields.AcademicInfo["CLASS"]["options"] = {"": "Select Class", **classes}


    AcademicInfo = AdmissionFields.AcademicInfo
    GuardianInfo = AdmissionFields.GuardianInfo
    AdditionalInfo = AdmissionFields.AdditionalInfo
    ContactInfo = AdmissionFields.ContactInfo
    PersonalInfo = AdmissionFields.PersonalInfo


    