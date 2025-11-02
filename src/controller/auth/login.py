# src/controller/auth.py

from flask import render_template, session, url_for, redirect, Blueprint, request, jsonify

from cryptography.fernet import Fernet

from src.model.Schools import Schools
from src.model.Sessions import Sessions
from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles

from ..permissions.get_permissions import get_permissions

import os
from src import r


login_bp = Blueprint( 'login_bp',   __name__)
FERNET_KEY = os.environ.get('FERNET_KEY')

@login_bp.route('/login', methods=["GET", "POST"])
def login():


    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = ( TeachersLogin.query .join(Roles, Roles.id == TeachersLogin.role_id) .filter(TeachersLogin.email == email) .first() )
        if not user:
            return render_template('login.html', error="No user found with this email")

        decrypted_password = Fernet(FERNET_KEY).decrypt(user.Password).decode()
        if decrypted_password != password:
            return render_template('login.html', error="Wrong email or password")

        if not save_sessions(user=user):
            return render_template('login.html', error="Something didn't go well, try again!")

        return redirect(url_for('student_list_bp.student_list'))

    required_keys = ["user_id","role","school_id","session_id","current_running_session","permissions","school_name", "permission_no", "logo", "role"]
    for key in required_keys:
        if key not in session:
            session.clear()
            return render_template('login.html', error=None)

    return redirect(url_for('student_list_bp.student_list'))
    

    



def save_sessions(user = None, user_id = None):

    print("Save session called")

    if not user and not user_id:
        return False

    if not user:
        user = ( TeachersLogin.query .join(Roles, Roles.id == TeachersLogin.role_id).filter(TeachersLogin.id == user_id) .first() )
    if not user:
        return False

    school = Schools.query.filter_by(id=user.school_id).first()

    if not school:
        return False

    sessions = Sessions.query.with_entities(
        Sessions.id, 
        Sessions.session, 
        Sessions.current_session
    ).filter(
        Sessions.id >= school.school_legacy_id
    ).order_by(
        Sessions.session.desc()
    ).all()
    
    session.permanent = True

    
    
    session["role"] = user.role_data.role_name
    session["all_sessions"] = [int(sessi.session) for sessi in sessions]
    session["school_name"] = school.School_Name
    session["user_id"] = user.id
    session['logo'] = school.Logo
    session["email"] = user.email
    session["school_id"] = user.school_id
    session["permission_no"] = user.permission_number

    permissions = get_permissions(user.id, user.role_id)
    session["permissions"] = permissions

    current_running_session = None
    for s in sessions:
        if s.current_session:
            current_running_session = s.id
            break

    session["session_id"]      = current_running_session
    session['current_running_session'] = current_running_session  # can be changed if user switches  to another session


    r.set(session['user_id'], user.permission_number)

    return True