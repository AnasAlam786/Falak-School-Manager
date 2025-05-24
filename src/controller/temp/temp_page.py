# src/controller/temp/temp_page.py

from flask import render_template, session, Blueprint
from sqlalchemy import select, func


from src.model.StudentsDB import StudentsDB
from src.model.ClassData import ClassData
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess

from src import db

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required



temp_page_bp = Blueprint( 'temp_page_bp',   __name__)

@temp_page_bp.route('/temp_page', methods=["POST","GET"])
@login_required
@permission_required('admission')
def temp_page():

    
    school_id = session["school_id"]
    user_id = session["user_id"]

    classes_query = (
        db.session.query(ClassData)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .filter(ClassAccess.staff_id == user_id)
        .order_by(ClassData.id.asc())
    )

    classes = classes_query.all()

    classes = {str(cls.id): cls.CLASS for cls in classes}


    # Correlated subquery with explicit correlation
    max_session_subq = (
        select(func.max(StudentSessions.id))
        .where(StudentSessions.student_id == StudentsDB.id)
        .correlate(StudentsDB)  # Explicitly correlate with StudentsDB
        .scalar_subquery()
    )

    data = db.session.query(
        StudentsDB.id,
        StudentsDB.STUDENTS_NAME,
        StudentsDB.FATHERS_NAME,
        StudentsDB.IMAGE,
        StudentsDB.ADMISSION_NO,
        StudentsDB.SR,
        StudentsDB.ADMISSION_DATE,
        StudentsDB.Admission_Class,
        StudentSessions.ROLL,
        ClassData.CLASS,
    ).outerjoin(
        StudentSessions,
        db.and_(
            StudentSessions.student_id == StudentsDB.id,
            StudentSessions.id == max_session_subq  # Match the max session ID
        )
    ).outerjoin(
        ClassData, StudentSessions.class_id == ClassData.id
    ).filter(
        StudentsDB.school_id == school_id,
        db.or_(
            StudentsDB.Admission_Class == None,
            StudentsDB.ADMISSION_DATE == None,
            StudentsDB.SR == None
        )
    ).order_by(
        StudentsDB.ADMISSION_NO.asc()
    ).all()




    return render_template('temp_update_colum.html',data=data, classes=classes)
      
