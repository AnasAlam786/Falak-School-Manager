from types import SimpleNamespace
from flask import render_template, session, request, Blueprint, jsonify

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

from src.model import StudentsDB, ClassData, StudentSessions, Schools
from src import db

get_seat_chits_bp = Blueprint('get_seat_chits_bp', __name__)


@get_seat_chits_bp.route('/seat_chits', methods=['GET'])
@login_required
@permission_required('admission')
def get_seat_chits_api():
    """Fetch students for admit cards and render `admit.html`.

    Accepts optional JSON payload (POST) or query params (GET):
      - class: class id to filter students by class
      - exam: exam name to display on cards
      - year: year to display on cards
      - quality: image size quality for GDrive images (default 200)

    Returns JSON with rendered HTML under the "html" key (consistent with other APIs).
    """

    school_id = session.get('school_id')
    current_session_id = session.get('session_id')

    if not school_id or not current_session_id:
        return jsonify({"message": "Missing session context (school/session)."}), 400

    # Build base query for students in the current session and school
    query = db.session.query(
        StudentsDB.STUDENTS_NAME,
        StudentsDB.IMAGE,
        StudentsDB.FATHERS_NAME,
        ClassData.CLASS.label('CLASS'),
        StudentSessions.ROLL,
    ).join(
        StudentSessions, StudentSessions.student_id == StudentsDB.id
    ).join(
        ClassData, StudentSessions.class_id == ClassData.id
    ).filter(
        StudentsDB.school_id == school_id,
        ~ClassData.id.in_([1, 2, 3]),  # exclude class IDs 1, 2, and 3
        StudentSessions.session_id == current_session_id,
    ).order_by(
        ClassData.display_order,  # first order by class display order
        StudentSessions.ROLL      # then by roll number
    )

    students = query.all()


    # Group students into sets of 12 using list slicing
    # i goes from 0 to total students in steps of 12
    # students[i:i+12] picks 12 students starting from index i
    grouped_students = [students[i:i+15] for i in range(0, len(students), 15)]

    return render_template('admit_card/exam_seat_chits.html', data=grouped_students)
