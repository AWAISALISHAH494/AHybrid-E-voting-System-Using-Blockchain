from models import db


class Candidate(db.Model):
    __tablename__ = 'candidates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    party = db.Column(db.String(100), nullable=True)
    symbol = db.Column(db.String(50), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    election_id = db.Column(db.Integer, db.ForeignKey('elections.id'), nullable=False)

    def __repr__(self):
        return f'<Candidate {self.name} ({self.party})>'
