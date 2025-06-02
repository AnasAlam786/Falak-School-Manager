from flask import session, jsonify, Blueprint, request, redirect, url_for
from src.model import Sessions
from ..auth.login_required import login_required


change_session_bp = Blueprint( 'change_session_bp',   __name__)


@change_session_bp.route('/change_session', methods=["POST"])
@login_required
def change_session():
    
    data = request.json
    current_session = data.get('year')
    

    # Validate input
    if not current_session or not str(current_session).isdigit():
        return jsonify({"message": "Invalid session ID"}), 400

    current_session = int(current_session)

    # Fetch all sessions from DB
    sessions_data = Sessions.query.with_entities(
        Sessions.id, Sessions.session, Sessions.current_session
    ).order_by(Sessions.session.asc()).all()

    # Store all session years in the session
    session["all_sessions"] = [s.session for s in sessions_data]

    # Find and set the requested session
    for s in sessions_data:
        if current_session == s.session:
            session["current_session"] = s.session
            session["session_id"] = s.id
            return jsonify({"message": f"Session Updated to {s.session}"}), 200

    

    return jsonify({"message": "Session not found"}), 404

    