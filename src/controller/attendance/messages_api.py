from datetime import datetime
from flask import session, request, jsonify, Blueprint

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required

get_message_api_bp = Blueprint( 'get_message_api_bp',   __name__)


@get_message_api_bp.route('/api/get_absent_message', methods=["GET"])
@login_required
@permission_required('attendance')
def get_absent_message_api():

    student_name = request.args.get("studentName")
    father_name = request.args.get("fathersName")
    class_name = request.args.get("className")
    date_str = request.args.get("date")
    school_name = session.get("school_name")

    


    def parse_date(date_str):
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except:
                pass
        return None

    try:
        date = parse_date(date_str)
        current_date = datetime.today().date()

        date_expanded = date.strftime("%A, %d %B %Y")
        

        message = f"""🔔 *Attendance Alert — {school_name}* 🔔
        
    👦 Student Name: *{student_name}*
    👨 Father's Name: *{father_name}*
    🏫 Class: *{class_name}*
    📅 Date: *{date_expanded}*

    ❗ Your child, *{student_name}* did not attend school {"on " + date_expanded if date != current_date else "today"}, so he/she has been marked ABSENT.

    If this was due to illness or any genuine reason, please try to inform the school. 
    You can ignore this message if you have already informed.

    *🤝 Thank you for keeping us informed.
        """
    except Exception as e: 
        print(f"Error generating absent message: {e}")
        return jsonify({"message": "Failed to generate absent message"}), 500



    return jsonify({"absent_message": message }), 200