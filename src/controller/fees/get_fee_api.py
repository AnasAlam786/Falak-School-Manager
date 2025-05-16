# src/controller/get_fee.py

from flask import render_template, session, url_for, redirect, request, jsonify, Blueprint
from sqlalchemy import and_ 

from src.model import (StudentsDB, StudentSessions, ClassData, 
                       FeeStructure, FeeAmount, FeeData)
from src import db

from bs4 import BeautifulSoup
from ..auth.login_required import login_required

get_fee_api_bp = Blueprint( 'get_fee_api_bp',   __name__)


@get_fee_api_bp.route('/api/get_fee', methods=["POST"])
@login_required
def get_fee_api():
    data = request.json

    student_id = data.get('student_id')


    if not student_id:
        return jsonify({"message": "Student not found"}), 404
    

    current_session = session["session_id"]
    school_id = session["school_id"]

    student_data = db.session.query(
        StudentsDB.id,
        StudentsDB.STUDENTS_NAME,
        ClassData.CLASS,
        StudentSessions.ROLL,
    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData, StudentSessions.class_id == ClassData.id
    ).join(
        FeeAmount, ClassData.id == FeeAmount.class_id
    ).filter(
        StudentsDB.id == student_id,
        StudentSessions.session_id == current_session
    ).first()

    if not student_data:
        return jsonify({"message": "Student not found"}), 404


    fee_data = db.session.query(
        FeeStructure.id.label('structure_id'),
        FeeStructure.period_name,
        FeeData.id.label('fee_data_id'),
        # Add other columns you need from FeeStructure and FeeData
    ).outerjoin(
        FeeData, 
        and_(
            FeeStructure.id == FeeData.structure_id,
            FeeData.student_id == student_id,
            FeeData.session_id == current_session
        )
    ).filter(
        FeeStructure.school_id == school_id
    ).all()



    fee_dicts = [row._asdict() for row in fee_data]

    print(student_data)
    print(fee_dicts)

    content = render_template('fee_modal.html', student_data=student_data, fee_data=fee_data)
    return jsonify({"html":str(content)})
    



