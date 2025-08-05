from flask import request, jsonify, render_template
from functools import wraps
from .has_permission import has_permission

def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):

            if not has_permission(permission_name):

                if request.blueprint and 'api' in request.blueprint.lower():
                    return jsonify({"message": "You do not have permission"}), 403
                else:
                    return render_template("permission_denied.html"), 403

            return f(*args, **kwargs)
        return wrapped
    return decorator
