# src/controller/promote_student.py

from collections import defaultdict
import csv
from flask import render_template, session, url_for, redirect, Blueprint
from sqlalchemy import extract, func

from src.model import StudentSessions, StudentsDB
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin
from src import db

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required


promote_student_bp = Blueprint( 'promote_student_bp',   __name__)


@promote_student_bp.route('/promote_student', methods=["GET", "POST"])
@login_required
@permission_required('promote_student')
def promoteStudent():

    min_session_subq = (
        db.session.query(
            StudentSessions.student_id,
            func.min(StudentSessions.session_id).label("min_session_id")
        )
        .group_by(StudentSessions.student_id)
        .subquery()
    )


    students = (
        db.session.query(
            extract('year', StudentsDB.ADMISSION_DATE).label("admission_year"),

            StudentsDB.STUDENTS_NAME,
            StudentsDB.SR,
            StudentsDB.ADMISSION_DATE,
            StudentsDB.DOB,
            StudentsDB.ADMISSION_NO,
            StudentsDB.AADHAAR,
            StudentsDB.FATHERS_NAME,
            StudentsDB.MOTHERS_NAME,
            StudentsDB.Caste_Type,
            ClassData.CLASS.label("admission_class"),
            StudentsDB.ADDRESS,

        )
        .join(min_session_subq, min_session_subq.c.student_id == StudentsDB.id)
        .join(
            StudentSessions,
            (StudentSessions.student_id == min_session_subq.c.student_id) &
            (StudentSessions.session_id == min_session_subq.c.min_session_id)
        )
        .join(ClassData, ClassData.id == StudentsDB.Admission_Class)
        .filter(StudentsDB.school_id == 'falak')
        .order_by(
            "admission_year",
            StudentsDB.SR
        )
        .all()
    )

    # --- group students by year in Python ---
    grouped_students = defaultdict(list)
    for s in students:
        year = s.admission_year  # already labeled in query
        grouped_students[year].append(s)


    csv_file_path = 'students_report.csv'


    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write header
        
        # Write data rows
        for year, same_year_students in grouped_students.items():
            writer.writerow(['STUDENTS_NAME', 'DOB', 'ADMISSION_DATE', 'ADMISSION_NO', 'SR', 'AADHAAR','FATHERS_NAME', 'MOTHERS_NAME', 'Caste_Type', "Admission Class", "ADDRESS"])

            for student in same_year_students:
                writer.writerow([
                    student.STUDENTS_NAME,
                    student.DOB.strftime('%Y-%m-%d') if student.DOB else '',
                    student.ADMISSION_DATE.strftime('%Y-%m-%d') if student.ADMISSION_DATE else '',
                    student.ADMISSION_NO,
                    student.SR,
                    str(student.AADHAAR),
                    student.FATHERS_NAME,
                    student.MOTHERS_NAME,
                    student.Caste_Type,
                    student.admission_class,
                    student.ADDRESS
                ])

            writer.writerow([])


    user_id = session["user_id"]

    classes = (
        db.session.query(ClassData.id, ClassData.CLASS)
        .join(ClassAccess, ClassAccess.class_id == ClassData.id)
        .join(TeachersLogin, TeachersLogin.id == ClassAccess.staff_id)
        .filter(TeachersLogin.id == user_id)
        .order_by(ClassData.id.asc())
        .all()
    )
    return render_template('promote_student.html', classes=classes)# src/controller/student_list.py

