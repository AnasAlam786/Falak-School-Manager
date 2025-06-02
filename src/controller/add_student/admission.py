# src/controller/admission.py

from flask import render_template, session, url_for, redirect, Blueprint
from sqlalchemy import func

from src.model.StudentsDB import StudentsDB
from src.model.ClassData import ClassData
from src.model.StudentsDB import StudentsDB
from src.model.ClassAccess import ClassAccess

from src import db

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required
from datetime import datetime

admission_bp = Blueprint( 'admission_bp',   __name__)



@admission_bp.route('/admission', methods=["GET", "POST"])
@login_required
@permission_required('admission')
def admission():

    
    user_id = session["user_id"]

    
    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()

    classes = {str(cls.id): cls.CLASS for cls in classes}


    school_id = session["school_id"]

    PersonalInfo = {
            "STUDENTS_NAME": {"label": "Student Name","type": "text", "required":True},  #True
            "DOB": {"label": "DOB", "type": "numeric", "required":True},  #True
            "GENDER": {"label": "Gender", "type": "select", "default": "Select Gender", "required":True,    #True
                        "options": {"" : "Select Gender", "Male" : "Male", "Female" : "Female"}},
            "AADHAAR": {"label": "Aadhar", "type": "numeric", "maxlength": 14, "required":True},   #True

            "Caste": {"label": "Caste", "type": "text", "required":False},

            "Caste_Type": {"label": "Caste Type", "type": "select", "default": "Select Caste Type", "required":True,    #True
                        "options": {"" : "Select Caste Type", "OBC" : "OBC", "GENERAL" : "GENERAL", "ST" : "ST", "SC" : "SC"}},
            

            "RELIGION": {"label": "Religion", "type": "select", "default": "Select Religion", "required": True,   #True
                        "options": {"" : "Select Religion", "Muslim" : "Muslim", "Hindu" : "Hindu", "Christian" : "Christian",
                                    "Sikh" : "Sikh","Buddhist" : "Buddhist","Parsi" : "Parsi","Jain" : "Jain"}},

            "Height": {"label": "Height (cm)", "type": "numeric", "maxlength": 3, "required":False},
            "Weight": {"label": "Weight (kg)", "type": "numeric", "maxlength": 3, "required":False},

            "BLOOD_GROUP": {"label": "Blood Group", "type": "select", "default": "Select Blood Group", "required":False,
                            "options": {"" : "Select Blood Group", "A+" : "A+", "A-" : "A-", "B+" : "B+","B-" : "B-",
                                        "O+" : "O+","O-" : "O-","AB+" : "AB+","AB-" : "AB-"}
                            }
        }

    AcademicInfo = {
            "CLASS": {
                    "label": "Class",
                    "type": "select",
                    "options": {"": "Select Class", **classes},
                    "default": "Select Class",
                    "required": True
                },
            "Section": {
                "label": "Section",
                "type": "select",
                "options": {"" : "Select Section", "A" : "A", "B" : "B", "C" : "C", "D" : "D", "E": "E", "F": "F"},
                "default": "Select Section",
                "required" : True    #True
            },
            "ROLL": {"label": "Roll No", "type": "numeric", "required":True},   #True
            "SR": {"label": "SR No.", "type": "numeric", "required":True},   #True
            "ADMISSION_NO": {"label": "Admission No.", "type": "numeric", "required":True},    #True
            "ADMISSION_DATE": {"label": "Admission Date", "type": "numeric", "required":True},    #True
            "PEN": {"label": "PEN No.", "type": "numeric", "maxlength": 11, "required":False},
            "APAAR": {"label": "APAAR No.", "type": "numeric", "maxlength": 12, "required":False},
            
        }

    GuardianInfo = {
            "FATHERS_NAME": {"label": "Father Name", "type": "text", "required": True},   #True
            "MOTHERS_NAME": {"label": "Mother Name", "type": "text", "required": True},   #True
            "FATHERS_AADHAR": {"label": "Father Aadhar", "type": "numeric", "maxlength": 14, "required":False},
            "MOTHERS_AADHAR": {"label": "Mother Aadhar", "type": "numeric", "maxlength": 14, "required":False},
            "FATHERS_EDUCATION": {
                "label": "Father Qualification",
                "type": "select",
                "options": {
                            "": "Father Qualification",
                            "Primary": "Primary",
                            "Upper Primary": "Upper Primary",
                            "Secondary or Equivalent": "Secondary or Equivalent",
                            "Higher Secondary or Equivalent": "Higher Secondary or Equivalent",
                            "More than Higher Secondary": "More than Higher Secondary",
                            "No Schooling Experience": "No Schooling Experience",

                        },
                "default": "Father Qualification",
                "required": True   #True
            },
            "MOTHERS_EDUCATION": {
                "label": "Mother Qualification",
                "type": "select",
                "options": {
                        "":                "Mother Qualification",
                        "Primary": "Primary",
                        "Upper Primary": "Upper Primary",
                        "Secondary or Equivalent": "Secondary or Equivalent",
                        "Higher Secondary or Equivalent": "Higher Secondary or Equivalent",
                        "More than Higher Secondary": "More than Higher Secondary",
                        "No Schooling Experience": "No Schooling Experience",
                    },
                "default": "Mother Qualification", 
                "required":True   #True
            },
            "FATHERS_OCCUPATION": {
                "label": "Father Occupation",
                "type": "select",
                "options": {
                                "":                   "Father Occupation",
                                "Labour" :            "Labour",
                                "Business":           "Business",
                                "Shop Owner":         "Shop Owner",
                                "Private Job":        "Private Job",
                                "Government Job":     "Government Job",
                                "Farmer":             "Farmer",
                                "Other":              "Other",
                            },
                "default": "Father Occupation", 
                "required": True   #True
            },
            "MOTHERS_OCCUPATION": {
                "label": "Mother Occupation",
                "type": "select",
                "options": {
                                "":                   "Mother Occupation",
                                "Homemaker":          "Homemaker",
                                "Labour" :            "Labour",
                                "Business":           "Business",
                                "Shop Owner":         "Shop Owner",
                                "Private Job":        "Private Job",
                                "Government Job":     "Government Job",
                                "Farmer":             "Farmer",
                                "Other":              "Other",
                            },
                "default": "Mother Occupation", 
                "required": True   #True
            }
        }

    ContactInfo = {
            "ADDRESS": {"label": "Address", "type": "text", "required": True},   #True
            
            
            "PHONE": {"label": "Phone", "type": "numeric", "maxlength": 10, "required":False},   #True
            "ALT_MOBILE": {"label": "Alternate Mobile Number", "type": "numeric", "value": "", "maxlength": 10, "required":False},
            "PIN": {"label": "PIN Code", "type": "numeric", "value": "244001", "maxlength": 6, "required":True},   #True
            "Home_Distance": {
                "label": "School to Home Distance (km)",
                "short_label": "Home Distance",
                "type": "select",
                "options": {"" : "Select Distance", "Less than 1 km" : "Less than 1 km", "Between 1-3 Kms" : "Between 1-3 Kms" ,
                            "Between 3-5 Kms" : "Between 3-5 Kms", "More than 5 Kms": "More than 5 Kms"},
                "default": "Select Distance",
                "required":True
            },
            "EMAIL": {"label": "Email ID", "type": "email", "value": "", "required":False},
        }

    AdditionalInfo = {
            "Previous_School_Marks": {"label": "Previous School Marks", "short_label":"Prv. School Marks", "type": "numeric", "maxlength": 3, "required":False},
            "Previous_School_Attendance": {"label": "Previous School Attendance(%)", "short_label":"Prv. School Attendance", "type": "numeric", "maxlength": 3, "required":False},
            "Previous_School_Name": {"label": "Previous School Name", "short_label":"Prv. School", "type": "text", "required":False},
            "Due_Amount": {"label": "Due Amount (Rs.)", "short_label":"Due", "type": "numeric", "required":False},

            
    }

    #get current date
    current_session_year = str(session["current_session"])[-2:]

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
    AcademicInfo["ADMISSION_DATE"]["value"] = current_date

    AcademicInfo["SR"]["value"] = new_sr
    AcademicInfo["ADMISSION_NO"]["value"] = new_adm
    
    return render_template('admission.html',PersonalInfo=PersonalInfo, AcademicInfo=AcademicInfo, 
                            GuardianInfo=GuardianInfo, ContactInfo=ContactInfo, AdditionalInfo=AdditionalInfo)
    
