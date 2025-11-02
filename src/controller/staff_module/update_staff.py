# src/controller/staff_module/update_staff.py

from flask import render_template, session, Blueprint, request, jsonify
from pydantic_core import ValidationError
from sqlalchemy import func

from src.controller.staff_module.utils.class_permission_validator import staff_specific_permission, validate_class, validate_permissions
from src.model import ClassData, Permissions, RolePermissions, StaffPermissions
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles

from src.controller.staff_module.utils.icons import permission_icons, ROLE_ICONS
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
    if not staff:
        return render_template('staff/update_staff.html', error="Staff not found")

    classes = (
        db.session.query(
            ClassData.id.label("id"),
            ClassData.CLASS,
            ClassAccess.id.label("access_id")   # It will be none if staff don't have access to that class
        )
        .outerjoin(
            ClassAccess, (ClassAccess.class_id == ClassData.id) & (ClassAccess.staff_id == staff_id)
        )
        .filter(ClassData.school_id == session.get('school_id'))
        .order_by(ClassData.display_order)
    ).all()

    selected_classes = [
        {"id": str(c.id), "name": c.CLASS}
        for c in classes if c.access_id
    ]


    # Get all the permissions staff have also accounting role permissions and exception staff permissions
    permissions_list = []
    permissions = (
        db.session.query(
            # Select permission details
            Permissions.description, Permissions.title,
            Permissions.id, Permissions.action,
            # RolePermissions.id will be None if the role doesn't have this permission
            RolePermissions.id.label("role_permission_id")
        )
        # Outer join to include all permissions,
        # even if not assigned to the current role
        .outerjoin(
            RolePermissions,
            (RolePermissions.permission_id == Permissions.id) &
            (RolePermissions.role_id == staff.role_id)
        )
        # Only include permissions that are marked as assignable
        .filter(Permissions.assignable.is_(True))
        .all()  # Fetch all results
    )

    
    staff_specific_permission = StaffPermissions.query.filter_by(staff_id=staff_id).all()
    staff_specific_permission_map = {p.permission_id: p.is_granted for p in staff_specific_permission}

    for permission in permissions:
        role_has_permission = permission.role_permission_id is not None
        staff_override = staff_specific_permission_map.get(permission.id)

            # Determine final access
        if staff_override is not None:
            is_granted = staff_override  # Explicit staff override
        else:
            is_granted = role_has_permission  # Default from role

        permissions_list.append({
            "id": permission.id,
            "title": permission.title,
            "description": permission.description,
            "action": permission.action,
            "icon": permission_icons.get(permission.title, "fa-cog"),  # default fallback icon
            "selected": is_granted,
            "role_permission_id": permission.role_permission_id,
            
        })
    
    roles = (
        db.session.query(
            Roles.id,
            Roles.role_name,
        )
        .filter(Roles.assignable == True)
        .order_by(Roles.display_order.asc())
        .all()
    )
    password = hash_password.decrypt_password(staff.Password)

    return render_template(
        'staff/update_staff.html',
        staff=staff, roles=roles,
        password=password,
        ROLE_ICONS=ROLE_ICONS,
        permissions_list=permissions_list,
        classes=classes,
        selected_classes=selected_classes
    )


