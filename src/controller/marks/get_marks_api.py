# src/controller/get_marks_api.py

from flask import session, request, jsonify, Blueprint, render_template 

from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src.model.ClassAccess import ClassAccess
from src import db

from .utils.calc_grades import get_grade
from .utils.marks_processing import result_data

from bs4 import BeautifulSoup


get_marks_api_bp = Blueprint('get_marks_api_bp',   __name__)


@get_marks_api_bp.route('/get_marks_api', methods=["POST"])
def get_marks_api():
    
    if "email" not in session:
        return jsonify({"message": "Unauthorized access. Login requires!"}), 403
    

    school_id = session["school_id"]
    current_session_id = session["session_id"]
    user_id = session["user_id"]

    try:
        class_id = int(request.json.get("class_id"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid class selected."}), 400

    if not school_id or not current_session_id or not user_id:
        return jsonify({"message": "Unable to get session data, Please try to logout and login again!"}), 403


    allowed_class_ids = (
        db.session.query(ClassAccess.class_id)
        .filter(ClassAccess.staff_id == user_id)
        .all()
    )
    allowed_class_ids = {c.class_id for c in allowed_class_ids}

    if class_id not in allowed_class_ids:
        return jsonify({"message": "You are not authorized to access this class."}), 403

    students_obj = StudentsDB.query.with_entities(
                    StudentsDB.STUDENTS_NAME, StudentsDB.PHONE,
                    StudentsDB.FATHERS_NAME, StudentsDB.id,
                    ClassData.Numeric_Subjects,ClassData.Grading_Subjects, 
                    ClassData.exam_format, ClassData.CLASS, 
                    StudentSessions.ROLL, 
                ).join(
                    StudentSessions, StudentSessions.student_id == StudentsDB.id  # Join using the foreign key
                ).join(
                    ClassData, StudentSessions.class_id == ClassData.id  # Join using the foreign key
                ).filter(
                    ClassData.id == class_id,
                    StudentsDB.school_id == school_id,
                    StudentSessions.session_id == current_session_id
                ).order_by(
                    StudentSessions.ROLL
                ).all()

    students_ids = [row.id for row in students_obj]

    results = result_data(current_session_id, students_ids)

    if not results:
        return jsonify({
            "html": """
            <div class="alert alert-warning text-center" role="alert" style="margin-top: 50px;">
                <h5 class="mb-0">No Students Found</h5>
            </div>
            """
        })

    Data=[]

    students_dict = {s.id: dict(s._asdict()) for s in students_obj}


    for student_id, student_data in students_dict.items():

        #student_id = 7682
        #student_data ={'STUDENTS_NAME': 'Faiz Raza', 'PHONE': '7866952', 'FATHERS_NAME': 'Ham Raza', 'id': 782, 
        #               'Numeric_Subjects': ['English', 'Hindi', 'Math', 'Urdu', 'SST/EVS', 'Computer', 'GK', 'Deeniyat'], 
        #               'Grading_Subjects': ['Drawing', 'Craft'], 'exam_format': {'FA1': '20', 'SA1': '80', 'FA2': '20', 'SA2': '80'}, 
        #               'CLASS': '2nd', 'ROLL': 201}



        numeric_subjects = student_data['Numeric_Subjects']
        grades_subjects = student_data['Grading_Subjects']
        exam_format = student_data['exam_format']

        FA1_Outof = int(exam_format["FA1"])
        SA1_Outof = int(exam_format["SA1"]) 
        FA1_SA1_Outof = FA1_Outof + SA1_Outof

        FA2_Outof = int(exam_format["FA2"])
        SA2_Outof = int(exam_format["SA2"])
        FA2_SA2_Outof = FA2_Outof + SA2_Outof

        Grand_Total_Outof = FA1_SA1_Outof + FA2_SA2_Outof

        no_of_numeric_subjects = len(numeric_subjects)

        numeric_subjects.append("Total")
        numeric_subjects.append("Percentage")
        Subjects = numeric_subjects + grades_subjects

        student_data["Subjects"] = Subjects

        #Mering Result and Student Data
        student_data.update(results[student_id])


        student_data["Percentage"] = {}

        student_data["Percentage"]["FA1"] = round((float(student_data["Total"]["FA1"]) / (FA1_Outof * no_of_numeric_subjects))  * 100, 1)
        student_data["Percentage"]["FA2"] = round((int(student_data["Total"]["FA2"]) / (FA2_Outof * no_of_numeric_subjects))  * 100, 1)
        student_data["Percentage"]["FA1_SA1_Total"] = round((int(student_data["Total"]["FA1_SA1_Total"]) / (FA1_SA1_Outof * no_of_numeric_subjects))  * 100, 1)
        
        
        student_data["Percentage"]["SA1"] = round((int(student_data["Total"]["SA1"]) / (SA1_Outof * no_of_numeric_subjects)) * 100, 1)
        student_data["Percentage"]["SA2"] = round((int(student_data["Total"]["SA2"]) / (SA2_Outof * no_of_numeric_subjects)) * 100, 1)
        student_data["Percentage"]["FA2_SA2_Total"] = round((int(student_data["Total"]["FA2_SA2_Total"]) / (FA2_SA2_Outof * no_of_numeric_subjects)) * 100, 1)
                                                    
        student_data["Percentage"]["Grand_Total"] = round((int(student_data["Total"]["Grand_Total"]) / (Grand_Total_Outof * no_of_numeric_subjects)) * 100, 1)

        for subject in numeric_subjects:

            if subject == 'Percentage':
                continue

            if subject == 'Total':
                percentage = int(student_data[subject]["Grand_Total"]) / (Grand_Total_Outof * no_of_numeric_subjects) * 100
                student_data[subject]["Percentage"] = round(percentage, 1)
                grade, remark = get_grade(percentage)

                student_data[subject]["Grade"] = grade
                student_data[subject]["Remark"] = remark

                student_data['Percentage']["Grade"] = grade
                student_data['Percentage']["Remark"] = remark
                
                continue


            percentage = int(student_data[subject]["Grand_Total"]) / (Grand_Total_Outof) * 100
            student_data[subject]["Percentage"] = round(percentage, 1)  #subject wise percentage


            grade, remark = get_grade(percentage)    # Calculate grade and remark of numerical subjects only based on percentage
            student_data[subject]["Grade"] = grade
            student_data[subject]["Remark"] = remark

        #print(student_data)

        Data.append(student_data)


    html = render_template('show_marks.html', Data=Data)
    soup = BeautifulSoup(html,"lxml")
    content = soup.body.find('div',{'id':'results'}).decode_contents()

    return jsonify({"html":str(content)})
    