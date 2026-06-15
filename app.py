import email

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from collections import Counter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexivara-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
import re

def is_valid_gmail(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@gmail\.com$'
    return re.match(pattern, email)

def is_valid_username(username):

    pattern = r'^(?=.*[a-zA-Z])[a-zA-Z0-9._]{3,30}$'

    return re.match(pattern, username)
def is_strong_password(password):
    """
    Password must contain:
    - 8 characters
    - uppercase
    - lowercase
    - number
    - special character
    """

    pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

    return re.match(pattern, password)

# --------------------------
# DATABASE MODELS
# --------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(200),
        nullable=False
    )

    reviews = db.relationship(
        'Review',
        backref='user',
        lazy=True,
        cascade='all, delete'
    )


class UserInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id')
    )

    cgpa = db.Column(db.Float, nullable=False)
    skills = db.Column(db.String(500), nullable=False)
    focus_level = db.Column(db.Integer, nullable=False)
    financial_stability = db.Column(db.Integer, nullable=False)
    district = db.Column(db.String(100), nullable=False)
    preferred_location = db.Column(db.String(100))
    degree = db.Column(db.String(20), nullable=False)


class Review(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    rating = db.Column(
        db.Integer,
        nullable=False
    )

    review = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )
with app.app_context():
    db.create_all()

# --------------------------
# SKILL FUNCTIONS
# --------------------------

def normalize_skills(text):
    if not text:
        return []
    return [s.strip().lower() for s in text.split(',') if s.strip()]

def has_strong(skills):
    strong = ['python','data','sql','ai','ml','cloud','sap']
    return any(k in skill for skill in skills for k in strong)

def is_low_skill(skills):
    return len(skills) < 2

# --------------------------
# CAREER FUNCTIONS
# --------------------------

def suggest_skills(user_skills):
    recommended = ['python','sql','data structures','cloud','communication','aptitude']
    return [skill for skill in recommended if skill not in user_skills]

def get_career_info(career):
    info = {
        "MSc": "Postgraduate degree focused on advanced subject knowledge.",
        "MCA": "Professional IT degree focused on software and development.",
        "MBA": "Management degree for leadership and business careers.",
        "Job": "Start earning and gain real-world industry experience.",
        "Internship": "Gain practical exposure and build your resume.",
        "Courses": "Short-term skill programs to improve employability.",
        "Government Job": "Secure job through competitive exams."
    }
    return info.get(career, "")

def get_roadmap(career):
    roadmap = {
        "MSc": ["Prepare entrance exams","Choose specialization","Apply colleges","Build projects"],
        "MCA": ["Prepare entrance","Improve coding","Apply colleges","Do internships"],
        "MBA": ["Prepare CAT/MAT","Improve aptitude","Apply B-schools","Focus management"],
        "Job": ["Build resume","Practice coding","Apply jobs","Prepare interviews"],
        "Internship": ["Search internships","Build projects","Improve skills","Gain experience"],
        "Courses": ["Join certification","Learn skills","Build projects","Get certified"],
        "Government Job": ["Prepare exams","Study daily","Mock tests","Stay consistent"]
    }
    return roadmap.get(career, [])

# --------------------------
# PREDICTION LOGIC
# --------------------------

def choose_prediction(cgpa, skills, focus, financial):

    if financial <= 4:
        if has_strong(skills):
            return "Job"
        elif focus >= 6:
            return "Internship"
        else:
            return "Courses"

    if is_low_skill(skills):
        return "Courses"

    if cgpa >= 8 and financial >= 6:
        return "MSc"

    if 7 <= cgpa < 8 and financial >= 6:
        return "MCA"

    if has_strong(skills) and focus >= 7:
        return "Job"

    if focus >= 5:
        return "Internship"

    return "Government Job"

# --------------------------
# GOOGLE QUERY
# --------------------------

def build_query(result, skills, location, degree):
    skills = skills if skills else "freshers"
    location = location if location else "India"

    # 🔥 Convert degree into proper text
    if degree == "BSc":
        degree_text = "BSc graduates"
    elif degree == "BCA":
        degree_text = "BCA graduates"
    else:
        degree_text = "graduates"

    if result == "Job":
        return f"Jobs for {degree_text} with {skills} in {location}"

    elif result == "Internship":
        return f"Internships for {degree_text} in {location}"

    elif result == "Courses":
        return f"Best certification courses after {degree_text} in {location}"

    elif result == "MSc":
        return f"Top MSc colleges for {degree_text} in {location}"

    elif result == "MCA":
        return f"Top MCA colleges for {degree_text} in {location}"

    else:
        return f"Government jobs for {degree_text} in {location}"

