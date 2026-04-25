from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from collections import Counter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nexivara-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --------------------------
# DATABASE MODELS
# --------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class UserInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cgpa = db.Column(db.Float, nullable=False)
    skills = db.Column(db.String(500), nullable=False)
    focus_level = db.Column(db.Integer, nullable=False)
    financial_stability = db.Column(db.Integer, nullable=False)
    district = db.Column(db.String(100), nullable=False)
    preferred_location = db.Column(db.String(100), nullable=True)
    degree = db.Column(db.String(20), nullable=False)

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

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    if not username or not password:
        return render_template('login.html', error="❌ Enter all fields")

    user = User.query.filter_by(username=username).first()

    if user:
        if user.password == password:
            session['user_id'] = user.id
            return redirect('/form')
        else:
            return render_template('login.html', error="❌ Wrong Password")

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    session['user_id'] = new_user.id
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

    return render_template('form.html', existing=existing)
# --------------------------
# RESULT
# --------------------------

@app.route('/result', methods=['POST'])
def result():
    if 'user_id' not in session:
        return redirect('/login-page')

    cgpa = float(request.form.get('cgpa', 0))
    skills_text = request.form.get('skills', '')
    focus = int(request.form.get('focus_level', 5))
    financial = int(request.form.get('financial_stability', 5))
    location = request.form.get('preferred_location', 'India')
    district = request.form.get('district', '')
    degree = request.form.get('degree', '')

    skills = normalize_skills(skills_text)

    # ✅ SAVE / UPDATE DATA
    existing = UserInput.query.filter_by(user_id=session['user_id']).first()

    if existing:
        existing.cgpa = cgpa
        existing.skills = skills_text
        existing.focus_level = focus
        existing.financial_stability = financial
        existing.district = district
        existing.preferred_location = location
        existing.degree = degree 
    else:
        db.session.add(UserInput(
            user_id=session['user_id'],
            cgpa=cgpa,
            skills=skills_text,
            focus_level=focus,
            financial_stability=financial,
            district=district,
            preferred_location=location,
            degree=degree  

        ))

    db.session.commit()

    # ✅ LOGIC
    prediction = choose_prediction(cgpa, skills, focus, financial)

    scores = {
        "Higher Studies": int(cgpa * 10),
        "Job": 80 if has_strong(skills) else 40,
        "Internship": 70,
        "Courses": 60,
        "Government Job": 50
    }

    return render_template(
        'result.html',
        scores=scores,
        prediction=prediction,
        google_query=build_query(prediction, skills_text, location, degree),
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

    total_users = len(users)

    career_list = []
    for d in data:
        skills = normalize_skills(d.skills)
        career_list.append(
            choose_prediction(d.cgpa, skills, d.focus_level, d.financial_stability)
        )

    career_stats = Counter(career_list)

    return render_template(
        'admindashboard.html',
        users=users,
        data=data,
        total_users=total_users,
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


# --------------------------
# ADMIN LOGOUT
# --------------------------

@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    return redirect('/admin-login')
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)