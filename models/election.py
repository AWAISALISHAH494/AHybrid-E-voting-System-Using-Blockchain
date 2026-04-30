from models import db
from datetime import datetime


class Election(db.Model):
    __tablename__ = 'elections'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')
    blockchain_tx_hash = db.Column(db.String(256), nullable=True)
    result_hash = db.Column(db.String(256), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    candidates = db.relationship('Candidate', backref='election', lazy=True, cascade='all, delete-orphan')
    votes = db.relationship('Vote', backref='election', lazy=True, cascade='all, delete-orphan')

    @property
    def is_active(self):
        now = datetime.utcnow()
        return self.status == 'active' and self.start_date <= now <= self.end_date

    def __repr__(self):
        return f'<Election {self.title} [{self.status}]>'
