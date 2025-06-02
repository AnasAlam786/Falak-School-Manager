# src/controller/tc.py

from flask import render_template, session, Blueprint

from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin
from src import db

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

tc_bp = Blueprint( 'tc_bp',   __name__)

@tc_bp.route('/tc', methods=['GET'])
@login_required
@permission_required('tc')
def tc():
    
    user_id = session["user_id"]

    classes = (
        db.session.query(ClassData.id, ClassData.CLASS)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .join(TeachersLogin, TeachersLogin.id == ClassAccess.staff_id)
        .filter(TeachersLogin.id == user_id)
        .order_by(ClassData.id.asc())
        .all()
    )

    return render_template('tc.html', classes=classes)
