# src/controller/get_result_api.py

from typing import OrderedDict
from flask import session, request, jsonify, Blueprint, render_template 
import pandas as pd
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


def add_grand_total(group):
    group["student_id"] = group.name

    # --- Step 1: sum numeric marks per subject ---
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
    grand_total_row["exam_display_order"] = group["exam_display_order"].max() + 1
    grand_total_row["exam_total"] = sum(total_subject_marks.values())
    grand_total_row["weightage"] = group["weightage"].sum()
    grand_total_row["subject_marks_dict"] = total_subject_marks

    max_marks = int(grand_total_row["weightage"]) * len(grand_total_row["subject_marks_dict"])

    grand_total_row["percentage"] = int(
        (grand_total_row["exam_total"] / max_marks) * 100 if max_marks > 0 else 0
    )


    # Concatenate both
    return pd.concat([group, pd.DataFrame([grand_total_row])], ignore_index=True)


@get_result_api_bp.route('/get_result_api', methods=["POST"])
@login_required
@permission_required('get_result')
def get_result_api():

    current_session_id = session["session_id"]
    user_id = session["user_id"]
    school_id = session["school_id"]

    print("Request JSON:", request.json)

    try:
        student_id = int(request.json.get("id"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid student ID."}), 400
    
    try:
        class_id = int(request.json.get("class_id"))
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid class ID."}), 400

    # Session checks
    if not student_id or not current_session_id or not user_id:
        return jsonify({"message": "Session data missing. Please logout and login again!"}), 403

    student_marks_data = result_data(school_id, current_session_id, class_id, student_ids=[student_id])
    print(student_marks_data)

    if not student_marks_data:
        return jsonify({"message": "No Data Found"}), 400

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
    student_marks_df = student_marks_df.sort_values(["CLASS", "ROLL"]).reset_index(drop=True)
    student_marks = student_marks_df.to_dict(orient='records')

    # Print the structure of result student_marks_dict
    import pprint
    pprint.pprint(student_marks)


    principle_sign = '14A_2bL47AwZ9ZZyhxsEpCcB1sfInjhe4'
    html = render_template('pdf-components/tall_result.html', student=student_marks[0], 
                            attandance_out_of = '214', principle_sign = principle_sign)
    return jsonify({"html":str(html)})
