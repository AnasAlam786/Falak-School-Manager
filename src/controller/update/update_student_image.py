# src/controller/update/update_student_image.py


from flask import render_template, session, Blueprint
from sqlalchemy import func

from src.model.StudentsDB import StudentsDB
from src.model.ClassData import ClassData
from src.model.StudentsDB import StudentsDB
from src.model.ClassAccess import ClassAccess

from src import db

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required
from datetime import datetime

update_student_image_bp = Blueprint( 'update_student_image_bp',   __name__)

@update_student_image_bp.route('/update_student_image', methods=["GET", "POST"])
@login_required
@permission_required('admission')
def update_student_image():

    user_id = session["user_id"]
    school_id = session["school_id"]

    student_id = req