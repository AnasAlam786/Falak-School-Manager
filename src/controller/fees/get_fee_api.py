# src/controller/get_fee.py

from flask import render_template, session, url_for, redirect, request, jsonify, Blueprint
from sqlalchemy import and_ 

from src.model import (StudentsDB, StudentSessions, ClassData, 
                       FeeStructure, FeeAmount, FeeData)
from src import db

from bs4 import BeautifulSoup
from datetime import datetime
from ..auth.login_required import login_required

get_fee_api_bp = Blueprint( 'get_fee_api_bp',   __name__)


@get_fee_api_bp.route('/api/get_fee', methods=["POST"])
@login_required
def get_fee_api():
    data = request.json

    student_id = data.get('student_id')
    family_id = data.get('family_id')

    current_month = datetime.now().month


    if not student_id:
        return jsonify({"message": "Student not found"}), 404
    

    current_session = session["session_id"]
    school_id = session["school_id"]

    siblings = db.session.query(
        StudentsDB.id,
        StudentsDB.STUDENTS_NAME,
        ClassData.CLASS,
        StudentSessions.ROLL,
        FeeAmount.amount.label('fee_amount'),
    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData, StudentSessions.class_id == ClassData.id
    ).join(
        FeeAmount, ClassData.id == FeeAmount.class_id
    ).filter(
        StudentsDB.family_id == family_id,
        StudentSessions.session_id == current_session,
        FeeAmount.session_id == current_session,
    ).all()

    sibling_ids = [s.id for s in siblings]

    if not siblings:
        return jsonify({"message": "Student not found"}), 404
    

    fee_structures = db.session.query(
        FeeStructure.id.label('structure_id'),
        FeeStructure.period_name,
        FeeStructure.sequence_number
    ).filter(
        FeeStructure.school_id == school_id
    ).order_by(
        FeeStructure.sequence_number
    ).all()


    fee_data_all = db.session.query(
        FeeData.id.label('fee_data_id'),
        FeeData.paid_at,
        FeeData.paid_amount,
        FeeData.structure_id,
        FeeData.student_id
    ).filter(
        FeeData.student_id.in_(sibling_ids),
        FeeData.session_id == current_session
    ).all()


    # Convert fee_data_all into a dictionary for quick lookup
    fee_data_dict = {
        (data.student_id, data.structure_id): data for data in fee_data_all
    }


    # Prepare the final result
    result = []

    for sibling in siblings:
        sibling_info = {
            'id': sibling.id,
            'student_name': sibling.STUDENTS_NAME,
            'class': sibling.CLASS,
            'roll': sibling.ROLL,
            'total_fee_amount': sibling.fee_amount,
            'fee_data': []
        }

        for structure in fee_structures:
            fee_data = fee_data_dict.get((sibling.id, structure.structure_id))

            fee_info = {
                'structure_id': structure.structure_id,
                'period_name': structure.period_name,
                'sequence_number': structure.sequence_number,
                'paid_amount': fee_data.paid_amount if fee_data else 0,
                'paid_at': fee_data.paid_at.isoformat() if fee_data and fee_data.paid_at else None,
                'fee_data_id': fee_data.fee_data_id if fee_data else None
            }

            sibling_info['fee_data'].append(fee_info)

        result.append(sibling_info)



    content = render_template('fees_modal.html', student_fee_data=result, current_month=current_month)
    return jsonify({"html": str(content)})

    