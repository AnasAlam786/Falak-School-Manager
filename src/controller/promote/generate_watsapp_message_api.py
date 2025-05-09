# src/controller/generate_watsapp_message_api.py

from flask import session,  request, jsonify, Blueprint

from sqlalchemy.orm import aliased
from sqlalchemy import func

from src import db
from src.model import StudentsDB
from src.model import StudentSessions
from src.model import ClassData

from ..auth.login_required import login_required
from ..permissions.permission_required import permission_required



generate_watsapp_message_api_bp = Blueprint('generate_watsapp_message_api_bp',   __name__)



@generate_watsapp_message_api_bp.route('/generate_watsapp_message_api', methods=["POST"])
@login_required
@permission_required('promote_student')
def generate_message():
    data = request.json
    student_id = data.get('student_id')

    session_id = session["session_id"]

    if not student_id:
        return jsonify({"message": "Missing student ID"}), 400

    PromotedSession = aliased(StudentSessions)
    PromotedClass = aliased(ClassData)
    PreviousSession = aliased(StudentSessions)
    PreviousClass = aliased(ClassData)

    student_data = db.session.query(
        StudentsDB.STUDENTS_NAME,
        StudentsDB.PHONE,
        PromotedClass.CLASS.label("promoted_class"),
        PromotedSession.ROLL.label("promoted_roll"),
        PromotedSession.Due_Amount,

        func.to_char(PromotedSession.created_at, 'FMDay, DD Mon YYYY').label("promoted_date"),
        PreviousClass.CLASS.label("previous_class"),
    ).join(
        PromotedSession,
        (StudentsDB.id == PromotedSession.student_id) &
        (PromotedSession.session_id == session_id)
    ).join(
        PromotedClass,
        PromotedSession.class_id == PromotedClass.id
    ).outerjoin(
        PreviousSession,
        (StudentsDB.id == PreviousSession.student_id) &
        (PreviousSession.session_id == session_id - 1)
    ).outerjoin(
        PreviousClass,
        PreviousSession.class_id == PreviousClass.id
    ).filter(
        StudentsDB.id == student_id
    ).first()
    school_name = session["school_name"]

    message = f'''🎉 Congratulations,\nहमें ये बताते हुए अत्यंत ख़ुशी हो रही है कि _*{student_data.STUDENTS_NAME}*_ का प्रमोशन Class _*{student_data.previous_class}*_ से Class _*{student_data.promoted_class}*_ में सफलतापूर्वक हो चुका है!\n\n\t✨ नया रोल नंबर: _*{student_data.promoted_roll}*_\n\t⏱️ तारीख: _*{student_data.promoted_date}*_\n\n🙌 आपकी मेहनत रंग लाई! ऐसे ही आगे बढ़ते रहो, चमकते रहो और हम सबका नाम रोशन करते रहो! 🌟'''
            
    if student_data.Due_Amount:
        message += f'''\n\n 💰 शेष बकाया राशि: _*{student_data.Due_Amount}*_ रुपये, कृपया जल्द से जल्द भुगतान करने की कृपा करें। 🙏'''

    message += f'''\n🥳🎊 _*{school_name}*_ कि तरफ से ढेरों बधाइयाँ! 🎊🥳'''

        
    return jsonify({"whatsappMessage": message, "PHONE": student_data.PHONE}), 200
