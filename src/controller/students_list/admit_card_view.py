from flask import Blueprint, render_template, session

from src.controller.auth.login_required import login_required
from src.controller.permissions.permission_required import permission_required
from src.model import ClassData
from src import db

admit_card_view_bp = Blueprint('admit_card_view_bp', __name__)


@admit_card_view_bp.route('/admit_and_schema', methods=['GET'])
@login_required
@permission_required('admission')
def admit_card_preview():
    """Render the admit card preview page and pass class list for the current school."""
    school_id = session.get('school_id')
    if not school_id:
        return "Missing school context", 400

    classes = db.session.query(ClassData).filter_by(school_id=school_id).order_by(ClassData.display_order).all()
    current_session_id = session.get('session_id')

    return render_template('admit_card/admit_card.html', classes=classes, current_session_id=current_session_id)
