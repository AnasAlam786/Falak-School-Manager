from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from sqlalchemy import or_
from pydantic import BaseModel, EmailStr, Field, ValidationError
from typing import Optional, List
from datetime import datetime
import os

from src import db
from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles
from src.model.ClassData import ClassData
from src.model.RolePermissions import RolePermissions
from src.model.Permissions import Permissions

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

from cryptography.fernet import Fernet


staff_bp = Blueprint('staff_bp', __name__)


FERNET_KEY = os.environ.get('FERNET_KEY')


class StaffCreateModel(BaseModel):
    Name: str = Field(..., min_length=2)
    Email: EmailStr
    Password: str = Field(..., min_length=6)
    Role: int
    School: str
    Classes: List[int] = Field(default_factory=list)
    Status: str = Field(...)
    ProfileImage: Optional[str] = None
    Signature: Optional[str] = None


class StaffUpdateModel(BaseModel):
    Name: Optional[str] = Field(None, min_length=2)
    Email: Optional[EmailStr] = None
    Password: Optional[str] = Field(None, min_length=6)
    Role: Optional[int] = None
    Classes: Optional[List[int]] = None
    Status: Optional[str] = None
    ProfileImage: Optional[str] = None
    Signature: Optional[str] = None


def _hash_password(raw_password: str) -> bytes:
    cipher = Fernet(FERNET_KEY)
    return cipher.encrypt(raw_password.encode())


def _teacher_to_dict(t: TeachersLogin) -> dict:
    return {
        'id': t.id,
        'name': t.Name,
        'email': t.email,
        'role': t.role_data.role_name if t.role_data else None,
        'role_id': t.role_id,
        'status': t.status,
        'avatar_url': 'https://placehold.co/96x96?text=User',
        'classes': [
            {'id': ca.class_id, 'label': f"{ca.class_data.CLASS}{('-' + ca.class_data.Section) if ca.class_data and ca.class_data.Section else ''}"}
            for ca in (t.class_access or []) if ca.class_data
        ]
    }


