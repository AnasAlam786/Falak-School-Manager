# src/controller/staff_module/update_staff.py

from flask import render_template, session, Blueprint, request, jsonify
from sqlalchemy import func

from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles

from src.controller.staff_module.utils import hash_password
from src.controller.staff_module.utils.pydantic_verification import StaffVerification

from src import db
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required


update_staff_bp = Blueprint( 'update_staff_bp',   __name__)

@update_staff_bp.route('/update_staff', methods=['GET'])
@permission_required('update_staff')
@login_required
def update_staff():
    # Get staff ID from query parameter
    staff_id = request.args.get('id')
    
    if not staff_id:
        return render_template('staff/update_staff.html', error="Staff ID is required")
    
    try:
        staff_id = int(staff_id)
    except ValueError:
        return render_template('staff/update_staff.html', error="Invalid Staff ID")
    
    # Get staff data
    staff = TeachersLogin.query.filter_by(id=staff_id, school_id=session.get('school_id')).first()

    # Print all attributes of the staff object
    print("Staff attributes:")
    for column in staff.__table__.columns:
        print(f"{column.name}: {getattr(staff, column.name)}")    
    if not staff:
        return render_template('staff/update_staff.html', error="Staff not found")
    
    # Get all roles for the form
    roles = Roles.query.all()
    password = hash_password.decrypt_password(staff.Password)

    sample_male_image = 'https://static.vecteezy.com/system/resources/previews/024/183/538/non_2x/male-avatar-portrait-of-a-business-man-in-a-suit-illustration-of-male-character-in-modern-color-style-vector.jpg'
    sample_female_image = 'https://static.vecteezy.com/system/resources/previews/025/030/083/non_2x/businesswoman-portrait-beautiful-woman-in-business-suit-employee-of-business-institution-in-uniform-lady-office-worker-woman-business-avatar-profile-picture-illustration-vector.jpg'

    
    return render_template(
        'staff/update_staff.html',
        staff=staff, roles=roles,
        sample_female_image=sample_female_image,
        sample_male_image=sample_male_image,
        password=password

    )

@update_staff_bp.route('/api/update_staff', methods=['POST'])
@login_required
@permission_required('update_staff')
def update_staff_api():
    data = request.get_json(silent=True) or (request.form.to_dict() if request.form else {})
    
    staff_id = data.get('staff_id')
    if not staff_id:
        return jsonify({'message': 'Staff ID is required'}), 400
    
    try:
        staff_id = int(staff_id)
    except ValueError:
        return jsonify({'message': 'Invalid Staff ID'}), 400
    
    # Get existing staff
    staff = TeachersLogin.query.filter_by(id=staff_id, school_id=session.get('school_id')).first()
    if not staff:
        return jsonify({'message': 'Staff not found'}), 404
    
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

    # Email unique check (exclude current staff)
    if model.email and model.email != staff.email:
        existing_staff = TeachersLogin.query.filter_by(email=str(model.email)).first()
        if existing_staff and existing_staff.id != staff_id:
            return jsonify({'message': f'Email ({model.email}) already exists'}), 400

    # Update staff data
    try:
        staff.Name = model.name
        staff.email = str(model.email) if model.email else None
        staff.User = model.username
        staff.qualification = model.qualification
        staff.dob = model.dob
        staff.phone = int(model.phone) if model.phone else None
        staff.date_of_joining = model.date_of_joining
        staff.address = model.address
        staff.gender = model.gender
        staff.role_id = model.role_id
        
        # Update password only if provided
        if model.password:
            staff.Password = hash_password.encrypt_password(model.password)
        
        # Update image and signature if provided
        if model.image:
            staff.image = model.image
        if model.sign:
            staff.Sign = model.sign
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error occurred while updating staff', 'error': str(e)}), 500

    return jsonify({'message': 'Staff updated successfully', 'id': staff.id}), 200