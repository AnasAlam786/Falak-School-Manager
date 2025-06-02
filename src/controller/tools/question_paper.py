# src/controller/tools/question_paper.py

from flask import session, render_template, redirect, url_for, Blueprint
from ..auth.login_required import login_required


question_paper_bp = Blueprint( 'question_paper_bp',   __name__)

@question_paper_bp.route('/question_paper', methods=["GET"])
@login_required
def question_paper():
    if 'email' not in session:
        return redirect(url_for('login_bp.login'))


    papers = None
    if 'papers' in session:
        papers = session['papers']
    
    return render_template('paper.html', index=1, papers=papers)
