# src/controller/fill_marks.py

from flask import request, jsonify, Blueprint, session
from sqlalchemy.orm.attributes import flag_modified

from src import db
from src.model import StudentsMarks_duplicate

update_marks_api_bp = Blueprint('update_marks_api_bp',   __name__)


@update_marks_api_bp.route('/update_marks_api', methods=['POST'])
def update_marks_api():
    data = request.json
    
    marks_id = data.get('marks_id')
    score = data.get('score')
    student_id = data.get('student_id')
    subject_id = data.get('subject_id')
    exam_id = data.get('exam_id')

    current_session_id = session.get("session_id")
    school_id = session.get("school_id")

    

    if not all([student_id, subject_id, exam_id, current_session_id, school_id]):
        return jsonify({"message": "Missing required fields"}), 400

    # 🟩 CASE 1: Update existing mark
    if marks_id and marks_id != "":
        
        student_marks = StudentsMarks_duplicate.query.filter_by(id=marks_id).first()
        print("Received data for update:", data)
        if student_marks:
            student_marks.score = score
            db.session.commit()
            return jsonify({"message": "Updated marks successfully"}), 200
        else:
            return jsonify({"message": "Unable to find student record in database"}), 400

    # 🟩 CASE 2: Try to find an existing record to update (by student + subject + exam)
    existing = StudentsMarks_duplicate.query.filter_by(
        student_id=student_id,
        subject_id=subject_id,
        exam_id=exam_id,
        session_id=current_session_id
    ).first()

    if existing:
        existing.score = score
        db.session.commit()
        return jsonify({"message": "Updated existing marks by composite key", "new_mark_id": existing.id}), 200

    # 🟩 CASE 3: Create new record
    new_mark = StudentsMarks_duplicate(
        student_id=student_id,
        subject_id=subject_id,
        exam_id=exam_id,
        score=score,
        session_id=current_session_id,
        school_id=school_id
    )
    db.session.add(new_mark)
    db.session.commit()

    return jsonify({
        "message": "Inserted new marks successfully",
        "new_mark_id": new_mark.id
    }), 200
