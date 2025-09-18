from flask import session, jsonify, Blueprint, request, redirect, url_for
from src.controller.permissions.permission_required import permission_required
from src.model import Sessions
from src.controller.auth.login_required import login_required



change_session_bp = Blueprint( 'change_session_bp',   __name__)


@change_session_bp.route('/change_session', methods=["POST"])
@login_required
@permission_required('change_session')
def change_session():
    
    data = request.json
    selected_session = data.get('year')

    # Validate input
    if not selected_session or not str(selected_session).isdigit():
        return jsonify({"message": "Invalid session ID"}), 400

    selected_session = int(selected_session)

    # Fetch all sessions from DB
    sessions_data = Sessions.query.with_entities(
        Sessions.id, Sessions.session, Sessions.current_session
    ).order_by(Sessions.session.desc()).all()

    # Store all session years in the session
    session["all_sessions"] = [s.id for s in sessions_data]

    # Find and set the requested session
    for s in sessions_data:
        if selected_session == s.id:
            session["session_id"] = s.id
            return jsonify({"message": f"Session Updated to {s.id}-{int(s.id)+1}"}), 200
        if s.current_session:
            # current running session found
           session["current_running_session"] = s.id

    print(session)

    

    return jsonify({"message": "Session not found"}), 404

    