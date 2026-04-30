from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import User
from models.election import Election
from models.candidate import Candidate
from models.vote import Vote
