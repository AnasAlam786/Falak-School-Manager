# src/controller/final_admission_api.py

from flask import session, request, jsonify, Blueprint

from src.model import (
    StudentsDB, ClassData, StudentSessions, Schools
    )

from src import db

from datetime import datetime

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

    password = request.form.get("password")
    image = request.files.get("IMAGE")

    if image:
        if not image.filename.lower().endswith(('.jpg', '.jpeg')):
            return jsonify({"message": "Invalid image format, Please upload a JPG or JPEG image."}), 400

    school_id=session["school_id"]

    if not password:
        return jsonify({"message": "Missing password"}), 400

    # 2) Lookup school
    school = Schools.query.filter_by(id=school_id).first()
    if not school:
        return jsonify({"message": "School not found"}), 404

    # 3) Verify password
    if not check_password_hash(school.Password, password):
        return jsonify({"message": "Wrong password"}), 401
    

    data = dict(request.form)
    data.pop('password', None)
    data.pop('IMAGE', None)    

    StudentDB_colums = {column.name for column in StudentsDB.__table__.columns}
    StudentDB_data = {key: value for key, value in data.items() if key in StudentDB_colums}

    StudentsSession_colums = {column.name for column in StudentSessions.__table__.columns}
    StudentsSession_data = {key: value for key, value in data.items() if key in StudentsSession_colums}



    # handling Date fields
    date_fields = ["DOB", "ADMISSION_DATE"]
    for field in date_fields:
        try:
            value = data[field].replace("/", "-")
            parsed_date = None
            for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                try:
                    parsed_date = datetime.strptime(value, fmt).date()
                    break
                except ValueError:
                    continue
            if not parsed_date:
                return jsonify({"message": f"Invalid date format for {field}. Expected DD-MM-YYYY or YYYY-MM-DD."}), 400
            StudentDB_data[field] = parsed_date
        except KeyError:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    # handling Date fields END


    # handling Aadhar fields
    aadhar_fields = ['MOTHERS_AADHAR', 'AADHAAR', 'FATHERS_AADHAR']
    for field in aadhar_fields:
        raw = data.get(field)
        if raw:
            StudentDB_data[field] = raw.replace('-', '').replace(' ', '')
        else:
            StudentDB_data[field] = None
    # handling Aadhar fields End
    

    
    StudentDB_data["school_id"] = school_id
    StudentDB_data["Admission_Class"] = data["CLASS"]
    StudentDB_data["session_id"] = session["session_id"]


    StudentsSession_data["class_id"] = data["CLASS"]
    StudentsSession_data["session_id"] = session["session_id"]
    StudentsSession_data["created_at"] = StudentDB_data["ADMISSION_DATE"]
    StudentsSession_data["Section"] = data["Section"]
    

    for key, value in StudentDB_data.items():
        if value == "":
            StudentDB_data[key] = None

    for key, value in StudentsSession_data.items():
        if value == "":
            StudentsSession_data[key] = None

    if image:
        try:
            folder_id = school.students_image_folder_id
            image_id = upload_image(image, data["ADMISSION_NO"], folder_id)
            StudentDB_data["IMAGE"] = image_id
            print('Uploaded image Drive ID:', image_id)
        except Exception as e:
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