@staff_bp.route('/staff', methods=['GET'])
@login_required
@permission_required('staff_view')
def staff_list():
    from src.model.ClassAccess import ClassAccess
    query = TeachersLogin.query.join(Roles, Roles.id == TeachersLogin.role_id)

    search = request.args.get('q')
    role = request.args.get('role')
    status = request.args.get('status')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    class_id = request.args.get('class_id')

    if search:
        like = f"%{search}%"
        query = query.filter(or_(TeachersLogin.Name.ilike(like), TeachersLogin.email.ilike(like)))

    if role:
        query = query.filter(TeachersLogin.role_id == role)

    if status:
        query = query.filter(TeachersLogin.status == status)

    if class_id:
        query = query.join(ClassAccess, ClassAccess.staff_id == TeachersLogin.id)
        query = query.filter(ClassAccess.class_id == str(class_id))

    pagination = query.order_by(TeachersLogin.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    roles = Roles.query.all()
    classes = ClassData.query.filter_by(school_id=session.get('school_id')).all()

    # initial page render vs ajax infinite scroll
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        items = [_teacher_to_dict(t) for t in pagination.items]
        return jsonify({
            'items': items,
            'has_next': pagination.has_next
        })

    return render_template('staff/list.html', staff=pagination.items, roles=roles, classes=classes, has_next=pagination.has_next)






@staff_bp.route('/staff/add', methods=['GET', 'POST'])
@login_required
@permission_required('staff_add')
def add_staff():
    if request.method == 'GET':
        roles = Roles.query.all()
        classes = ClassData.query.filter_by(school_id=session.get('school_id')).all()
        return render_template('staff/add_edit.html', roles=roles, classes=classes, mode='add', staff=None)

    data = request.form.to_dict() if request.form else request.get_json(silent=True) or {}
    try:
        model = StaffCreateModel(**{
            'Name': data.get('Name'),
            'Email': data.get('Email'),
            'Password': data.get('Password'),
            'Role': int(data.get('Role')) if data.get('Role') else None,
            'School': session.get('school_id'),
            'Classes': [],
            'Status': data.get('Status'),
            'ProfileImage': data.get('ProfileImage'),
            'Signature': data.get('Signature'),
        })
    except ValidationError as e:
        return jsonify({'message': e.errors()[0]['msg']}), 400

    if TeachersLogin.query.filter_by(email=model.Email).first():
        return jsonify({'message': 'Email already exists'}), 400

    teacher = TeachersLogin(
        Name=model.Name,
        email=str(model.Email),
        Password=_hash_password(model.Password),
        IP=None,
        Sign=None,
        User=model.Name,
        status=model.Status,
        school_id=model.School,
        role_id=model.Role,
    )
    db.session.add(teacher)
    db.session.commit()

    # assign class access
    if model.Classes:
        from src.model.ClassAccess import ClassAccess
        for class_id in model.Classes:
            db.session.add(ClassAccess(
                granted_at=datetime.utcnow().date(),
                access_role=None,
                class_id=str(class_id),
                staff_id=str(teacher.id)
            ))
        db.session.commit()

    return jsonify({'message': 'Staff added successfully', 'id': teacher.id}), 200


@staff_bp.route('/staff/<int:staff_id>', methods=['GET'])
@login_required
@permission_required('staff_view')
def staff_profile(staff_id: int):
    t = TeachersLogin.query.get_or_404(staff_id)
    # permissions summary for this teacher via role
    perms = (
        db.session.query(Permissions)
        .join(RolePermissions, RolePermissions.permission_id == Permissions.id)
        .filter(RolePermissions.role_id == t.role_id)
        .all()
    )
    return render_template('staff/profile.html', t=t, permissions=perms)


@staff_bp.route('/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@permission_required('staff_edit')
def edit_staff(staff_id: int):
    t = TeachersLogin.query.get_or_404(staff_id)
    if request.method == 'GET':
        roles = Roles.query.all()
        classes = ClassData.query.filter_by(school_id=session.get('school_id')).all()
        return render_template('staff/add_edit.html', roles=roles, classes=classes, mode='edit', staff=t)

    data = request.form.to_dict() if request.form else request.get_json(silent=True) or {}

    try:
        model = StaffUpdateModel(**{
            'Name': data.get('Name'),
            'Email': data.get('Email'),
            'Password': data.get('Password'),
            'Role': int(data.get('Role')) if data.get('Role') else None,
            'Classes': [int(x) for x in (data.get('Classes') or [])] if isinstance(data.get('Classes'), list) else None,
            'Status': data.get('Status'),
            'ProfileImage': data.get('ProfileImage'),
            'Signature': data.get('Signature'),
        })
    except ValidationError as e:
        return jsonify({'message': e.errors()[0]['msg']}), 400

    if model.Email and (model.Email != t.email) and TeachersLogin.query.filter_by(email=model.Email).first():
        return jsonify({'message': 'Email already exists'}), 400

    if model.Name: t.Name = model.Name
    if model.Email: t.email = str(model.Email)
    if model.Password: t.Password = _hash_password(model.Password)
    if model.Role is not None: t.role_id = model.Role
    if model.Status: t.status = model.Status
    # store signature in Sign field (url or base64 until you wire storage)
    if model.Signature is not None: t.Sign = model.Signature

    db.session.commit()

    # classes will be managed from Access page now
    return jsonify({'message': 'Staff updated successfully'}), 200


@staff_bp.route('/staff/access/<int:staff_id>', methods=['GET'])
@login_required
@permission_required('staff_access')
def staff_access(staff_id: int):
    t = TeachersLogin.query.get_or_404(staff_id)
    all_perms = Permissions.query.order_by(Permissions.title.asc()).all()
    role_perm_ids = set(
        p.permission_id for p in RolePermissions.query.filter_by(role_id=t.role_id).all()
    )
    classes = ClassData.query.filter_by(school_id=session.get('school_id')).all()
    current_class_ids = {ca.class_id for ca in (t.class_access or [])}
    return render_template('staff/access.html', t=t, permissions=all_perms, granted_ids=role_perm_ids, classes=classes, current_class_ids=current_class_ids)


@staff_bp.route('/staff/access/<int:staff_id>/toggle', methods=['POST'])
@login_required
@permission_required('staff_access')
def staff_access_toggle(staff_id: int):
    t = TeachersLogin.query.get_or_404(staff_id)
    data = request.get_json() or {}
    permission_id = int(data.get('permission_id'))
    grant = bool(data.get('grant'))

    link = RolePermissions.query.filter_by(role_id=t.role_id, permission_id=permission_id).first()
    if grant and not link:
        link = RolePermissions(role_id=t.role_id, permission_id=permission_id, granted_at=datetime.utcnow().date())
        db.session.add(link)
    elif not grant and link:
        db.session.delete(link)
    db.session.commit()
    return jsonify({'message': 'Updated'}), 200


@staff_bp.route('/staff/access/<int:staff_id>/apply_role_defaults', methods=['POST'])
@login_required
@permission_required('staff_access')
def apply_role_defaults(staff_id: int):
    t = TeachersLogin.query.get_or_404(staff_id)
    # In this simplified version, role defaults are already represented by RolePermissions on the role
    # So we just echo success; a future enhancement could copy from a Role template
    return jsonify({'message': 'Role default permissions are active for this teacher via role assignment.'}), 200


@staff_bp.route('/staff/access/<int:staff_id>/classes', methods=['POST'])
@login_required
@permission_required('staff_access')
def staff_access_classes(staff_id: int):
    t = TeachersLogin.query.get_or_404(staff_id)
    from src.model.ClassAccess import ClassAccess
    data = request.get_json() or {}
    class_ids = data.get('class_ids') or []
    ClassAccess.query.filter_by(staff_id=str(t.id)).delete()
    for cid in class_ids:
        db.session.add(ClassAccess(
            granted_at=datetime.utcnow().date(),
            access_role=None,
            class_id=str(cid),
            staff_id=str(t.id)
        ))
    db.session.commit()
    return jsonify({'message': 'Class access updated'}), 200


@staff_bp.route('/staff/deactivate/<int:staff_id>', methods=['POST'])
@login_required
@permission_required('staff_deactivate')
def deactivate_staff(staff_id: int):
    t = TeachersLogin.query.get_or_404(staff_id)
    t.status = 'Inactive'
    # Remove class access entries
    # Assuming ClassAccess links staff to classes, clear them
    from src.model.ClassAccess import ClassAccess
    ClassAccess.query.filter_by(staff_id=str(t.id)).delete()
    db.session.commit()
    return jsonify({'message': 'Staff deactivated and access removed'}), 200


