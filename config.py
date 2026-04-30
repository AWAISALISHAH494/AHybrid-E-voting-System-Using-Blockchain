# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hybrid-evoting-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///evoting.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'HybridEVotingAES256SecretKey2026')
    BLOCKCHAIN_SERVICE_URL = os.environ.get('BLOCKCHAIN_SERVICE_URL', 'http://localhost:3001')
    GANACHE_URL = os.environ.get('GANACHE_URL', 'http://127.0.0.1:7545')
# ==========================================
# Author: Awais Ali Shah
# License: All Rights Reserved
# Unauthorized use or submission is prohibited
# ==========================================