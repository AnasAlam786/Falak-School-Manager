from flask import session, redirect, url_for, request, jsonify
from functools import wraps


def login_required(f):
    @wraps(f)
    
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.blueprint and 'api' in request.blueprint.lower():
                return jsonify({"message": "You have to login first!"}), 403
            else:
                return redirect(url_for('login_bp.login'))
        return f(*args, **kwargs)
    return decorated_function