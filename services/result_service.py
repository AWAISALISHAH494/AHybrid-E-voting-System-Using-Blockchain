import json
import requests
from flask import current_app
from models import db
from models.election import Election
from services.vote_service import VoteService
from services.encryption import EncryptionService


class ResultService:
    @staticmethod
    def combine_results(election_id: int) -> dict:
        return VoteService.count_votes(election_id)

    @staticmethod
    def generate_result_hash(results: dict) -> str:
        result_string = json.dumps(results, sort_keys=True)
        return EncryptionService.hash_sha256(result_string)

    @staticmethod
    def finalize_election(election_id: int) -> dict:
        election = Election.query.get(election_id)
        if not election:
            return {'success': False, 'message': 'Election not found.'}
        if election.status == 'finalized':
            return {'success': False, 'message': 'Election is already finalized.'}

        results = ResultService.combine_results(election_id)
        result_hash = ResultService.generate_result_hash(results)

        blockchain_url = current_app.config['BLOCKCHAIN_SERVICE_URL']
        try:
            response = requests.post(
                f'{blockchain_url}/api/store-result',
                json={
                    'electionId': str(election_id),
                    'resultHash': result_hash
                },
                timeout=30
            )
            blockchain_data = response.json()

            if not blockchain_data.get('success'):
                return {
                    'success': False,
                    'message': f'Blockchain error: {blockchain_data.get("error", "Unknown error")}'
                }

            tx_hash = blockchain_data.get('transactionHash', '')

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to blockchain service. Ensure Node.js server and Ganache are running.'
            }
        except Exception as e:
            return {'success': False, 'message': f'Blockchain error: {str(e)}'}

        election.status = 'finalized'
        election.result_hash = result_hash
        election.blockchain_tx_hash = tx_hash
        db.session.commit()

        return {
            'success': True,
            'message': 'Election finalized and results stored on blockchain!',
            'result_hash': result_hash,
            'transaction_hash': tx_hash,
            'results': results
        }

    @staticmethod
    def verify_on_blockchain(election_id: int) -> dict:
        election = Election.query.get(election_id)
        if not election:
            return {'success': False, 'message': 'Election not found.'}
        if not election.result_hash:
            return {'success': False, 'message': 'Election has not been finalized yet.'}

        results = ResultService.combine_results(election_id)
        current_hash = ResultService.generate_result_hash(results)

        blockchain_url = current_app.config['BLOCKCHAIN_SERVICE_URL']
        try:
            response = requests.get(
                f'{blockchain_url}/api/verify-result/{election_id}',
                params={'resultHash': current_hash},
                timeout=30
            )
            blockchain_data = response.json()

            blockchain_hash = blockchain_data.get('storedHash', '')
            is_verified = blockchain_data.get('isVerified', False)
            is_tampered = (current_hash != election.result_hash)

            return {
                'success': True,
                'stored_hash': election.result_hash,
                'current_hash': current_hash,
                'blockchain_hash': blockchain_hash,
                'is_verified': is_verified,
                'is_tampered': is_tampered,
                'transaction_hash': election.blockchain_tx_hash
            }

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to blockchain service. Ensure Node.js server and Ganache are running.'
            }
        except Exception as e:
            return {'success': False, 'message': f'Verification error: {str(e)}'}
