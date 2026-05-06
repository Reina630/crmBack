import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:amina@localhost:5432/leads_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt_dev_secret_key')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 heures
    JWT_IDENTITY_CLAIM = 'sub'
    JWT_ALGORITHM = 'HS256'
