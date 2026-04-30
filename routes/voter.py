from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.election import Election
from models.candidate import Candidate
from services.vote_service import VoteService
from datetime import datetime

voter_bp = Blueprint('voter', __name__)


def voter_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'voter':
            flash('Access denied. Voter account required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@voter_bp.route('/dashboard')
@login_required
@voter_required
def dashboard():
    active_elections = Election.query.filter(
        Election.status == 'active'
    ).all()
    completed_elections = Election.query.filter(
        Election.status.in_(['completed', 'finalized'])
    ).all()
    return render_template('voter/dashboard.html',
                           active_elections=active_elections,
                           completed_elections=completed_elections)


@voter_bp.route('/vote/<int:election_id>', methods=['GET'])
@login_required
@voter_required
def vote_page(election_id):
    election = Election.query.get_or_404(election_id)
    candidates = Candidate.query.filter_by(election_id=election_id).all()

    if election.status != 'active':
        flash('This election is not currently active.', 'error')
        return redirect(url_for('voter.dashboard'))

    return render_template('voter/vote.html',
                           election=election,
                           candidates=candidates)


@voter_bp.route('/vote/<int:election_id>', methods=['POST'])
@login_required
@voter_required
def cast_vote(election_id):
    candidate_id = request.form.get('candidate_id', type=int)
    if not candidate_id:
        flash('Please select a candidate.', 'error')
        return redirect(url_for('voter.vote_page', election_id=election_id))

    result = VoteService.cast_vote(election_id, candidate_id, current_user.cnic)

    if result['success']:
        flash(result['message'], 'success')
        return render_template('voter/vote_success.html',
                               election=Election.query.get(election_id),
                               receipt=result.get('receipt'))
    else:
        flash(result['message'], 'error')
        return redirect(url_for('voter.vote_page', election_id=election_id))


@voter_bp.route('/results/<int:election_id>')
@login_required
@voter_required
def results(election_id):
    election = Election.query.get_or_404(election_id)
    if election.status not in ['completed', 'finalized']:
        flash('Results are not yet available for this election.', 'info')
        return redirect(url_for('voter.dashboard'))

    vote_counts = VoteService.count_votes(election_id)
    return render_template('voter/results.html',
                           election=election,
                           results=vote_counts)


@voter_bp.route('/verify', methods=['GET', 'POST'])
@login_required
@voter_required
def verify_vote():
    verification = None
    if request.method == 'POST':
        receipt_code = request.form.get('receipt_code', '')
        if receipt_code:
            verification = VoteService.verify_receipt(receipt_code)
        else:
            flash('Please enter a receipt code.', 'error')
    return render_template('voter/verify.html', verification=verification)
