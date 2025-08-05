# src/controller/update/update_student_image.py


from flask import session, Blueprint, request, jsonify

from src.model.Schools import Schools
from src.model.StudentsDB import StudentsDB
from src.model.StudentsDB import StudentsDB

from src import db

from src.controller.students.utils.upload_image import upload_image, delete_image, move_image

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

final_student_update_api_bp = Blueprint( 'final_student_update_api_bp',   __name__)

@final_student_update_api_bp.route('/api/final_student_update_api', methods=["POST"])
@login_required
@permission_required('admission')
def final_student_update_api():
    print("Final Student Update API called")

    user_id = session["user_id"]
    school_id = session["school_id"]

    student_id = request.json.get("student_id")
    image_status = request.json.get("image_status")
    image = request.json.get("image", None)
    form_data = request.json.get("formData", None)

    if not student_id:
        return jsonify({"message": "Missing student id"}), 400
    if not image_status:
        return jsonify({"message": "Missing image status"}), 400

    student = db.session.query(StudentsDB).filter_by(id=student_id).first()
    school = db.session.query(Schools).filter_by(id=school_id).first()

    if not student:
        return jsonify({"message": "Student not found"}), 404
    if not school:
        return jsonify({"message": "School not found"}), 404

    deleted_images_folder_id = "1e8iHskcj2Vtv_Mg_Mtp4BzdHocuhLd_f"

    try:
        if image_status == "updated" and image:

            encoded_image = image.split(",")[1]
            folder_id = school.students_image_folder_id

            image_id = upload_image(encoded_image, student.ADMISSION_NO, folder_id)
            if student.IMAGE:
                # is_deleted = delete_image(student.IMAGE)
                # if not is_deleted:
                move_image(student.IMAGE, deleted_images_folder_id, 
                        rename=str(student.id))

            student.IMAGE = image_id
            db.session.commit()

        elif image_status == "removed" and student.IMAGE and not image:
            old_image_id = student.IMAGE
            student.IMAGE = None

            # is_deleted = delete_image(old_image_id)
            # if not is_deleted:
            move_image(old_image_id, deleted_images_folder_id, 
                    rename=str(student.id))


            db.session.commit()
        else:
            print("No image update required")
            return jsonify({"message": "You have not updated the image"}), 400

    except Exception as e:
        db.session.rollback()
        if 'image_id' in locals():

            is_deleted = delete_image(image_id)
            if not is_deleted:
                move_image(student.IMAGE, deleted_images_folder_id,
                           rename=f"{school_id}-{student.ADMISSION_NO}")

        print(f"Image handling error: {e}")
        return jsonify({"message": f"Image handling error: {e}"}), 400

    return jsonify({"message": "Student information updated successfully"}), 200
   