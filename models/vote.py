# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================

from models import db
from datetime import datetime


class Vote(db.Model):
    __tablename__ = 'votes'

    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)
    encrypted_vote = db.Column(db.LargeBinary, nullable=False)
    vote_type = db.Column(db.String(15), nullable=False, default='electronic')
    voter_hash = db.Column(db.String(256), nullable=False)
    receipt_hash = db.Column(db.String(256), unique=True, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Vote {self.id} [{self.vote_type}] Election:{self.election_id}>'

# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================