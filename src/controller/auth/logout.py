from flask import session, url_for, redirect, Blueprint

logout_bp = Blueprint( 'logout_bp',   __name__)


@logout_bp.route('/logout', methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for('login_bp.login'))