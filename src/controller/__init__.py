# src/controller/__init__.py

from .auth.login import login_bp
from .auth.logout import logout_bp

from .home import home_bp
from .students_list.student_list import student_list_bp
from .students_list.student_modal_data_api import student_modal_data_api_bp

from .students.update.update_student_info import update_student_info_bp
from .students.update.final_student_update_api import final_student_update_api_bp
from .students.update.update_conflic_varification import update_conflict_verification_api_bp

from .fees.pay_fee_api import pay_fee_api_bp
from .fees.get_fee_api import get_fee_api_bp

from .marks.fill_marks import fill_marks_bp
from .marks.update_marks_api import update_marks_api_bp
from .marks.show_marks import show_marks_bp
from .marks.get_marks_api import get_marks_api_bp
from .marks.get_result_api import get_result_api_bp

from .staff_module.staff_view import staff_view_bp
from .staff_module.add_staff import add_staff_bp
from .staff_module.update_staff import update_staff_bp
from .staff_module.add_staff_api import add_staff_api_bp

from .idcard.idcard import idcard_bp


from .sessions.change_session import change_session_bp
from .RTE.RTE_students import RTE_students_bp

from .promote.promote_student import promote_student_bp
from .promote.prv_year_students_api import prv_year_student_api_bp
from .promote.student_data_modal_api import student_data_modal_api_bp
from .promote.promoted_student_modal_api import promoted_student_modal_api_bp

from .promote.final_promotion_api import final_promotion_api_bp
from .promote.final_update_api import final_update_api_bp
from .promote.final_depromotion_api import final_depromotion_api_bp
from .promote.generate_watsapp_message_api import generate_watsapp_message_api_bp

from .tc.tc import tc_bp
from .tc.tc_student_list_api import tc_student_list_api_bp
from .tc.generate_tc_form_api import generate_tc_form_api_bp

from .students.add_student.admission import admission_bp
from .students.add_student.pydantic_verification_api import pydantic_verification_api_bp
from .students.add_student.conflict_verification_api import conflict_verification_api_bp
from .students.add_student.get_new_roll_api import get_new_roll_api_bp
from .students.add_student.final_admission_api import final_admission_api_bp

from .students.utils.create_watsapp_message_api import create_watsapp_message_api_bp
from .students.utils.create_admission_form_api import create_admission_form_api_bp


from .temp.temp_page import temp_page_bp
from .temp.fill_colums_api import fill_colums_api_bp

from .tools.question_paper import question_paper_bp
from .tools.question_paper_api import question_paper_api_bp

from .staff_module import staff_bp

def register_blueprints(app):

    app.register_blueprint(login_bp)
    app.register_blueprint(logout_bp)
    app.register_blueprint(change_session_bp)

    app.register_blueprint(home_bp)
    app.register_blueprint(student_list_bp)
    app.register_blueprint(student_modal_data_api_bp)

    app.register_blueprint(update_student_info_bp)
    app.register_blueprint(final_student_update_api_bp)
    app.register_blueprint(update_conflict_verification_api_bp)
    
    app.register_blueprint(pay_fee_api_bp)
    app.register_blueprint(get_fee_api_bp)

    app.register_blueprint(admission_bp)
    app.register_blueprint(pydantic_verification_api_bp)
    app.register_blueprint(conflict_verification_api_bp)
    app.register_blueprint(get_new_roll_api_bp)
    app.register_blueprint(final_admission_api_bp)

    app.register_blueprint(create_watsapp_message_api_bp)
    app.register_blueprint(create_admission_form_api_bp)

    app.register_blueprint(fill_marks_bp)
    app.register_blueprint(update_marks_api_bp)
    app.register_blueprint(show_marks_bp)
    app.register_blueprint(get_marks_api_bp)
    app.register_blueprint(get_result_api_bp)

    app.register_blueprint(staff_view_bp)
    app.register_blueprint(add_staff_api_bp)
    app.register_blueprint(add_staff_bp)
    app.register_blueprint(update_staff_bp)

    app.register_blueprint(idcard_bp)

    app.register_blueprint(promote_student_bp)
    app.register_blueprint(prv_year_student_api_bp)
    app.register_blueprint(student_data_modal_api_bp)
    app.register_blueprint(promoted_student_modal_api_bp)

    app.register_blueprint(final_promotion_api_bp)
    app.register_blueprint(final_update_api_bp)
    app.register_blueprint(final_depromotion_api_bp)
    app.register_blueprint(generate_watsapp_message_api_bp)

    app.register_blueprint(tc_bp)
    app.register_blueprint(tc_student_list_api_bp)
    app.register_blueprint(generate_tc_form_api_bp)

    app.register_blueprint(question_paper_bp)
    app.register_blueprint(question_paper_api_bp)


    app.register_blueprint(temp_page_bp)
    app.register_blueprint(fill_colums_api_bp)


    app.register_blueprint(RTE_students_bp)
    app.register_blueprint(staff_bp)
    