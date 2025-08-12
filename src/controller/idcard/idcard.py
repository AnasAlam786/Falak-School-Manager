# src/controller/idcard/idcard.py

from flask import render_template, session, Blueprint
from sqlalchemy import func

from src.model import Schools, TeachersLogin
from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src import db
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required



idcard_bp = Blueprint( 'idcard_bp',   __name__)

#add the aadhar of aarish in database after taking from udise

@idcard_bp.route('/idcard', methods=['GET'])
@login_required
def student_list():

    school_id = session['school_id']
    current_session = 2
    user_id = session["user_id"]

    print(current_session)

    # build your query
    students = db.session.query(
        StudentsDB.id,
        StudentsDB.STUDENTS_NAME,
        func.to_char(StudentsDB.DOB, 'Dy, DD Month YYYY').label('dob'),
        StudentsDB.FATHERS_NAME,
        StudentsDB.IMAGE,
        StudentsDB.PHONE,
        StudentsDB.ADDRESS,
        StudentSessions.ROLL,
        ClassData.CLASS,
        ClassData.Section,
        TeachersLogin.Sign.label('teachers_sign')
        
    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData,    StudentSessions.class_id == ClassData.id
    ).join(
        TeachersLogin,    ClassData.class_teacher_id == TeachersLogin.id
    ).filter(
        StudentsDB.school_id    == school_id,
        StudentSessions.session_id == current_session,
        # StudentSessions.class_id == 6,
        StudentsDB.IMAGE.isnot(None)
    ).order_by(
        ClassData.id.asc(),
        ClassData.Section.asc(),
        StudentSessions.ROLL.asc()
    ).all()


    school = db.session.query(
        func.upper(Schools.School_Name).label('School_Name'),
        Schools.Address,
        Schools.Phone,
        Schools.Logo,
        Schools.UDISE
    ).filter(
        Schools.id == school_id
    ).first()
        




    return render_template('/pdf-components/icards/hanging_image_icard.html',
                           students=students, school = school)