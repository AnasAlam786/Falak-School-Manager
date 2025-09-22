"""Marks processing utilities built around the new StudentsMarks_duplicate model.

This module exposes a reusable query-builder that can be used across the app to
compose SQLAlchemy queries for marks with a fluent API.

Compatibility wrapper `result_data()` is provided for existing controllers.
"""

from src import db
from src.model.ClassExams import ClassExams
from src.model.StudentsDB import StudentsDB
from src.model.StudentSessions import StudentSessions
from src.model.ClassData import ClassData
from src.model.Subjects import Subjects
from src.model.Exams import Exams
from src.model.StudentsMarks_duplicate import StudentsMarks_duplicate

from sqlalchemy import func, case, cast, Float, literal, func, desc
from sqlalchemy.sql import over
from sqlalchemy.dialects.postgresql import aggregate_order_by
from collections import OrderedDict


def result_data(school_id, session_id, class_id, student_ids=None):

    # Step A: students in this session+class (limit scope for performance)
    students_subq = (
        db.session.query(StudentSessions.student_id)
        .filter(StudentSessions.session_id == session_id)
        .filter(StudentSessions.class_id == class_id)
    )

    if student_ids:
        students_subq = students_subq.filter(StudentSessions.student_id.in_(student_ids))
    students_subq = students_subq.subquery()
    

    # Step B: exams for the school
    exams_subq = (
        db.session.query(
            Exams.id.label("exam_id"),
            Exams.exam_code.label("exam_name"),   # or exam_code if you prefer
            Exams.term.label("exam_term"),
            Exams.weightage,
            Exams.display_order.label("exam_display_order")
        )
        .join(ClassExams, ClassExams.exam_id == Exams.id)
        .filter(ClassExams.class_id == class_id,
                Exams.school_id == school_id)
        .distinct()  # ensure uniqueness
        .subquery()
    )

    # Step C: subjects for the class (we need subjects even when marks are missing)
    subjects_subq = (
        db.session.query(
            Subjects.id.label('subject_id'),
            Subjects.subject.label('subject_name'),
            Subjects.evaluation_type,
            Subjects.display_order.label('subject_display_order')
        )
        .filter(Subjects.class_id == class_id)
        .subquery()
    )

    ses = (
        db.session.query(
            students_subq.c.student_id,
            exams_subq.c.exam_id,
            exams_subq.c.exam_name,
            exams_subq.c.weightage,
            exams_subq.c.exam_term,
            exams_subq.c.exam_display_order,
            subjects_subq.c.subject_id,
            subjects_subq.c.subject_name,
            subjects_subq.c.evaluation_type,
            subjects_subq.c.subject_display_order
        )
        .select_from(students_subq)              # explicit starting table
        .join(exams_subq, literal(True))         # cross join students × exams
        .join(subjects_subq, literal(True))      # cross join × subjects
        .subquery()
    )

    # Step F: LEFT JOIN marks on student + exam + subject
    marks_with_subjects = (
        db.session.query(
            ses.c.student_id,
            ses.c.exam_name,
            ses.c.weightage,
            ses.c.exam_term,
            ses.c.exam_display_order,
            ses.c.subject_id,
            ses.c.subject_name,
            ses.c.evaluation_type,
            ses.c.subject_display_order,
            StudentsMarks_duplicate.score
        )
        .outerjoin(
            StudentsMarks_duplicate,
            (StudentsMarks_duplicate.student_id == ses.c.student_id) &
            (StudentsMarks_duplicate.exam_id == ses.c.exam_id) &
            (StudentsMarks_duplicate.subject_id == ses.c.subject_id) &
            (StudentsMarks_duplicate.session_id == session_id)   # 🔑 Important
        )
        .subquery()
    )

    # Step G: Aggregate per student+exam
    # -> jsonb_agg of { subject_name: blank-or-score } in subject order
    # -> sum numeric scores
    # -> safe percentage using NULLIF to avoid division by zero (percentage will be NULL if denom is 0)
    subq = (
        db.session.query(
            marks_with_subjects.c.student_id,
            marks_with_subjects.c.exam_name,
            marks_with_subjects.c.weightage,
            marks_with_subjects.c.exam_term,
            marks_with_subjects.c.exam_display_order,

            func.jsonb_agg(
                aggregate_order_by(
                    func.jsonb_build_object(
                        marks_with_subjects.c.subject_name,
                        func.coalesce(marks_with_subjects.c.score, '')   # blank when missing
                    ),
                    marks_with_subjects.c.subject_display_order.asc()
                )
            ).label('subject_marks_dict'),

            # total numeric marks (0 for non-numeric rows)
            func.sum(
                case(
                    (marks_with_subjects.c.evaluation_type == 'numeric',
                     cast(marks_with_subjects.c.score, Float)),
                    else_=0
                )
            ).label('exam_total'),

            # percentage = (sum_numeric * 100) / nullif(weightage * number_of_numeric_subjects, 0)
            (
                func.sum(
                    case(
                        (marks_with_subjects.c.evaluation_type == 'numeric',
                         cast(marks_with_subjects.c.score, Float)),
                        else_=0
                    )
                ) * 100.0
                /
                func.nullif(
                    marks_with_subjects.c.weightage *
                    func.count(
                        case(
                            (marks_with_subjects.c.evaluation_type == 'numeric', 1)
                        )
                    ),
                    0
                )
            ).label('percentage')
        )
        .group_by(
            marks_with_subjects.c.student_id,
            marks_with_subjects.c.exam_name,
            marks_with_subjects.c.weightage,
            marks_with_subjects.c.exam_term,
            marks_with_subjects.c.exam_display_order
        )
        .subquery()
    )



    # Step H: join student details and return
    final_query = (
        db.session.query(
            subq.c.exam_name,
            subq.c.weightage,
            subq.c.exam_term,
            subq.c.subject_marks_dict,
            subq.c.exam_total,
            subq.c.percentage,
            subq.c.exam_display_order,

            StudentsDB.id.label('student_id'),
            StudentsDB.STUDENTS_NAME,
            StudentsDB.DOB,
            StudentsDB.FATHERS_NAME,

            ClassData.CLASS,
            StudentSessions.class_id.label('class_id'),
            StudentSessions.ROLL,
        )
        .join(StudentSessions, StudentSessions.student_id == subq.c.student_id)
        .join(StudentsDB, StudentsDB.id == StudentSessions.student_id)
        .join(ClassData, ClassData.id == StudentSessions.class_id)
        .filter(StudentSessions.session_id == session_id,
                StudentSessions.class_id == class_id)
        .order_by(subq.c.exam_display_order, StudentSessions.ROLL)
    )

    result = final_query.all()

    def result_to_dict(row):
        row_dict = row._asdict()
        mj = row_dict.get("subject_marks_dict")
        if mj:
            ordered_marks = OrderedDict()
            for kv in mj:
                ordered_marks.update(kv)
            row_dict["subject_marks_dict"] = ordered_marks

        return row_dict

    return [result_to_dict(r) for r in result]