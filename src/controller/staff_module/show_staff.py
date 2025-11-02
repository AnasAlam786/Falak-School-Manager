# src/controller/staff_module/show_staff.py

from collections import Counter
from flask import render_template, session, Blueprint
from sqlalchemy import distinct, func

from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src import db
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required


show_staff_bp = Blueprint( 'show_staff_bp',   __name__)

#add the aadhar of aarish in database after taking from udise

@show_staff_bp.route('/show_staff', methods=['GET'])
@login_required
@permission_required('show_staff')
def show_staff():
    school_id = session['school_id']

    # --- teachers data (role + accessible classes + total accessible count per teacher)
    teachers_query = (
        db.session.query(
            TeachersLogin,
            Roles.role_name.label("role_name"),
            func.array_remove(func.array_agg(distinct(ClassData.CLASS)), None)
                .label("accessible_classes"),
            func.count(distinct(ClassData.id)).label("total_accessible_classes")
        )
        .join(Roles, TeachersLogin.role_id == Roles.id)
        .outerjoin(ClassAccess, TeachersLogin.id == ClassAccess.staff_id)
        .outerjoin(ClassData, ClassAccess.class_id == ClassData.id)
        .filter(TeachersLogin.school_id == school_id)
        .group_by(TeachersLogin.id, Roles.role_name)
        .order_by(TeachersLogin.role_id)  # sort by role id
    )
    teachers = teachers_query.all()

    # --- total classes in school (independent of access)
    total_classes = (
        db.session.query(func.count(ClassData.id))
        .filter(ClassData.school_id == school_id)
        .scalar()
    )

    # --- role buckets (count in Python)
    # Unpack once cleanly
    role_names = [role_name for (_teacher, role_name, _classes, _n) in teachers]
    counts = Counter(role_names)

    admin_roles = {"Manager", "Principal", "Vice Principal", "Admin"}

    teachers_count = counts.get("Teacher", 0)
    administrator_count = sum(counts.get(r, 0) for r in admin_roles)
    helper_staff_count = len(teachers) - teachers_count - administrator_count

    total_staff = len(teachers)
    sample_male_image = 'https://static.vecteezy.com/system/resources/previews/024/183/538/non_2x/male-avatar-portrait-of-a-business-man-in-a-suit-illustration-of-male-character-in-modern-color-style-vector.jpg'
    sample_female_image = 'https://static.vecteezy.com/system/resources/previews/025/030/083/non_2x/businesswoman-portrait-beautiful-woman-in-business-suit-employee-of-business-institution-in-uniform-lady-office-worker-woman-business-avatar-profile-picture-illustration-vector.jpg'

    return render_template(
        'staff/show_staff.html',
        teachers=teachers,
        total_staff=total_staff,
        total_classes=total_classes,
        helper_staff_count=helper_staff_count,
        administrator_count=administrator_count,
        teachers_count=teachers_count,
        sample_male_image=sample_male_image,
        sample_female_image=sample_female_image
    )
