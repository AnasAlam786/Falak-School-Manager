# src/controller/get_fee.py

from collections import defaultdict
import time
from flask import render_template, session, url_for, redirect, request, jsonify, Blueprint
from sqlalchemy import and_, outerjoin, select 

from src.model import (FeeHeads, Sessions, StudentsDB, StudentSessions, ClassData, 
                       FeeStructure, FeeData)
from src import db

from datetime import date, datetime

from src.model.FeeSessionData import FeeSessionData
from src.model.FeeTransaction import FeeTransaction
from ..auth.login_required import login_required

get_fee_api_bp = Blueprint( 'get_fee_api_bp',   __name__)


@get_fee_api_bp.route('/api/get_fee', methods=["GET"])
@login_required
def get_fee_api():
    # data = request.json

    # student_id = data.get('student_id')
    # phone_number = data.get('phone_number')
    current_date = datetime.now().date()

    phone = request.args.get("phone")
    student_session_id = request.args.get("student_session_id")

    if not student_session_id:
        return jsonify({"message": "student_session_id is required"}), 400
    if not phone:
        phone = (
            db.session.query(StudentsDB.PHONE)
                .join(StudentSessions, StudentSessions.student_id == StudentsDB.id)
                .filter(StudentSessions.id == student_session_id)
                .scalar()
        )

    current_session = session["session_id"]
    school_id = session["school_id"]

    students = (
        db.session.query(
            StudentsDB.id.label("student_id"),
            StudentsDB.STUDENTS_NAME, StudentsDB.FATHERS_NAME,
            StudentsDB.PHONE, StudentsDB.IMAGE,
            StudentSessions.id.label("student_session_id"),
            StudentSessions.class_id, StudentSessions.session_id, 
            StudentSessions.ROLL, ClassData.CLASS
        )
        .join(StudentSessions, StudentsDB.id == StudentSessions.student_id)
        .join(ClassData, ClassData.id == StudentSessions.class_id)
        .filter(
            StudentsDB.PHONE == phone,
            StudentSessions.session_id == current_session,
        )
        .all()
    )

    
    class_ids = list({s.class_id for s in students})
    fee_structure = (
        db.session.query(
            FeeHeads.fee_type,
            FeeStructure.id.label("structure_id"),
            FeeStructure.period_name, FeeStructure.year_increment,
            FeeStructure.start_day, FeeStructure.start_month,
            
            FeeSessionData.amount, FeeSessionData.class_id,
            FeeSessionData.id.label("fee_session_id"), 
        )
        .outerjoin(FeeHeads, FeeStructure.fee_type_id == FeeHeads.id)
        .outerjoin(FeeSessionData, FeeSessionData.structure_id == FeeStructure.id)
        .filter(
            # FeeData.student_session_id.in_(student_session_ids),
            FeeSessionData.class_id.in_(class_ids),
            FeeStructure.school_id == school_id
        )
        .order_by(FeeStructure.sequence_number.asc())
        .all()
    )

    student_session_ids = list({s.student_session_id for s in students})
    fee_payments = (
        db.session.query(
            FeeData.fee_session_id,
            FeeData.student_session_id,
            FeeData.payment_status,
            FeeTransaction.paid_amount, 
            FeeTransaction.transaction_no,
            FeeTransaction.payment_date
        )
        .outerjoin(FeeTransaction, FeeTransaction.id == FeeData.transaction_id)
        .filter(FeeData.student_session_id.in_(student_session_ids))
        .all()
    )


    students_data = []
    for i, student in enumerate(students):
        students_data.append({
            "id": i,
            "student_session_id": student.student_session_id,  # keep this for mapping
            "name": student.STUDENTS_NAME,
            "class": student.CLASS,
            "class_id": student.class_id,
            "rollNo": student.ROLL,
            "image": f"https://lh3.googleusercontent.com/d/{student.IMAGE}=s50" if student.IMAGE else "",
            "monthlyFees": [],
            "otherFees": [],
            "selectedFees": []
        })

    payment_map = {}
    for fee in fee_payments:
        payment_map[(fee.student_session_id, fee.fee_session_id)] = {
            "status": fee.payment_status,
            "payment_date": fee.payment_date,
            "transaction_no": fee.transaction_no,
        }



    for student in students_data:
        i=0
        for f in fee_structure:
            # Only include fee items for the student's class
            if f.class_id != student["class_id"]:
                continue

            i+=1
            key = (student["student_session_id"], f.fee_session_id)
            payment = payment_map.get(key)

            # Determine year
            due_year = int(current_session) + (f.year_increment or 0)
            due_date = date(due_year, f.start_month, f.start_day)

            if payment:
                status = payment["status"]
                paid_date = payment["payment_date"]
                transaction_no = payment["transaction_no"]
            else:
                status = "due" if current_date > due_date else "upcoming"
                paid_date = None
                transaction_no = None

            fee_dict = {
                "id": i,
                "fee_id": f.fee_session_id,
                "fee_type": f.fee_type,
                "period_name": f.period_name,
                "amount": float(f.amount) if f.amount else 0,
                "dueDate": f"{f.start_day}-{f.start_month}-{due_year}",
                "status": status,
                "paid_date": paid_date.strftime("%d-%m-%Y") if paid_date else None,   # <-- UPDATED
                "transaction_no": transaction_no,
            }

            # append to right category
            if f.fee_type.lower() == "tuition fee":
                student["monthlyFees"].append(fee_dict)
            else:
                student["otherFees"].append(fee_dict)


    # time.sleep(10)
    # print(students_data)
    
    return jsonify(students_data)