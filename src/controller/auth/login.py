# src/controller/auth.py

from flask import render_template, session, url_for, redirect, Blueprint, request, make_response

from cryptography.fernet import Fernet

from src.model.Schools import Schools
from src.model.Sessions import Sessions
from src.model.TeachersLogin import TeachersLogin
from src.model.Roles import Roles

from ..permissions.get_permissions import get_permissions

import os


login_bp = Blueprint( 'login_bp',   __name__)
FERNET_KEY = os.environ.get('FERNET_KEY')

@login_bp.route('/login', methods=["GET", "POST"])
def login():
    error=None
    
    if "user_id" in session:
        return redirect(url_for('student_list_bp.student_list'))

    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        cipher_suite = Fernet(FERNET_KEY)
        

        user = (
            TeachersLogin.query
                .join(Roles, Roles.id == TeachersLogin.role_id)
                .filter(TeachersLogin.email == email)
                .first()
        )

        decrypted_password = cipher_suite.decrypt(user.Password).decode()

        if user and (decrypted_password == password):


            school = Schools.query.filter_by(id=user.school_id).first()
            sessions = Sessions.query.with_entities(Sessions.id, Sessions.session, Sessions.current_session
                                                    ).order_by(Sessions.session.asc()).all()
            
            session.permanent = True
        
            
            session["role"] = user.role_data.role_name
            session["all_sessions"] = [sessi.session for sessi in sessions]
            session["school_name"] = school.School_Name
            session["user_id"] = user.id
            session["logo"] = school.Logo
            session["email"] = user.email
            session["school_id"] = user.school_id

            permissions = get_permissions(user.id)
            session["permissions"] = permissions


            # pick out the one where current_session==True (or None if none)
            session_id, current_session = next(
                ((s.id, s.session) for s in sessions if s.current_session),
                (None, None)
            )

            session["session_id"]      = session_id
            session["current_session"] = current_session

            return redirect(url_for('student_list_bp.student_list'))
               
        else: error="Wrong email or password"
                

    return render_template('login.html', error=error)
