# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.election import Election
from models.candidate import Candidate
from models.vote import Vote
from models.user import User
from services.vote_service import VoteService
from services.result_service import ResultService
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_voters = User.query.filter_by(role='voter').count()
    total_elections = Election.query.count()
    active_elections = Election.query.filter_by(status='active').count()
    total_votes = Vote.query.count()
    recent_elections = Election.query.order_by(Election.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           total_voters=total_voters,
                           total_elections=total_elections,
                           active_elections=active_elections,
                           total_votes=total_votes,
                           recent_elections=recent_elections)


@admin_bp.route('/elections')
@login_required
@admin_required
def elections():
    all_elections = Election.query.order_by(Election.created_at.desc()).all()
    return render_template('admin/elections.html', elections=all_elections)


@admin_bp.route('/elections/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_election():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status', 'pending')

        if not title or not start_date or not end_date:
            flash('Title, start date, and end date are required.', 'error')
            return render_template('admin/create_election.html')

        election = Election(
            title=title,
            description=description,
            start_date=datetime.strptime(start_date, '%Y-%m-%dT%H:%M'),
            end_date=datetime.strptime(end_date, '%Y-%m-%dT%H:%M'),
            status=status,
            created_by=current_user.id
        )
        db.session.add(election)
        db.session.commit()

        flash('Election created successfully!', 'success')
        return redirect(url_for('admin.elections'))

    return render_template('admin/create_election.html')


@admin_bp.route('/elections/<int:election_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_election(election_id):
    election = Election.query.get_or_404(election_id)

    if request.method == 'POST':
        election.title = request.form.get('title', '').strip()
        election.description = request.form.get('description', '').strip()
        election.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%dT%H:%M')
        election.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%dT%H:%M')
        election.status = request.form.get('status', election.status)
        db.session.commit()

        flash('Election updated successfully!', 'success')
        return redirect(url_for('admin.elections'))

    return render_template('admin/edit_election.html', election=election)


@admin_bp.route('/elections/<int:election_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_election(election_id):
    election = Election.query.get_or_404(election_id)
    if election.status == 'finalized':
        flash('Cannot delete a finalized election.', 'error')
        return redirect(url_for('admin.elections'))

    db.session.delete(election)
    db.session.commit()
    flash('Election deleted successfully.', 'success')
    return redirect(url_for('admin.elections'))


@admin_bp.route('/elections/<int:election_id>/candidates')
@login_required
@admin_required
def candidates(election_id):
    election = Election.query.get_or_404(election_id)
    all_candidates = Candidate.query.filter_by(election_id=election_id).all()
    return render_template('admin/candidates.html',
                           election=election,
                           candidates=all_candidates)


@admin_bp.route('/elections/<int:election_id>/candidates/add', methods=['POST'])
@login_required
@admin_required
def add_candidate(election_id):
    election = Election.query.get_or_404(election_id)

    name = request.form.get('name', '').strip()
    party = request.form.get('party', '').strip()
    symbol = request.form.get('symbol', '').strip()

    if not name:
        flash('Candidate name is required.', 'error')
        return redirect(url_for('admin.candidates', election_id=election_id))

    candidate = Candidate(
        name=name,
        party=party,
        symbol=symbol,
        election_id=election_id
    )
    db.session.add(candidate)
    db.session.commit()

    flash(f'Candidate "{name}" added successfully!', 'success')
    return redirect(url_for('admin.candidates', election_id=election_id))


@admin_bp.route('/candidates/<int:candidate_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_candidate(candidate_id):
    candidate = Candidate.query.get_or_404(candidate_id)
    election_id = candidate.election_id
    db.session.delete(candidate)
    db.session.commit()
    flash('Candidate removed.', 'success')
    return redirect(url_for('admin.candidates', election_id=election_id))


@admin_bp.route('/elections/<int:election_id>/manual-vote', methods=['GET', 'POST'])
@login_required
@admin_required
def manual_vote(election_id):
    election = Election.query.get_or_404(election_id)
    candidates_list = Candidate.query.filter_by(election_id=election_id).all()

    if request.method == 'POST':
        candidate_id = request.form.get('candidate_id', type=int)
        ballot_id = request.form.get('ballot_id', '').strip()

        if not candidate_id or not ballot_id:
            flash('Candidate and ballot ID are required.', 'error')
            return render_template('admin/manual_vote.html',
                                   election=election,
                                   candidates=candidates_list)

        result = VoteService.add_manual_vote(election_id, candidate_id, ballot_id)
        flash(result['message'], 'success' if result['success'] else 'error')

    return render_template('admin/manual_vote.html',
                           election=election,
                           candidates=candidates_list)


@admin_bp.route('/elections/<int:election_id>/results')
@login_required
@admin_required
def election_results(election_id):
    election = Election.query.get_or_404(election_id)
    vote_counts = VoteService.count_votes(election_id)
    return render_template('admin/results.html',
                           election=election,
                           results=vote_counts)


@admin_bp.route('/elections/<int:election_id>/finalize', methods=['POST'])
@login_required
@admin_required
def finalize_election(election_id):
    result = ResultService.finalize_election(election_id)
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')
    return redirect(url_for('admin.election_results', election_id=election_id))


@admin_bp.route('/elections/<int:election_id>/verify')
@login_required
@admin_required
def verify_blockchain(election_id):
    election = Election.query.get_or_404(election_id)
    verification = ResultService.verify_on_blockchain(election_id)
    return render_template('admin/blockchain.html',
                           election=election,
                           verification=verification)


@admin_bp.route('/voters')
@login_required
@admin_required
def voters():
    all_voters = User.query.filter_by(role='voter').order_by(User.created_at.desc()).all()
    return render_template('admin/voters.html', voters=all_voters)

# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================