from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    degree = db.Column(db.String(20)) # BSc or BCA
    cgpa = db.Column(db.Float)
    financial_stability = db.Column(db.Integer) # 1-10
    focus_level = db.Column(db.Integer) # 1-10
    urgency = db.Column(db.Integer) # 1-10
    district = db.Column(db.String(100))
    skills = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
degree = db.Column(db.String(50))