# src/controller/fill_marks.py

from flask import request, jsonify, Blueprint

from sqlalchemy.orm.attributes import flag_modified

from src import db
from src.model import StudentsMarks

update_marks_api_bp = Blueprint('update_marks_api_bp',   __name__)


@update_marks_api_bp.route('/update_marks_api', methods=['POST'])
def update_marks_api():

    data = request.json

    #subject = data.get('subject')
    exam = data.get('exam')
    score = data.get('value')
    id = data.get('id')

    student = StudentsMarks.query.filter_by(id=id).first()

    if student:

        setattr(student, exam, score)
        flag_modified(student, exam)
        
        db.session.commit()
        return jsonify({"message": "Updated marks succesfully"}), 200
    
    return jsonify({"message": "Unable to find student record in database"}), 400