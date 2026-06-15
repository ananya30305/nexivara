import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here' # Change this later
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///instance/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
import os

class Config:
    SECRET_KEY = 'your-secret-key-here' # Change this later
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
>>>>>>> cf9b8872db064c314bb505cd2112a4c2b78213a2
