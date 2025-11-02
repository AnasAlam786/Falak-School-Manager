# src/controller/staff_module/add_staff.py

from collections import Counter
from flask import jsonify, render_template, session, Blueprint, request
from sqlalchemy import distinct, func, select


from src.model import Permissions, RolePermissions
from src.model.Roles import Roles
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src import db
from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required
from src.model.Roles import Roles

from src.controller.staff_module.utils.icons import permission_icons, ROLE_ICONS


add_staff_bp = Blueprint( 'add_staff_bp',   __name__)

#add the aadhar of aarish in database after taking from udise

@add_staff_bp.route('/add_staff', methods=['GET'])
@login_required
@permission_required('add_staff')
def add_staff():

    user_id = session["user_id"]

    classes = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    ).all()


    roles = (
        db.session.query(Roles.id, Roles.role_name).filter(Roles.assignable == True)
        .order_by(Roles.display_order.asc())
    ).all()

    permissions = (
        db.session.query(
            Permissions.description,
            Permissions.title,
            Permissions.id,
            Permissions.action
        )
        .filter(Permissions.assignable.is_(True))
        .all()
    )

    permissions_list = [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "action": p.action,
            "icon": permission_icons.get(p.title, "fa-cog"),  # default fallback icon
            "selected": False,
        }
        for p in permissions
    ]


    
    return render_template(
        'staff/add_staff.html',
        roles=roles,
        ROLE_ICONS=ROLE_ICONS,
        classes=classes,
        permissions_list=permissions_list
    )

