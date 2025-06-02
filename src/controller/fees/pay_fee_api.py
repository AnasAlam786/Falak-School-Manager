# src/controller/pay_fee.py

from flask import render_template, session, url_for, redirect, request, jsonify, Blueprint


from src.model import StudentsDB, StudentSessions, ClassData, StudentsMarks, TeachersLogin
from src.model import ClassAccess
from src import db

from bs4 import BeautifulSoup
from ..auth.login_required import login_required

pay_fee_api_bp = Blueprint( 'pay_fee_api_bp',   __name__)


@pay_fee_api_bp.route('/api/pay_fee', methods=["POST"])
@login_required
def pay_fee_api():
    data = request.json.get("payload", {})
    if not data:
        return jsonify({"message": "No data provided"}), 400
    

    whatsapp_message = "Fees Paid Successfully!\n"

    for fee_record in data:
        print(fee_record)
        student_id = fee_record.get("student_id")
        structure_ids = fee_record.get("structure_ids")

        if not student_id or not structure_ids:
            return jsonify({"message": "Student ID and fee periods aren't provided!"}), 400

        student = StudentsDB.query.filter_by(id=student_id).first()
        if not student:
            return jsonify({"message": f"Student with ID {student_id} not found"}), 404

        whatsapp_message += f"\nFees paid for student: *{student.STUDENTS_NAME}* (ID: {student.id})"

    phone = "8533998822"

    print(whatsapp_message)
    return jsonify({"message": "Paid Successfully", "phone": phone, "whatsapp_message": whatsapp_message}), 200