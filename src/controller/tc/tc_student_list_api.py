# src/controller/tc_student_list_api.py

from flask import render_template, session, request, Blueprint, jsonify
from sqlalchemy import func

from src.model import StudentsDB
from src.model import ClassData
from src.model import StudentSessions

from src import db

from bs4 import BeautifulSoup
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

tc_student_list_api_bp = Blueprint( 'tc_student_list_api_bp',   __name__)

@tc_student_list_api_bp.route('/tc_student_list_api', methods=['POST', 'GET'])
@login_required
@permission_required('tc')
def tc_student_list_api():
    
    if "email" not in session:
        return jsonify({"message": "You are not authorised to access this API. Login required!"})


    data = request.json

    CLASS = data.get('class')
    school_id = session["school_id"]
    current_session_id = session["session_id"]


    data = db.session.query(
                            StudentsDB.STUDENTS_NAME, StudentsDB.id, StudentsDB.ADMISSION_DATE,
                            StudentsDB.FATHERS_NAME, StudentsDB.IMAGE, StudentsDB.ADMISSION_NO,
                            StudentsDB.Admission_Class, StudentsDB.SR,

                            ClassData.CLASS, 
                            StudentSessions.ROLL,
                            func.to_char(StudentsDB.DOB, 'Day, DD Month YYYY').label('DOB'),
                        ).join(
                            StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                        ).join(
                            ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                        ).filter(
                            StudentSessions.class_id == CLASS,
                            StudentsDB.school_id == school_id,
                            StudentSessions.session_id == current_session_id
                        ).order_by(
                            StudentSessions.ROLL
                        ).all()

    html = render_template('tc.html', data=data)
    soup=BeautifulSoup(html,"lxml")
    content=soup.body.find('div',{'id':'StudentData'}).decode_contents()

    return jsonify({"html":str(content)})
        