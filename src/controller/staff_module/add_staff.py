# src/controller/staff_module/add_staff.py

from collections import Counter
from flask import render_template, session, Blueprint, request
from sqlalchemy import distinct, func, select


from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src import db
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required
from src.model.Roles import Roles


add_staff_bp = Blueprint( 'add_staff_bp',   __name__)

#add the aadhar of aarish in database after taking from udise

@add_staff_bp.route('/add_staff', methods=['GET'])
@permission_required('add_staff')
@login_required
def add_staff():

    school_id = session['school_id']
    user_id = session["user_id"]


    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()


    roles_list = ["Teacher", "Support Staff", "Vice Principal", "Vice Principal"]
    roles = db.session.query(Roles.id, Roles.role_name).filter(Roles.role_name.in_(roles_list)).all()
    roles_dict = {role.role_name: role.id for role in roles}
    
    return render_template(
        'staff/add_staff.html',
        roles=roles_dict
    )