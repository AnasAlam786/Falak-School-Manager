# src/controller/get_result_api.py

from flask import session, request, jsonify, Blueprint, render_template 
from sqlalchemy import func

from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src.model.TeachersLogin import TeachersLogin
from src import db

from .utils.calc_grades import get_grade
from .utils.marks_processing import result_data
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

get_result_api_bp = Blueprint('get_result_api_bp',   __name__)


@get_result_api_bp.route('/get_result_api', methods=["POST"])
@login_required
@permission_required('get_result')
def get_result_api():
    if "email" not in session:
        return jsonify({"message": "Unauthorized access. Login required"}), 401
    

    current_session_id = session["session_id"]
    user_id = session["user_id"]

    try:
        student_id = int(request.json.get("id"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid student ID."}), 400

    # Session checks
    if not student_id or not current_session_id or not user_id:
        return jsonify({"message": "Session data missing. Please logout and login again!"}), 403

    # Authorization: find student's class
    student_session = db.session.query(StudentSessions).filter_by(
        student_id=student_id,
        session_id=current_session_id
    ).first()
    if not student_session:
        return jsonify({"message": "Student not found in current session."}), 404

    class_id = student_session.class_id
    allowed = (
        db.session.query(ClassAccess.class_id)
        .filter(ClassAccess.staff_id == user_id)
        .all()
    )
    allowed_class_ids = {c.class_id for c in allowed}
    if class_id not in allowed_class_ids:
        return jsonify({"message": "You are not authorized to access this class."}), 403

    students_obj = StudentsDB.query.with_entities(
                        StudentsDB.STUDENTS_NAME, StudentsDB.PHONE, StudentsDB.id,
                        StudentsDB.FATHERS_NAME, StudentsDB.IMAGE, 
                        StudentsDB.MOTHERS_NAME, StudentsDB.ADDRESS,StudentsDB.GENDER,
                        StudentsDB.PEN,

                        ClassData.Numeric_Subjects,ClassData.Grading_Subjects, 
                        ClassData.exam_format,ClassData.CLASS, 
                        StudentSessions.Attendance,
                        StudentSessions.ROLL,
                        TeachersLogin.Sign,
                        func.to_char(StudentsDB.DOB, 'Day, DD Month YYYY').label('DOB'),
                    ).join(
                        StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                    ).join(
                        ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                    ).join(
                        TeachersLogin, ClassData.class_teacher_id == TeachersLogin.id
                    ).filter(
                        StudentsDB.id == student_id,
                        StudentSessions.session_id == current_session_id
                    ).first()

    if not students_obj:
        return jsonify({"message": "Student not found"}), 404
    
    students_id = [students_obj.id]

    result = result_data(current_session_id, students_id)
    if not result:
        return jsonify({
            "html": '<div class="alert alert-warning text-center mt-5"><h5>No Result Found</h5></div>'
        })
    
    Data=[]

    student_data = students_obj._asdict()

    #student_data ={'STUDENTS_NAME': 'Faiz Raza', 'PHONE': '7866952', 'FATHERS_NAME': 'Ham Raza', 'id': 782, 
    #               'Numeric_Subjects': ['English', 'Hindi', 'Math', 'Urdu', 'SST/EVS', 'Computer', 'GK', 'Deeniyat'], 
    #               'Grading_Subjects': ['Drawing', 'Craft'], 'exam_format': {'FA1': '20', 'SA1': '80', 'FA2': '20', 'SA2': '80'}, 
    #               'CLASS': '2nd', 'ROLL': 201}



    numeric_subjects = student_data['Numeric_Subjects']
    grading_subjects = student_data['Grading_Subjects']
    exam_format = student_data['exam_format']

    FA1_Outof = int(exam_format["FA1"])
    SA1_Outof = int(exam_format["SA1"])
    FA2_Outof = int(exam_format["FA2"])
    SA2_Outof = int(exam_format["SA2"])

    FA1_SA1_Outof = FA1_Outof + SA1_Outof
    FA2_SA2_Outof = FA2_Outof + SA2_Outof
    Grand_Total_Outof = FA1_SA1_Outof + FA2_SA2_Outof

    no_of_subjects = len(numeric_subjects)
    extended_subjects = numeric_subjects + ["Total", "Percentage"]
    all_subjects = extended_subjects + grading_subjects

    student_data["Subjects"] = all_subjects
    student_data.update(result[student_id])


    student_data["Percentage"] = {}

    student_data["Percentage"]["FA1"] = round((float(student_data["Total"]["FA1"]) / (FA1_Outof * no_of_subjects))  * 100, 1)
    student_data["Percentage"]["FA2"] = round((int(student_data["Total"]["FA2"]) / (FA2_Outof * no_of_subjects))  * 100, 1)
    student_data["Percentage"]["SA1"] = round((int(student_data["Total"]["SA1"]) / (SA1_Outof * no_of_subjects)) * 100, 1)
    student_data["Percentage"]["SA2"] = round((int(student_data["Total"]["SA2"]) / (SA2_Outof * no_of_subjects)) * 100, 1)
    student_data["Percentage"]["FA1_SA1_Total"] = round((int(student_data["Total"]["FA1_SA1_Total"]) / (FA1_SA1_Outof * no_of_subjects))  * 100, 1)
    student_data["Percentage"]["FA2_SA2_Total"] = round((int(student_data["Total"]["FA2_SA2_Total"]) / (FA2_SA2_Outof * no_of_subjects)) * 100, 1)
    student_data["Percentage"]["Grand_Total"] = round((int(student_data["Total"]["Grand_Total"]) / (Grand_Total_Outof * no_of_subjects)) * 100, 1)


    for subject in extended_subjects:
        if subject == "Percentage":
            continue

        grand_total = int(student_data[subject]["Grand_Total"])
        if subject == "Total":
            percentage = (grand_total / (Grand_Total_Outof * no_of_subjects)) * 100
        else:
            percentage = (grand_total / Grand_Total_Outof) * 100

        student_data[subject]["Percentage"] = round(percentage, 1)
        grade, remark = get_grade(percentage)
        student_data[subject]["Grade"] = grade
        student_data[subject]["Remark"] = remark

        if subject == "Total":
            student_data["Percentage"]["Grade"] = grade
            student_data["Percentage"]["Remark"] = remark

    #print(student_data)
    Data.append(student_data)


    principle_sign = '14A_2bL47AwZ9ZZyhxsEpCcB1sfInjhe4'
    html = render_template('pdf-components/tall_result.html', data=Data[0], 
                            attandance_out_of = '214', principle_sign = principle_sign)
    return jsonify({"html":str(html)})
