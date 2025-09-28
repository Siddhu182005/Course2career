import os
import json
import re
import requests
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import google.generativeai as genai
import jwt
import sqlitecloud as sq
from flask import Flask, request, jsonify, g, render_template, redirect, url_for, send_from_directory
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
SQLITECLOUD_CONNECTION = os.environ.get("SQLITECLOUD_CONNECTION_STRING")
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')

if not app.config['SECRET_KEY']:
    raise ValueError("FATAL ERROR: JWT_SECRET environment variable is not set.")
if not GEMINI_API_KEY:
    raise ValueError("FATAL ERROR: GEMINI_API_KEY environment variable is not set.")
if not SQLITECLOUD_CONNECTION:
    raise ValueError("FATAL ERROR: SQLITECLOUD_CONNECTION_STRING environment variable is not set.")
if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
    print("WARNING: GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET environment variables are not set. GitHub login will not work.")

genai.configure(api_key=GEMINI_API_KEY)

def sqldb(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        db = sq.connect(SQLITECLOUD_CONNECTION)
        db.row_factory = sq.Row
        c = db.cursor()
        final = function(c, *args, **kwargs)
        db.commit()
        db.close()
        return final
    return wrapper

def authenticate_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Authentication token is required."}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired."}), 403
        except jwt.InvalidTokenError:
            return jsonify({"message": "Token is invalid."}), 403
            
        return f(*args, **kwargs)
    return decorated_function

