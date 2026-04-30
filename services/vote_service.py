from models import db
from models.vote import Vote
from models.election import Election
from models.candidate import Candidate
from services.encryption import EncryptionService
from flask import current_app
import uuid
from datetime import datetime


class VoteService:
    @staticmethod
    def get_encryption_service() -> EncryptionService:
        key = current_app.config['ENCRYPTION_KEY']
        return EncryptionService(key)

    @staticmethod
    def cast_vote(election_id: int, candidate_id: int, voter_cnic: str) -> dict:
        enc = VoteService.get_encryption_service()

        election = Election.query.get(election_id)
        if not election:
            return {'success': False, 'message': 'Election not found.'}
        if election.status != 'active':
            return {'success': False, 'message': 'Election is not currently active.'}

        candidate = Candidate.query.filter_by(id=candidate_id, election_id=election_id).first()
        if not candidate:
            return {'success': False, 'message': 'Invalid candidate for this election.'}

        voter_hash = enc.generate_voter_hash(voter_cnic, election_id)
        existing_vote = Vote.query.filter_by(
            election_id=election_id,
            voter_hash=voter_hash
        ).first()
        if existing_vote:
            return {'success': False, 'message': 'You have already voted in this election.'}

        encrypted_vote = enc.encrypt(str(candidate_id))

        receipt_raw = f"{uuid.uuid4().hex}:{datetime.utcnow().isoformat()}:{election_id}"
        receipt_hash = enc.hash_sha256(receipt_raw)[:16].upper()

        vote = Vote(
            election_id=election_id,
            encrypted_vote=encrypted_vote,
            vote_type='electronic',
            voter_hash=voter_hash,
            receipt_hash=receipt_hash
        )
        db.session.add(vote)
        db.session.commit()

        return {
            'success': True,
            'message': 'Your vote has been cast successfully!',
            'receipt': receipt_hash
        }

    @staticmethod
    def add_manual_vote(election_id: int, candidate_id: int, manual_id: str) -> dict:
        enc = VoteService.get_encryption_service()

        election = Election.query.get(election_id)
        if not election:
            return {'success': False, 'message': 'Election not found.'}
        if election.status == 'finalized':
            return {'success': False, 'message': 'Election is already finalized.'}

        candidate = Candidate.query.filter_by(id=candidate_id, election_id=election_id).first()
        if not candidate:
            return {'success': False, 'message': 'Invalid candidate for this election.'}

        voter_hash = enc.hash_sha256(f"manual:{manual_id}:{election_id}")

        existing = Vote.query.filter_by(
            election_id=election_id,
            voter_hash=voter_hash
        ).first()
        if existing:
            return {'success': False, 'message': 'This manual ballot has already been entered.'}

        encrypted_vote = enc.encrypt(str(candidate_id))

        vote = Vote(
            election_id=election_id,
            encrypted_vote=encrypted_vote,
            vote_type='manual',
            voter_hash=voter_hash
        )
        db.session.add(vote)
        db.session.commit()

        return {'success': True, 'message': 'Manual vote added successfully.'}

    @staticmethod
    def count_votes(election_id: int) -> dict:
        enc = VoteService.get_encryption_service()

        votes = Vote.query.filter_by(election_id=election_id).all()
        candidates = Candidate.query.filter_by(election_id=election_id).all()

        counts = {}
        for c in candidates:
            counts[c.id] = {
                'candidate_id': c.id,
                'name': c.name,
                'party': c.party,
                'electronic': 0,
                'manual': 0,
                'total': 0
            }

        for vote in votes:
            try:
                decrypted_candidate_id = int(enc.decrypt(vote.encrypted_vote))
                if decrypted_candidate_id in counts:
                    counts[decrypted_candidate_id][vote.vote_type] += 1
                    counts[decrypted_candidate_id]['total'] += 1
            except Exception:
                continue

        return {
            'election_id': election_id,
            'total_votes': len(votes),
            'results': list(counts.values())
        }

    @staticmethod
    def verify_receipt(receipt_code: str) -> dict:
        receipt_code = receipt_code.strip().upper()
        vote = Vote.query.filter_by(receipt_hash=receipt_code).first()

        if not vote:
            return {'success': False, 'message': 'Invalid receipt code. Please check and try again.'}

        enc = VoteService.get_encryption_service()

        try:
            decrypted_candidate_id = int(enc.decrypt(vote.encrypted_vote))
            candidate = Candidate.query.get(decrypted_candidate_id)
            election = Election.query.get(vote.election_id)

            is_intact = candidate is not None

            return {
                'success': True,
                'is_intact': is_intact,
                'receipt': receipt_code,
                'election_title': election.title if election else 'Unknown',
                'election_status': election.status if election else 'unknown',
                'candidate_name': candidate.name if candidate else 'Unknown',
                'candidate_party': candidate.party if candidate else '',
                'vote_type': vote.vote_type,
                'timestamp': vote.timestamp.strftime('%b %d, %Y at %I:%M %p'),
                'blockchain_verified': bool(election.blockchain_tx_hash) if election else False
            }
        except Exception:
            return {
                'success': True,
                'is_intact': False,
                'receipt': receipt_code,
                'message': 'Vote data appears to be corrupted or tampered with.'
            }
