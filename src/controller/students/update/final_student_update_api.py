# src/controller/update/update_student_image.py


from flask import session, Blueprint, request, jsonify

from src.model.RTEInfo import RTEInfo
from src.model.Schools import Schools
from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions

from src import db

from src.controller.students.utils.upload_image import upload_image, delete_image, move_image

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required
from sqlalchemy.exc import IntegrityError

final_student_update_api_bp = Blueprint( 'final_student_update_api_bp',   __name__)

@final_student_update_api_bp.route('/api/final_student_update_api', methods=["POST"])
@login_required
@permission_required('update_student')
def final_student_update_api():
    school_id = session["school_id"]
    current_session_id = session["session_id"]

    payload = request.get_json(silent=True) or {}
    student_id = payload.get("student_id")
    image_status = payload.get("image_status")
    image = payload.get("image", None)
    verified_items = payload.get("verifiedData")

    if not student_id:
        return jsonify({"message": "Missing student id"}), 400
    if image_status not in {"updated", "removed", "unchanged", None}:
        return jsonify({"message": "Invalid image status"}), 400

    student: StudentsDB | None = (
        db.session.query(StudentsDB).filter_by(id=student_id).first()
    )
    school: Schools | None = (
        db.session.query(Schools).filter_by(id=school_id).first()
    )

    if not student:
        return jsonify({"message": "Student not found"}), 404
    if not school:
        return jsonify({"message": "School not found"}), 404

    # Build a verified_map from either verifiedData (preferred) or formData
    verified_map: dict = {}
    
    if not isinstance(verified_items, list) and not verified_items and not isinstance(verified_items[0], dict):
        # verifiedData like [{field, value, label}, ...]
        return jsonify({"message": "The input fields is not valid. Please try again!"}), 404
    verified_map = {item.get("field"): item.get("value") for item in verified_items}

    # Prepare updates for StudentsDB and StudentSessions
    studentsdb_columns = {column.name for column in StudentsDB.__table__.columns}
    sessions_columns = {column.name for column in StudentSessions.__table__.columns}
    rte_info = {column.name for column in RTEInfo.__table__.columns}

    studentsdb_updates = {
        key: value for key, value in verified_map.items() if key in studentsdb_columns
    }
    sessions_updates = {
        key: value for key, value in verified_map.items() if key in sessions_columns
    }
    rte_info_updates = {
        key: value for key, value in verified_map.items() if key in rte_info
    }

    # Maintain special mappings similar to admission flow
    if "CLASS" in verified_map:
        sessions_updates["class_id"] = verified_map["CLASS"]
    if "Section" in verified_map:
        sessions_updates["Section"] = verified_map["Section"]
    if "ROLL" in verified_map:
        sessions_updates["ROLL"] = verified_map["ROLL"]

    # Persist updates (uniqueness already checked upstream)
    try:
        # Update StudentsDB
        for key, value in studentsdb_updates.items():
            setattr(student, key, value)

        # Update or create current session row
        session_row: StudentSessions | None = (
            db.session.query(StudentSessions)
            .filter(
                StudentSessions.student_id == student.id,
                StudentSessions.session_id == current_session_id,
            )
            .first()
        )

        if not session_row:
            session_row = StudentSessions(
                student_id=student.id,
                session_id=current_session_id,
            )
            db.session.add(session_row)

        for key, value in sessions_updates.items():
            setattr(session_row, key, value)

        # Update or create RTE row
        RTE_row: RTEInfo | None = (
            db.session.query(RTEInfo)
            .filter(
                RTEInfo.student_id == student.id,
            )
            .first()
        )
        if not RTE_row:
            RTE_row = RTEInfo(
                student_id=student.id,
            )
            db.session.add(RTE_row)
        for key, value in rte_info_updates.items():
            setattr(RTE_row, key, value)

        # 6) Image handling
        deleted_images_folder_id = "1e8iHskcj2Vtv_Mg_Mtp4BzdHocuhLd_f"

        if image_status == "updated" and image:
            try:
                encoded_image = image.split(",")[1]
            except Exception:
                return jsonify({"message": "Invalid image payload"}), 400

            folder_id = school.students_image_folder_id
            image_id = upload_image(encoded_image, student.ADMISSION_NO, folder_id)
            if student.IMAGE:
                move_image(
                    student.IMAGE,
                    deleted_images_folder_id,
                    rename=str(student.id),
                )
            student.IMAGE = image_id

        elif image_status == "removed" and student.IMAGE and not image:
            old_image_id = student.IMAGE
            student.IMAGE = None
            move_image(old_image_id, deleted_images_folder_id, rename=str(student.id))

        db.session.commit()

    except IntegrityError as ie:
        db.session.rollback()
        return jsonify({"message": "Conflicting values already exist", "detail": str(ie)}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Failed to update student: {e}"}), 500

    return (
        jsonify(
            {
                "message": "Student information updated successfully",
                "student_id": student.id,
            }
        ),
        200,
    )
   