# --------------------------
# ROUTES
# --------------------------

@app.route('/')
def index():
    return render_template('index.html')

# ✅ FIXED LOADING ROUTE
@app.route('/loading', endpoint='loading')
def loading():
    return render_template('loading.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():

    username = request.form.get('username', '').strip()

    if not is_valid_username(username):
        return render_template(
            'login.html',
            error="❌ Invalid username format"
        )

    password = request.form.get('password', '').strip()

    if not username or not password:
        return render_template('login.html', error="❌ Enter all fields")

    user = User.query.filter_by(username=username).first()

    if not user:
        return render_template('login.html', error="❌ User not found. Please sign up")

    if not check_password_hash(user.password, password):
        return render_template('login.html', error="❌ Wrong Password")

    session['user_id'] = user.id
    return redirect('/form')
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login-page')

@app.route('/form')
def form():
    if 'user_id' not in session:
        return redirect('/login-page')

    existing = UserInput.query.filter_by(user_id=session['user_id']).first()

    selected_skills = []
    if existing and existing.skills:
        selected_skills = [s.strip() for s in existing.skills.split(",")]

    return render_template(
        'form.html',
        existing=existing,
        selected_skills=selected_skills
    
    )
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if request.method == 'POST':

        username = request.form.get('username').strip()

        if not is_valid_username(username):
            return render_template(
                'signup.html',
                error="❌ Username must be 3-30 characters and contain only letters, numbers, underscore (_) or dot (.)"
            )

        email = request.form.get('email').strip().lower()

        password = request.form.get('password').strip()

        confirm_password = request.form.get('confirm_password').strip()

        # EMPTY CHECK
        if not username or not email or not password:
            return render_template(
                'signup.html',
                error="❌ Fill all fields"
            )

        if not is_valid_gmail(email):
            return render_template(
                'signup.html',
                error="❌ Only Gmail accounts allowed (@gmail.com)"
            )

        if password != confirm_password:
            return render_template(
                'signup.html',
                error="❌ Passwords do not match"
            )

        if not is_strong_password(password):
            return render_template(
                'signup.html',
                error="❌ Password must contain uppercase, lowercase, number and special character"
            )

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template(
                'signup.html',
                error="❌ Username already exists"
            )

        existing_email = User.query.filter_by(email=email).first()

        if existing_email:
            return render_template(
                'signup.html',
                error="❌ Email already registered"
            )

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login-page')

    return render_template('signup.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        username = request.form.get('username', '').strip()

        if not is_valid_username(username):
            return render_template(
                'forgot_password.html',
                error="❌ Invalid username format"
            )

        email = request.form.get('email', '').strip().lower()

        new_password = request.form.get('new_password', '').strip()

        confirm_password = request.form.get('confirm_password', '').strip()

        user = User.query.filter_by(
            username=username,
            email=email
        ).first()

        if not user:
            return render_template(
                'forgot_password.html',
                error="❌ Invalid username or email"
            )

        if new_password != confirm_password:
            return render_template(
                'forgot_password.html',
                error="❌ Passwords do not match"
            )

        if not is_strong_password(new_password):
            return render_template(
                'forgot_password.html',
                error="❌ Weak password"
            )

        user.password = generate_password_hash(new_password)

        db.session.commit()

        return redirect('/login-page')

    return render_template('forgot_password.html')
# RESULT
# --------------------------

@app.route('/result', methods=['POST'])
def result():

    if 'user_id' not in session:
        return redirect('/login-page')

    cgpa = float(request.form.get('cgpa', 0))
    skills_list = request.form.getlist('skills[]')
    skills_text = ",".join(skills_list)

    focus = int(request.form.get('focus_level', 1))
    financial = int(request.form.get('financial_stability', 1))
    location = request.form.get('preferred_location', 'India')
    district = request.form.get('district', '')
    degree = request.form.get('degree', '')

    skills = normalize_skills(skills_text)

    existing = UserInput.query.filter_by(
        user_id=session['user_id']
    ).first()

    if existing:

        existing.cgpa = cgpa
        existing.skills = skills_text
        existing.focus_level = focus
        existing.financial_stability = financial
        existing.district = district
        existing.preferred_location = location
        existing.degree = degree

    else:

        db.session.add(
            UserInput(
                user_id=session['user_id'],
                cgpa=cgpa,
                skills=skills_text,
                focus_level=focus,
                financial_stability=financial,
                district=district,
                preferred_location=location,
                degree=degree
            )
        )

    db.session.commit()

    prediction = choose_prediction(
        cgpa,
        skills,
        focus,
        financial
    )

    scores = {
        "Higher Studies": int(cgpa * 10),
        "Job": 80 if has_strong(skills) else 40,
        "Internship": 70,
        "Courses": 60,
        "Government Job": 50
    }

    google_query = build_query(
        prediction,
        skills_text,
        location,
        degree
    )

    # Save for review page
    session['google_query'] = google_query

    return render_template(
        'result.html',
        scores=scores,
        prediction=prediction,
        google_query=google_query,
        roadmap=get_roadmap(prediction),
        skill_suggestions=suggest_skills(skills),
        career_info=get_career_info(prediction)
    )
# --------------------------
# ADMIN LOGIN
# --------------------------

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == "admin" and password == "admin123":
            session['admin'] = True
            return redirect('/admin-dashboard')
        else:
            return render_template('adminlogin.html', error="❌ Invalid Admin Credentials")

    return render_template('adminlogin.html')


# --------------------------
# ADMIN DASHBOARD
# --------------------------

@app.route('/admin-dashboard')
def admin_dashboard():

    if not session.get('admin'):
        return redirect('/admin-login')

    users = User.query.all()
    data = UserInput.query.all()
    reviews = Review.query.order_by(
        Review.created_at.desc()
    ).all()

    total_users = len(users)
    total_reviews = len(reviews)

    avg_rating = 0
    if reviews:
        avg_rating = round(
            sum(r.rating for r in reviews) / total_reviews,
            1
        )

    career_list = []

    for d in data:

        skills = normalize_skills(d.skills)

        career_list.append(
            choose_prediction(
                d.cgpa,
                skills,
                d.focus_level,
                d.financial_stability
            )
        )

    career_stats = Counter(career_list)

    return render_template(
        'admindashboard.html',
        users=users,
        data=data,
        reviews=reviews,
        total_users=total_users,
        total_reviews=total_reviews,
        avg_rating=avg_rating,
        career_stats=career_stats
    )


# --------------------------
# DELETE USER
# --------------------------

@app.route('/admin/delete_user/<int:user_id>')
def delete_user(user_id):
    if not session.get('admin'):
        return redirect('/admin-login')

    user = User.query.get(user_id)

    if user:
        UserInput.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()

    return redirect('/admin-dashboard')
@app.route('/admin/delete_review/<int:id>')
def admin_delete_review(id):

    if not session.get('admin'):
        return redirect('/admin-login')

    review = Review.query.get_or_404(id)

    db.session.delete(review)
    db.session.commit()

    return redirect('/admin-dashboard')

# --------------------------
# ADMIN LOGOUT
# --------------------------

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin-login')

@app.route('/reviews')
def reviews():

    if 'user_id' not in session:
        return redirect('/login-page')

    reviews = Review.query.order_by(
        Review.created_at.desc()
    ).all()

    avg_rating = 0

    if reviews:
        avg_rating = round(
            sum(r.rating for r in reviews) / len(reviews),
            1
        )

    user_review = Review.query.filter_by(
        user_id=session['user_id']
    ).first()

    return render_template(
    'review.html',
    reviews=reviews,
    user_review=user_review,
    avg_rating=avg_rating,
    google_query=session.get('google_query', '')
)
@app.route('/add-review', methods=['POST'])
def add_review():

    if 'user_id' not in session:
        return redirect('/login-page')

    rating = int(request.form.get('rating'))
    text = request.form.get('review').strip()

    existing = Review.query.filter_by(
        user_id=session['user_id']
    ).first()

    if existing:

        existing.rating = rating
        existing.review = text

    else:

        db.session.add(
            Review(
                user_id=session['user_id'],
                rating=rating,
                review=text
            )
        )

    db.session.commit()

    return redirect('/reviews')


@app.route('/delete-review/<int:id>')
def delete_review(id):

    review = Review.query.get_or_404(id)

    if review.user_id == session.get('user_id'):

        db.session.delete(review)
        db.session.commit()

    return redirect('/reviews')
    
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)

