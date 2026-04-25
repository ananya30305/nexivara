import os

class Config:
    SECRET_KEY = 'your-secret-key-here' # Change this later
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
