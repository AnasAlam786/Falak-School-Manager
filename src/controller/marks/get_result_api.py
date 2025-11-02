# src/controller/get_result_api.py

from typing import OrderedDict
from flask import session, request, jsonify, Blueprint, render_template 
import pandas as pd
from sqlalchemy import func

from src.model import StudentsDB
from src.model.ClassAccess import ClassAccess
from src.model.Roles import Roles
from src.model.TeachersLogin import TeachersLogin

from .utils.calc_grades import get_grade
from .utils.marks_processing import result_data
from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required

# import time

get_result_api_bp = Blueprint('get_result_api_bp',   __name__)


def add_grand_total(group, exams):
    group["student_id"] = group.name

    df = group[group["exam_name"].isin(exams)]

    # --- Step 1: sum numeric marks per subject ---
    total_subject_marks = OrderedDict()
    for subj_dict in df["subject_marks_dict"]:
        for subj, mark in subj_dict.items():
            try:
                total_subject_marks[subj] = total_subject_marks.get(subj, 0) + int(mark)
            except:
                pass

    grand_total_row = df.iloc[0].copy()
    
    grand_total_row["exam_name"] = "G. Total"
    grand_total_row["exam_display_order"] = df["exam_display_order"].max() + 1
    grand_total_row["exam_total"] = sum(total_subject_marks.values())
    grand_total_row["weightage"] = df["weightage"].sum()
    grand_total_row["subject_marks_dict"] = total_subject_marks

    max_marks = int(grand_total_row["weightage"]) * len(grand_total_row["subject_marks_dict"])

    grand_total_row["percentage"] = int(
        (grand_total_row["exam_total"] / max_marks) * 100 if max_marks > 0 else 0
    )
    # grand_total_row["grade"], grand_total_row["remark"] = get_grade(grand_total_row["percentage"])
    # Concatenate both
    return pd.concat([group, pd.DataFrame([grand_total_row])], ignore_index=True)

def add_grades(group, exams):
    group["student_id"] = group.name


    # Only use rows whose exam_name is in the passed exams list
    df = group[group["exam_name"].isin(exams)]

    # Now df contains only the intended exams
    max_subject_marks = df["weightage"].sum()

    subject_grades = OrderedDict()
    subject_totals = OrderedDict()
    
    for subj_dict in df["subject_marks_dict"]:
        for subj, mark in subj_dict.items():
            try:
                subject_totals[subj] = subject_totals.get(subj, 0) + int(mark)
            except Exception as e:
                continue


            percentage = (subject_totals[subj] / max_subject_marks) * 100 if max_subject_marks > 0 else 0
            grade, _ = get_grade(percentage)
            subject_grades[subj] = grade

    grade_row = df.iloc[0].copy()
    max_total_marks = max_subject_marks * len(subject_grades)
    total_percentage = (sum(subject_totals.values()) / max_total_marks) * 100 if max_total_marks > 0 else 0
    grade, remark = get_grade(total_percentage)

    grade_row["exam_name"] = "Grades"
    grade_row["exam_display_order"] = df["exam_display_order"].max() + 2
    grade_row["exam_total"] = grade
    grade_row["weightage"] = "A,B,C,D,E"
    grade_row["percentage"] = None
    # grade_row["remark"] = remark
    grade_row["subject_marks_dict"] = subject_grades

    return pd.concat([group, pd.DataFrame([grade_row])], ignore_index=True)

@get_result_api_bp.route('/get_result_api', methods=["POST"])
@login_required
@permission_required('get_result')
def get_result_api():

    current_session_id = session["session_id"]
    user_id = session["user_id"]
    school_id = session["school_id"]

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
    
    extra_fields = {
        "StudentsDB": ["STUDENTS_NAME", "FATHERS_NAME", "FATHERS_NAME", "IMAGE",
                       "MOTHERS_NAME", "ADDRESS", "PHONE", 'GENDER', "PEN"],
        "expr": [func.to_char(StudentsDB.DOB, 'Dy, DD Mon YYYY').label("DOB")],
        "ClassData": ["CLASS"],
        "StudentSessions": ["ROLL", "class_id", "Attendance"],
        
    }


    student_marks_data = result_data(school_id, current_session_id, 
                                     class_id, student_ids=[student_id],
                                     extra_fields=extra_fields)

    # print(student_marks_data)

    if not student_marks_data:
        return jsonify({"message": "No Data Found"}), 400

    student_marks_df = pd.DataFrame(student_marks_data)

    # Extract Pure exam names and subjects
    exams = set(student_marks_df["exam_name"].unique())
    subjects = set()
    for exam in exams:
        exam_df = student_marks_df[student_marks_df["exam_name"] == exam]
        for subj_dict in exam_df["subject_marks_dict"]:
            subjects.update(subj_dict.keys())


    student_marks_df = (
        student_marks_df
        .groupby("student_id", group_keys=False)
        .apply(lambda g: add_grades(g, exams), include_groups=False)
        .reset_index(drop=True)
    )

    student_marks_df = (
        student_marks_df
        .groupby("student_id", group_keys=False)
        .apply(lambda g: add_grand_total(g, exams), include_groups=False)
        .reset_index(drop=True)
    )
    

    student_marks_df['percentage'] = student_marks_df['percentage'].fillna(0).round(1)
    student_marks_df['exam_total'] = pd.to_numeric(student_marks_df['exam_total'], errors='coerce').fillna(0).round(1)


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

    student_marks_df[common_columns] = student_marks_df[common_columns].fillna("")
    student_marks_df = student_marks_df.groupby(common_columns).apply(exam_info_group, include_groups=False).reset_index(name = "marks")

    student_marks_df = student_marks_df.sort_values(["CLASS", "ROLL"]).reset_index(drop=True)
    student_marks = student_marks_df.to_dict(orient='records')

    # # Print the structure of result student_marks_dict
    # import pprint
    # pprint.pprint(student_marks)

    # get principal and class teacher sign from database
    principle_sign = (
        TeachersLogin.query
        .join(Roles, Roles.id == TeachersLogin.role_id)
        .filter(
            TeachersLogin.school_id == school_id,
            Roles.role_name == 'Principal'
        ).first()
    )
    

    # Teacher sign
    teacher_sign = (
        TeachersLogin.query
        .join(ClassAccess, ClassAccess.staff_id == TeachersLogin.id)
        .join(Roles, Roles.id == TeachersLogin.role_id)
        .filter(
            ClassAccess.class_id == class_id,
            TeachersLogin.school_id == school_id,
            Roles.role_name == 'Teacher'
        ).first()
    )

    principle_sign = principle_sign.Sign if principle_sign else None
    teacher_sign = teacher_sign.Sign if teacher_sign else None

    # principle_sign = principle_sign[0] if principle_sign else None
    # teacher_sign = teacher_sign[0] if teacher_sign else None

    html = render_template('pdf-components/tall_result.html', student=student_marks[0], 
                            attandance_out_of = '214', 
                            principle_sign = principle_sign, teacher_sign = teacher_sign)
    return jsonify({"html":str(html)})
