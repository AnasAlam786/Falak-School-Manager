# src/controller/prv_year_students.py

from flask import render_template, session, request, Blueprint, jsonify
from sqlalchemy import select
from sqlalchemy.orm import aliased

from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

from bs4 import BeautifulSoup

from src import db

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

prv_year_student_api_bp = Blueprint( 'prv_year_student_api_bp',   __name__)



@prv_year_student_api_bp.route('/get_prv_year_students_api', methods=["POST"])
@login_required
@permission_required('promote_student')
def get_prv_year_students():
    data = request.json
    class_id = data.get('class_id')

    school_id = session["school_id"]
    current_session = session["session_id"]


    PromotedSession = aliased(StudentSessions)
    promoted_subq = (
        select(
            PromotedSession.student_id,
            PromotedSession.id.label("promoted_session_id"),
            PromotedSession.ROLL.label("next_roll"),
            PromotedSession.created_at.label("promoted_date")
        )
        .where(
            PromotedSession.session_id == current_session
        )
        .subquery()
    )


    # Main query with LEFT JOIN to promoted_subq
    data = db.session.query(
        StudentsDB.id,
        StudentsDB.STUDENTS_NAME,
        StudentsDB.ADMISSION_NO,
        StudentsDB.IMAGE,
        StudentsDB.GENDER,
        StudentsDB.FATHERS_NAME,
        StudentsDB.ADMISSION_DATE,
        ClassData.CLASS.label("previous_class"),
        StudentSessions.ROLL.label("previous_roll"),
        StudentSessions.class_id,

        promoted_subq.c.next_roll,
        promoted_subq.c.promoted_date,
        promoted_subq.c.promoted_session_id,

        # nested subquery to find next class using display_order
        select(ClassData.CLASS)
            .where(
                ClassData.display_order == (
                    select(ClassData.display_order)
                    .where(ClassData.id == class_id)
                    .scalar_subquery()
                ) + 1,
                ClassData.school_id == school_id
            )
            .scalar_subquery()
            .label("next_class")
    ).join(
        StudentSessions, 
        StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData, 
        StudentSessions.class_id == ClassData.id
    ).outerjoin(  # LEFT JOIN promoted details
        promoted_subq,
        promoted_subq.c.student_id == StudentsDB.id
    ).filter(
        ClassData.id == class_id,
        StudentsDB.school_id == school_id,
        StudentSessions.session_id == current_session - 1  # Previous session
    ).order_by(
        StudentSessions.ROLL
    ).all()

    if not data:
        return jsonify({
            "html": """
            <div class="alert alert-warning text-center" role="alert" style="margin-top: 50px;">
                <h5 class="mb-0">No Students Found</h5>
            </div>
            """
        })
    
    html = render_template('promote_student.html', data=data)
    soup=BeautifulSoup(html,"lxml")
    content=soup.body.find('div',{'id':'StudentData'}).decode_contents()

    return jsonify({"html":str(content)})