def authenticate_admin(f):
    @wraps(f)
    @authenticate_token
    def decorated_function(*args, **kwargs):
        if 'role' not in g.user or g.user['role'] != 'admin':
            return jsonify({"message": "Administrator access required."}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/signup', methods=['POST'])
@sqldb
def signup(c):
    data = request.get_json()
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    insert_query = "INSERT INTO users(full_name, email, password) VALUES(?, ?, ?)"
    
    try:
        c.execute(insert_query, (full_name, email, hashed_password))
        new_user_id = c.lastrowid
        new_user_object = {
            "id": new_user_id,
            "full_name": full_name,
            "email": email
        }
        return jsonify({
            "message": "Account created successfully!",
            "user": new_user_object
        }), 201
    except sq.IntegrityError:
        return jsonify({"message": "User with this email already exists."}), 400
    except Exception as e:
        return jsonify({"message": "Server error during signup."}), 500

@app.route('/api/login', methods=['POST'])
@sqldb
def login(c):
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    query = "SELECT * FROM users WHERE email = ?"
    c.execute(query, (email,))
    user = c.fetchone()

    if not user:
        return jsonify({"message": "User with this email not found."}), 404

    if bcrypt.check_password_hash(user['password'], password):
        payload = {
            'userId': user['id'],
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({
            "message": "Login successful!",
            "token": token,
            "userId": user['id'],
            "role": user['role']
        })
    else:
        return jsonify({"message": "Invalid password."}), 401

@app.route('/login/github')
def github_login():
    if not GITHUB_CLIENT_ID:
        return "GitHub login is not configured.", 500
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=user:email"
    return redirect(github_auth_url)

@app.route('/login/github/authorized')
@sqldb
def github_authorized(c):
    code = request.args.get('code')
    if not code:
        return "Error: No authorization code provided from GitHub.", 400

    token_url = 'https://github.com/login/oauth/access_token'
    token_params = {'client_id': GITHUB_CLIENT_ID, 'client_secret': GITHUB_CLIENT_SECRET, 'code': code}
    headers = {'Accept': 'application/json'}
    token_res = requests.post(token_url, params=token_params, headers=headers)
    token_json = token_res.json()
    access_token = token_json.get('access_token')

    if not access_token:
        return "Error: Could not retrieve access token from GitHub.", 400

    user_api_url = 'https://api.github.com/user'
    auth_header = {'Authorization': f'token {access_token}'}
    user_res = requests.get(user_api_url, headers=auth_header)
    user_json = user_res.json()
    
    user_email = user_json.get('email')
    if not user_email:
        emails_res = requests.get(f'{user_api_url}/emails', headers=auth_header)
        emails = emails_res.json()
        primary_email = next((email['email'] for email in emails if email['primary']), None)
        user_email = primary_email

    if not user_email:
        return "Error: Could not retrieve email from GitHub.", 400

    c.execute("SELECT * FROM users WHERE email = ?", (user_email,))
    user = c.fetchone()

    if not user:
        user_name = user_json.get('name') or user_json.get('login')
        placeholder_password = bcrypt.generate_password_hash(os.urandom(16)).decode('utf-8')
        c.execute("INSERT INTO users(full_name, email, password) VALUES(?, ?, ?)", (user_name, user_email, placeholder_password))
        c.execute("SELECT * FROM users WHERE email = ?", (user_email,))
        user = c.fetchone()

    payload = {'userId': user['id'], 'email': user['email'], 'role': user['role'], 'exp': datetime.utcnow() + timedelta(hours=1)}
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
    
    return redirect(url_for('github_auth_complete_page', token=token, userId=user['id'], role=user['role']))

@app.route('/api/profile', methods=['GET'])
@authenticate_token
@sqldb
def get_profile(c):
    user_id = g.user['userId']
    query = "SELECT id, full_name, email, avatar_url, created_at FROM users WHERE id = ?"
    c.execute(query, (user_id,))
    user = c.fetchone()
    if user:
        return jsonify(dict(user))
    return jsonify({"message": "User not found."}), 404

@app.route('/api/profile', methods=['PUT'])
@authenticate_token
@sqldb
def update_profile(c):
    user_id = g.user['userId']
    data = request.get_json()
    full_name = data.get('fullName')
    email = data.get('email')
    avatar_url = data.get('avatarUrl')
    
    update_query = "UPDATE users SET full_name = ?, email = ?, avatar_url = ? WHERE id = ?"
    select_query = "SELECT id, full_name, email, avatar_url FROM users WHERE id = ?"
    
    try:
        c.execute(update_query, (full_name, email, avatar_url, user_id))
        c.execute(select_query, (user_id,))
        updated_user = c.fetchone()
        if updated_user:
            return jsonify({"message": "Profile updated successfully!", "user": dict(updated_user)})
        return jsonify({"message": "User not found."}), 404
    except sq.IntegrityError:
        return jsonify({"message": "This email is already taken."}), 400
    except Exception as e:
        return jsonify({"message": 'Server error while updating profile.'}), 500

@app.route('/api/save-course', methods=['POST'])
@authenticate_token
@sqldb
def save_course(c):
    user_id = g.user['userId']
    data = request.get_json()
    course_title = data.get('courseTitle')
    query = "INSERT INTO saved_courses(user_id, course_title) VALUES(?, ?)"
    try:
        c.execute(query, (user_id, course_title))
        return jsonify({"message": "Course saved successfully!"}), 201
    except Exception as e:
        return jsonify({"message": "Could not save the course."}), 500

@app.route('/api/saved-courses', methods=['GET'])
@authenticate_token
@sqldb
def get_saved_courses(c):
    user_id = g.user['userId']
    query = "SELECT course_title, saved_at FROM saved_courses WHERE user_id = ? ORDER BY saved_at DESC"
    try:
        c.execute(query, (user_id,))
        courses = c.fetchall()
        return jsonify([dict(course) for course in courses])
    except Exception as e:
        return jsonify({"message": "Could not retrieve saved courses."}), 500

@app.route('/api/generate-course-with-ai', methods=['POST'])
@authenticate_token
def generate_course():
    data = request.get_json()
    user_query = data.get('query')
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""
            You are an expert course creator for a user wanting to learn about: "{user_query}".
            Generate a detailed course outline as a clean JSON object without any markdown formatting.
            The JSON object must have these exact keys: "title", "description", "duration",
            "difficulty" (Beginner, Intermediate, or Advanced), "startingSalary" (a string for salary in INR),
            "skills" (an array of 5-7 strings), and "imageQuery" (a 4-5 word, highly descriptive search term for a stock photo, e.g., "person coding on laptop").
            """
        response = model.generate_content(prompt)
        cleaned_text = re.sub(r'^```json\s*|```\s*$', '', response.text, flags=re.MULTILINE).strip()
        course_data = json.loads(cleaned_text)
        return jsonify(course_data)
    except Exception as e:
        return jsonify({"error": "Failed to generate course from AI."}), 500

@app.route('/api/users', methods=['GET'])
@authenticate_admin
@sqldb
def get_all_users(c):
    query = "SELECT id, full_name, email, role, created_at FROM users"
    try:
        c.execute(query)
        users = c.fetchall()
        return jsonify([dict(user) for user in users])
    except Exception as e:
        return jsonify({"message": "Could not retrieve users."}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@authenticate_admin
@sqldb
def delete_user(c, user_id):
    try:
        c.execute("DELETE FROM saved_courses WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return jsonify({"message": "User deleted successfully."}), 200
    except Exception as e:
        return jsonify({"message": "Error deleting user."}), 500
        
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login')
def login_page():
    return render_template("login.html")

@app.route('/signup')
def signup_page():
    return render_template("signup.html")

@app.route('/dashboard')
def dashboard_page():
    return render_template("dashboard.html")
    
@app.route('/profile')
def profile_page():
    return render_template("profile.html")

@app.route('/saved-courses')
def saved_courses_page():
    return render_template("saved-course.html")
    
@app.route('/course-details')
def course_details_page():
    return render_template("course-details.html")

@app.route('/course-path')
def course_path_page():
    return render_template("course-path.html")

@app.route('/admin')
def admin_page():
    return render_template("admin.html")

@app.route('/github-auth-complete')
def github_auth_complete_page():
    return render_template("github-auth-complete.html")

@sqldb
def init_db(c):
    create_user_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      full_name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      avatar_url TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      role TEXT DEFAULT 'user' NOT NULL
    );
    """
    create_saved_courses_table_sql = """
    CREATE TABLE IF NOT EXISTS saved_courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      course_title TEXT NOT NULL,
      saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """
    try:
        c.execute(create_user_table_sql)
        c.execute(create_saved_courses_table_sql)
    except Exception as e:
        raise

if __name__ == '__main__':
    init_db()
    app.run(debug=True)

