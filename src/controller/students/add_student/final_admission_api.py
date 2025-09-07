# src/controller/final_admission_api.py

from flask import session, request, jsonify, Blueprint

from src.model import (
    StudentsDB, ClassData, StudentSessions, Schools
    )

from src import db

from werkzeug.security import check_password_hash

from src.controller.students.utils.upload_image import upload_image, delete_image

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required
from src.model.RTEInfo import RTEInfo

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

    # if not password:
    #     return jsonify({"message": "Missing password"}), 400

    # 2) Lookup school
    # school = Schools.query.filter_by(id=school_id).first()
    # if not school:
    #     return jsonify({"message": "School not found"}), 404

    # 3) Verify password
    # if not check_password_hash(school.Password, password):
    #     return jsonify({"message": "Wrong password"}), 401
      

    StudentDB_colums = {column.name for column in StudentsDB.__table__.columns}
    StudentsSession_colums = {column.name for column in StudentSessions.__table__.columns}
    RTEInfo_colums = {column.name for column in RTEInfo.__table__.columns}

    StudentDB_data = {key: value for key, value in data.items() if key in StudentDB_colums}    
    StudentsSession_data = {key: value for key, value in data.items() if key in StudentsSession_colums}
    rte_info_data = {key: value for key, value in data.items() if key in RTEInfo_colums}


    
    StudentDB_data["school_id"] = school_id
    StudentDB_data["Admission_Class"] = data["CLASS"]
    StudentDB_data["session_id"] = session["session_id"]


    StudentsSession_data["class_id"] = data["CLASS"]
    StudentsSession_data["session_id"] = session["session_id"]
    StudentsSession_data["created_at"] = StudentDB_data["ADMISSION_DATE"]
    StudentsSession_data["Section"] = data["Section"]
    
    try:
        # Step 1: Insert student (without image yet)
        new_student = StudentsDB(**StudentDB_data)
        db.session.add(new_student)
        db.session.flush()  # assign new_student.id (but not committed yet)

        # Step 2: Prepare student session + RTE row
        student_session = StudentSessions(
            student_id=new_student.id,
            **StudentsSession_data
        )
        rte_row = RTEInfo(
            student_id=new_student.id,
            **rte_info_data
        )
        db.session.add(student_session)
        db.session.add(rte_row)

        # Step 3: Upload image using admission no or student id
        if image:
            encoded_image = image.split(",")[1]
            school = Schools.query.filter_by(id=school_id).first()
            folder_id = school.students_image_folder_id
            image_id = upload_image(encoded_image, data.get("ADMISSION_NO"), folder_id)

            # update field before commit
            new_student.IMAGE = image_id

        # Step 4: Commit everything together
        db.session.commit()

        return jsonify({
            "message": "Data submitted successfully",
            "student_id": new_student.id,
            "image_id": new_student.IMAGE
        }), 200

    except Exception as e:
        db.session.rollback()
        if 'image_id' in locals():
            delete_image(image_id)  # cleanup orphan image
        print('Error while adding student:', str(e))
        return jsonify({"message": f"Failed to add student: {str(e)}"}), 500
