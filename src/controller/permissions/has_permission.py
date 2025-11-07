from flask import session

def has_permission(permission_name):

    if session['role'].lower() in ['manager', 'admin']:
        return True
    return permission_name in session.get('permissions', [])