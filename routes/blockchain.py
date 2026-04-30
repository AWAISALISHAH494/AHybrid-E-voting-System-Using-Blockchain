from flask import Blueprint, jsonify
from flask_login import login_required
from services.result_service import ResultService

blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/api/blockchain')


@blockchain_bp.route('/verify/<int:election_id>')
@login_required
def verify(election_id):
    result = ResultService.verify_on_blockchain(election_id)
    return jsonify(result)
