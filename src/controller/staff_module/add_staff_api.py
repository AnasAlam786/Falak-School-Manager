# src/controller/staff_module/add_staff.py

from collections import Counter
import datetime
from flask import jsonify, render_template, session, Blueprint, request
from pydantic import ValidationError
from sqlalchemy import distinct, func


from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src.controller.staff_module.utils import hash_password
from src.controller.staff_module.utils.pydantic_verification import StaffVerification

from src import db
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

add_staff_api_bp = Blueprint( 'add_staff_api_bp',   __name__)

@add_staff_api_bp.route('/api/add_staff', methods=['POST'])
@login_required
@permission_required('add_staff')
def add_staff():

    data = request.get_json(silent=True) or (request.form.to_dict() if request.form else {})

    # Normalize gender to match Pydantic Literal and DB Enum
    gender = data.get('gender')
    if isinstance(gender, str):
        gender_norm = gender.strip().title()  # male -> Male
        if gender_norm not in {"Male", "Female"}:
            gender_norm = None
    else:
        gender_norm = None


    # Resolve role_id: accept numeric id or map from role_name/value label
    role_id_raw = data.get('role_id')
    resolved_role_id = None
    if isinstance(role_id_raw, (int,)):
        resolved_role_id = role_id_raw
    elif isinstance(role_id_raw, str) and role_id_raw.isdigit():
        resolved_role_id = int(role_id_raw)
    else:
        # Try to map by role_name from payload label or value
        role_name = (data.get('role_name') or str(role_id_raw or '')).strip()
        if role_name:
            role = Roles.query.filter(func.lower(Roles.role_name) == role_name.lower()).first()
            if role:
                resolved_role_id = int(role.id)
            else:
                return jsonify({'message': 'Invalid role'}), 400
        else:
            return jsonify({'message': 'Role name is required'}), 400

    try:
        model = StaffVerification(**{
            'name': data.get('name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'dob': data.get('dob'),
            'gender': gender_norm,
            'address': data.get('address') or None,
            'username': data.get('username'),
            'password': data.get('password'),
            'date_of_joining': data.get('date_of_joining'),
            'qualification': data.get('qualification') or None,
            'salary': data.get('salary') or None,
            'role_id': resolved_role_id,
            'image': data.get('image') or None,
            'sign': data.get('sign') or None,
        })
    except Exception as e:
        return jsonify({'message': str(e)}), 400

    # Email unique check
    if model.email and TeachersLogin.query.filter_by(email=str(model.email)).first():
        return jsonify({'message': f'Email ({model.email}) already exists'}), 400

    # Build DB entity
    try:
        teacher = TeachersLogin(
            Name=model.name,
            email=str(model.email) if model.email else None,
            Password=hash_password.encrypt_password(model.password),
            IP=None,
            Sign=model.sign,
            User=model.username,
            status='active',
            school_id=session.get('school_id'),
            role_id=model.role_id,
            image=model.image,
            qualification=model.qualification,
            dob=model.dob,
            phone=int(model.phone) if model.phone else None,
            date_of_joining=model.date_of_joining,
            address=model.address,
            gender=model.gender,
        )
        db.session.add(teacher)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error occurred while adding staff', 'error': str(e)}), 500

    return jsonify({'message': 'Staff added successfully', 'id': teacher.id}), 200