from flask import session, redirect, url_for, request, jsonify
from functools import wraps
from src import r
from .login import save_sessions
# import time


def login_required(f):
    @wraps(f)
    
    def decorated_function(*args, **kwargs):
        # start_time = time.time()  # start timer

        required_keys = ["user_id","role","school_id","session_id","current_running_session","permissions","school_name", "permission_no"]
        for key in required_keys:
            if key not in session:
                if request.blueprint and 'api' in request.blueprint.lower():
                    return jsonify({"message": "You have to login first!"}), 403
                else:
                    return redirect(url_for('login_bp.login'))
            
        redis_permission_no = r.get(session['user_id'])
        session_permission_no = session["permission_no"]

        if not redis_permission_no:
            save_sessions(user_id=session['user_id'])

        if int(session_permission_no) != int(redis_permission_no):
            save_sessions(user_id=session['user_id'])

        # end_time = time.time()  # end timer
        # print(f"login_required decorator took {end_time - start_time:.6f} seconds to run")

        return f(*args, **kwargs)
    return decorated_function