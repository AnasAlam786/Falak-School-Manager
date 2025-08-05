# src/controller/utils/marks/marks_processing.py

from itertools import groupby
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import case, cast, func, literal
from sqlalchemy.sql.sqltypes import Integer, Numeric, String

from src.model import StudentsDB, StudentsMarks, ClassData, StudentSessions
from src import db

def _cast_numeric_if_digits(column_expr, default: Union[int, float] = 0):
    """
    SQLAlchemy expression: if `column_expr` is all digits (optionally with decimal),
    cast it to Numeric; otherwise use `default`.
    This lets SUM() ignore non-numeric marks.
    """
    return case(
        (column_expr.op("~")(r"^[0-9]+(\.[0-9]+)?$"), cast(column_expr, Numeric)),
        else_=default
    )


def result_data(current_session_id: int, student_ids: Optional[List[int]] = None
                ) -> Dict[int, Dict[str, Any]]:
    """
    Fetch per-subject and total/rank data for a set of students in one session.

    Parameters:
        current_session_id  The academic session ID to filter by.
        student_ids         List of student IDs to include. If empty or None, returns {}.

    Returns:
        A dict mapping each student_id ➔ {
            subject_name: {
                "FA1": row.FA1,
                "SA1": row.SA1,
                "FA2": row.FA2,
                "SA2": row.SA2,
                "FA1_SA1_Total": row.FA1_SA1_Total,
                "FA2_SA2_Total": row.FA2_SA2_Total,
                "Grand_Total": row.Grand_Total,
                "SA1_Rank": row.SA1_Rank,
                "SA2_Rank": row.SA2_Rank,
                "Grand_Rank": row.Grand_Rank,
            },
            "Total": { ... }   # same keys, but totals across subjects and class-wide ranks
        }
    """
    if not student_ids:
        return {}

    # --- per-subject rows for just these students ---
    subj_q = (
        db.session.query(
            StudentsMarks.student_id,
            cast(StudentsMarks.Subject, String).label("Subject"),
            StudentsMarks.FA1.label("FA1"),
            StudentsMarks.SA1.label("SA1"),
            StudentsMarks.FA2.label("FA2"),
            StudentsMarks.SA2.label("SA2"),
            # Cast totals to String to match summary query
            cast(
                _cast_numeric_if_digits(StudentsMarks.FA1)
                + _cast_numeric_if_digits(StudentsMarks.SA1),
                String
            ).label("FA1_SA1_Total"),
            cast(
                _cast_numeric_if_digits(StudentsMarks.FA2)
                + _cast_numeric_if_digits(StudentsMarks.SA2),
                String
            ).label("FA2_SA2_Total"),
            cast(
                _cast_numeric_if_digits(StudentsMarks.FA1)
                + _cast_numeric_if_digits(StudentsMarks.SA1)
                + _cast_numeric_if_digits(StudentsMarks.FA2)
                + _cast_numeric_if_digits(StudentsMarks.SA2),
                String
            ).label("Grand_Total"),
            literal(None).cast(Integer).label("SA1_Rank"),
            literal(None).cast(Integer).label("SA2_Rank"),
            literal(None).cast(Integer).label("Grand_Rank"),
        )
        .join(StudentsDB, StudentsMarks.student_id == StudentsDB.id)
        .filter(
            StudentsMarks.session_id == current_session_id,
            StudentsMarks.student_id.in_(student_ids),
        )
    )

    # --- summary rows (totals + class-wide ranks) for all students in that session ---
    sum_q = (
        db.session.query(
            StudentsMarks.student_id,
            literal("Total").cast(String).label("Subject"),
            cast(func.sum(_cast_numeric_if_digits(StudentsMarks.FA1)), String).label("FA1"),
            cast(func.sum(_cast_numeric_if_digits(StudentsMarks.SA1)), String).label("SA1"),
            cast(func.sum(_cast_numeric_if_digits(StudentsMarks.FA2)), String).label("FA2"),
            cast(func.sum(_cast_numeric_if_digits(StudentsMarks.SA2)), String).label("SA2"),
            cast(
                func.sum(
                    _cast_numeric_if_digits(StudentsMarks.FA1)
                    + _cast_numeric_if_digits(StudentsMarks.SA1)
                ), String
            ).label("FA1_SA1_Total"),
            cast(
                func.sum(
                    _cast_numeric_if_digits(StudentsMarks.FA2)
                    + _cast_numeric_if_digits(StudentsMarks.SA2)
                ), String
            ).label("FA2_SA2_Total"),
            cast(
                func.sum(
                    _cast_numeric_if_digits(StudentsMarks.FA1)
                    + _cast_numeric_if_digits(StudentsMarks.SA1)
                    + _cast_numeric_if_digits(StudentsMarks.FA2)
                    + _cast_numeric_if_digits(StudentsMarks.SA2)
                ), String
            ).label("Grand_Total"),
            func.rank()
            .over(
                partition_by=ClassData.CLASS,
                order_by=func.sum(_cast_numeric_if_digits(StudentsMarks.SA1)).desc(),
            )
            .label("SA1_Rank"),
            func.rank()
            .over(
                partition_by=ClassData.CLASS,
                order_by=func.sum(_cast_numeric_if_digits(StudentsMarks.SA2)).desc(),
            )
            .label("SA2_Rank"),
            func.rank()
            .over(
                partition_by=ClassData.CLASS,
                order_by=func.sum(
                    _cast_numeric_if_digits(StudentsMarks.FA1)
                    + _cast_numeric_if_digits(StudentsMarks.SA1)
                    + _cast_numeric_if_digits(StudentsMarks.FA2)
                    + _cast_numeric_if_digits(StudentsMarks.SA2)
                ).desc(),
            )
            .label("Grand_Rank"),
        )
        .join(StudentsDB, StudentsMarks.student_id == StudentsDB.id)
        .join(StudentSessions, StudentsDB.id == StudentSessions.student_id)
        .join(ClassData, StudentSessions.class_id == ClassData.id)
        .filter(StudentsMarks.session_id == current_session_id)
        .group_by(StudentsMarks.student_id, ClassData.CLASS)
    )

    # --- union them and pull into Python objects ---
    combined = subj_q.union_all(sum_q).all()

    # Keep only our target students
    filtered = [row for row in combined if row.student_id in set(student_ids)]

    # Sort and group by student_id
    filtered.sort(key=lambda r: r.student_id)
    grouped: Dict[int, Dict[str, Any]] = {}
    for sid, rows in groupby(filtered, key=lambda r: r.student_id):
        grouped[sid] = {
            row.Subject: {
                "FA1": row.FA1,
                "SA1": row.SA1,
                "FA2": row.FA2,
                "SA2": row.SA2,
                "FA1_SA1_Total": row.FA1_SA1_Total,
                "FA2_SA2_Total": row.FA2_SA2_Total,
                "Grand_Total": row.Grand_Total,
                "SA1_Rank": row.SA1_Rank,
                "SA2_Rank": row.SA2_Rank,
                "Grand_Rank": row.Grand_Rank,
            }
            for row in rows
        }

    return grouped
