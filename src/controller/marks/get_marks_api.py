# src/controller/get_marks_api.py


from typing import OrderedDict
from sqlalchemy import exists, true
from flask import session, request, jsonify, Blueprint, render_template 


from src.model.ClassAccess import ClassAccess
from src import db

from src.controller.marks.utils.calc_grades import get_grade
from src.controller.marks.utils.marks_processing import result_data

from bs4 import BeautifulSoup

import pandas as pd
from decimal import Decimal
import datetime


get_marks_api_bp = Blueprint('get_marks_api_bp',   __name__)

def convert_serializable(obj):
    if isinstance(obj, Decimal):
        return float(obj)   # Convert Decimal to float
    elif isinstance(obj, datetime.date):
        return obj.isoformat()  # Convert date to string
    elif isinstance(obj, dict):
        return {k: convert_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_serializable(i) for i in obj]
    return obj

def add_grand_total(group):

    group["student_id"] = group.name
    total_subject_marks = OrderedDict()

    for subj_dict in group["subject_marks_dict"]:
        for subj, mark in subj_dict.items():
            try:
                mark = float(mark)
                total_subject_marks[subj] = total_subject_marks.get(subj, 0) + mark
            except:
                pass

    grand_total_row = group.iloc[0].copy()
    
    grand_total_row["exam_name"] = "G. Total"
    grand_total_row["exam_display_order"] = len(group)+1
    grand_total_row["exam_total"] = sum(total_subject_marks.values())
    grand_total_row["weightage"] = sum(group.weightage.values)
    grand_total_row["subject_marks_dict"] = total_subject_marks

    max_marks = int(grand_total_row["weightage"]) * len(grand_total_row["subject_marks_dict"])

    grand_total_row["percentage"] = int(
        (grand_total_row["exam_total"] / max_marks) * 100 if max_marks > 0 else 0
    )

    # Concatenate both
    return pd.concat([group, pd.DataFrame([grand_total_row])], ignore_index=True)

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


    has_access = db.session.query(
        exists().where(ClassAccess.staff_id == user_id)
    ).scalar()

    if not has_access:
        return jsonify({"message": "You are not authorized to access this class."}), 403
    
    student_marks_data = result_data(school_id, current_session_id, class_id)


    if not student_marks_data:
        return jsonify({"message": "No Data Found"}), 400

    
    # serializable_data = convert_serializable(student_marks_data)
    # try:
    #     response = requests.post(
    #         'http://127.0.0.1:5000/process-marks',
    #         json={"student_marks_data": serializable_data},
    #         headers={"X-API-Key": 'Falak@12345'},
    #         timeout=10
    #     )
    #     print(response.json())
    #     response.raise_for_status()

    #     # ✅ Store processed result in variable instead of returning
    #     student_marks = response.json()



    # except requests.exceptions.RequestException as e:
    #     return jsonify({"error": str(e)}), 500



    student_marks_df = pd.DataFrame(student_marks_data)

    student_marks_df = student_marks_df.groupby("student_id", group_keys=False).apply(add_grand_total, include_groups=False).reset_index(drop=True)    
    student_marks_df['percentage'] = student_marks_df['percentage'].astype(int)


    all_columns = student_marks_df.columns.tolist()
    non_common_colums = ['exam_name', 'subject_marks_dict', 'exam_total', 'percentage', 'exam_display_order', 'weightage', "exam_term"]
    common_columns = [col for col in all_columns if col not in non_common_colums]


    def exam_info_group(df):
        df_sorted = df.sort_values('exam_display_order', na_position='last')
        
        ordered_exams = OrderedDict()
        for _, row in df_sorted.iterrows():
            ordered_exams[row['exam_name']] = {
                'subject_marks_dict': row['subject_marks_dict'],
                'exam_total': row['exam_total'],
                'percentage': row['percentage'],
                'weightage': row['weightage'],
                'exam_term': row['exam_term'],
            }
        return ordered_exams


    
    student_marks_df = student_marks_df.groupby(common_columns).apply(exam_info_group, include_groups=False).reset_index(name = "marks")
    student_marks = student_marks_df.to_dict(orient='records')

    # # Print the structure of result student_marks_dict
    # import pprint
    # pprint.pprint(student_marks)
   

    html = render_template('show_marks.html', student_marks=student_marks)
    soup = BeautifulSoup(html,"lxml")
    content = soup.body.find('div',{'id':'results'}).decode_contents()



    return jsonify({"html":str(content)})
    