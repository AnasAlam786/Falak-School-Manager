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
@permission_required('idcard')
def idcards_page():

    school_id = session['school_id']
    current_session = session["session_id"]
    user_id = session["user_id"]

    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()
    class_ids = [cls.id for cls in classes]

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
        StudentSessions.class_id,
        ClassData.CLASS,
        ClassData.Section,
        TeachersLogin.Sign.label('teachers_sign')
        
    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData,    StudentSessions.class_id == ClassData.id
    ).outerjoin(
        TeachersLogin,    ClassData.class_teacher_id == TeachersLogin.id
    ).filter(
        StudentsDB.school_id    == school_id,
        StudentSessions.session_id == current_session,
        # ClassData.id == 11
        ClassData.id.in_(class_ids),
        #StudentsDB.IMAGE.isnot(None)
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

    principal_sign = db.session.query( TeachersLogin.Sign
        ).filter(
            TeachersLogin.school_id == school_id,
            TeachersLogin.role_id == 2  #2 role_id is for principal in database
        ).scalar()

    # for student in students:
    #     print({
    #         "id": student.id,
    #         "name": student.STUDENTS_NAME,
    #         "dob": student.dob,
    #         "father": student.FATHERS_NAME,
    #         "image": student.IMAGE,
    #         "phone": student.PHONE,
    #         "address": student.ADDRESS,
    #         "roll": student.ROLL,
    #         "class": student.CLASS,
    #         "section": student.Section,
    #         "teacher_sign": student.teachers_sign
    #     })
    #     print("")


        

    # '/pdf-components/icards/hanging_image_icard.html'

    session_logo = 'https://lh3.googleusercontent.com/d/1tJnm5i4GgSyb4HIULAb2tvbejXfrz5HZ=s200'

    return render_template('/idcard.html',
                           students=students, school = school, classes=classes, session_logo = session_logo, principal_sign = principal_sign)

