# src/controller/final_admission_api.py

from flask import session, request, jsonify, Blueprint

from src.model import (
    StudentsDB, ClassData, StudentSessions, Schools
    )

from src import db

import base64

from werkzeug.security import check_password_hash

from .utils.upload_image import upload_image, delete_image
from .utils.create_watsapp_message import watsapp_message
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

final_admission_api_bp = Blueprint( 'final_admission_api_bp',   __name__)


@final_admission_api_bp.route('/final_admission_api', methods=["POST"])
@login_required
@permission_required('admission')
def final_admission_api():
    data = request.get_json()

    password = data.get("password")
    image = data.get("image", None)
    verified_data = data.get("verifiedData", None)
    school_id=session["school_id"]


    data = {}
    for input_data in verified_data:
        data[input_data["field"]] = input_data["value"]

    if not password:
        return jsonify({"message": "Missing password"}), 400

    # 2) Lookup school
    school = Schools.query.filter_by(id=school_id).first()
    if not school:
        return jsonify({"message": "School not found"}), 404

    # 3) Verify password
    if not check_password_hash(school.Password, password):
        return jsonify({"message": "Wrong password"}), 401
      

    StudentDB_colums = {column.name for column in StudentsDB.__table__.columns}
    StudentsSession_colums = {column.name for column in StudentSessions.__table__.columns}

    StudentDB_data = {key: value for key, value in data.items() if key in StudentDB_colums}    
    StudentsSession_data = {key: value for key, value in data.items() if key in StudentsSession_colums}


    
    StudentDB_data["school_id"] = school_id
    StudentDB_data["Admission_Class"] = data["CLASS"]
    StudentDB_data["session_id"] = session["session_id"]


    StudentsSession_data["class_id"] = data["CLASS"]
    StudentsSession_data["session_id"] = session["session_id"]
    StudentsSession_data["created_at"] = StudentDB_data["ADMISSION_DATE"]
    StudentsSession_data["Section"] = data["Section"]
    

    if image:
        try:
        
            encoded_image = image.split(",")[1]

            folder_id = school.students_image_folder_id
            image_id = upload_image(encoded_image, data["ADMISSION_NO"], folder_id)

            StudentDB_data["IMAGE"] = image_id
            print('Uploaded image Drive ID:', image_id)
        except Exception as e:
            print(f"Error uploading image: {e}")
            return jsonify({"message": f"Error uploading image: {e}"}), 400

    try:    
        # Adding new rows in StudentsDB and StudentSessions tables
        new_student = StudentsDB(**StudentDB_data)
        db.session.add(new_student)
        db.session.flush()  # Flush to get new_student.id

        student_session = StudentSessions(
            student_id=new_student.id, 
            **StudentsSession_data
        )
        db.session.add(student_session)
        db.session.flush()

        db.session.commit()


        # now fetch the newly added studentDB and studentSession joined data
        student_data = db.session.query(
            StudentsDB, StudentSessions, ClassData, Schools
        ).join(
            StudentSessions, StudentsDB.id == StudentSessions.student_id
        ).join(
            ClassData, ClassData.id == StudentSessions.class_id
        ).join(
            Schools, Schools.id == StudentsDB.school_id
        ).filter(
            Schools.id == school_id,
            StudentsDB.id == new_student.id,
            StudentSessions.id == student_session.id,
        ).first()

        message = watsapp_message(student_data)
        print('WhatsApp message:', message)

        return jsonify({"message": "Data submitted successfully", "watsapp_message": message}), 200

    except Exception as e:
        db.session.rollback()  # Undo everything

        if 'image_id' in locals():  # If image upload was successful, delete the image
            delete_image(image_id)

        print('Error while adding student:', str(e))
        return jsonify({"message": "Failed to add student"}), 500