import os
import json
import re
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import google.generativeai as genai
import jwt
import sqlitecloud as sq
from flask import Flask, request, jsonify, g, render_template
from flask_bcrypt import Bcrypt

load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
SQLITECLOUD_CONNECTION = os.environ.get("SQLITECLOUD_CONNECTION_STRING")
AI_MODEL = 'gemini-2.5-flash'

if not app.config['SECRET_KEY']:
    raise ValueError("FATAL ERROR: JWT_SECRET environment variable is not set.")
if not GEMINI_API_KEY:
    raise ValueError("FATAL ERROR: GEMINI_API_KEY environment variable is not set.")
if not SQLITECLOUD_CONNECTION:
    raise ValueError("FATAL ERROR: SQLITECLOUD_CONNECTION_STRING environment variable is not set.")

genai.configure(api_key=GEMINI_API_KEY)

def get_db():
    if 'db' not in g:
        g.db = sq.connect(SQLITECLOUD_CONNECTION)
        g.db.row_factory = sq.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def sqldb(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        db = get_db()
        c = db.cursor()
        try:
            result = function(c, *args, **kwargs)
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise e
    return wrapper

@sqldb
def init_db(c):
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      full_name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      role TEXT DEFAULT 'user' NOT NULL
    );""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS saved_courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      course_title TEXT NOT NULL,
      course_data TEXT NOT NULL,
      saved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );""")
    print("Database initialized.")


def authenticate_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Authentication token is required."}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.user = data
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 403
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token is invalid."}), 403

        return f(*args, **kwargs)
    return decorated_function

def authenticate_admin(f):
    @wraps(f)
    @authenticate_token
    def decorated_function(*args, **kwargs):
        if 'role' not in g.user or g.user['role'] != 'admin':
            return jsonify({"error": "Administrator access required."}), 403
        return f(*args, **kwargs)
    return decorated_function

def generate_ai_content(prompt):
    try:
        model = genai.GenerativeModel(AI_MODEL)
        response = model.generate_content(prompt)
        cleaned_text = re.sub(r'^```json\s*|\s*```\s*$', '', response.text, flags=re.MULTILINE | re.DOTALL).strip()
        data = json.loads(cleaned_text)
        return data, None
    except json.JSONDecodeError:
        return None, ({"error": "The AI returned an unexpected format. Please try again."}, 500)
    except Exception as e:
        return None, ({"error": f"AI communication error: {str(e)}"}, 500)

@app.route('/api/signup', methods=['POST'])
@sqldb
def signup(c):
    data = request.get_json()
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')

    if not all([full_name, email, password]):
        return jsonify({"error": "Missing required fields."}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        c.execute("INSERT INTO users(full_name, email, password) VALUES(?, ?, ?)", (full_name, email, hashed_password))
        return jsonify({"message": "Account created successfully!"}), 201
    except sq.IntegrityError:
        return jsonify({"error": "A user with this email already exists."}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
@sqldb
def login(c):
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()

    if user and bcrypt.check_password_hash(user['password'], password):
        payload = {
            'userId': user['id'], 'email': user['email'], 'role': user['role'],
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
        return jsonify({
            "message": "Login successful!", "token": token, "userId": user['id'], "role": user['role']
        })
    else:
        return jsonify({"error": "Invalid email or password."}), 401

@app.route('/api/profile', methods=['GET', 'PUT'])
@authenticate_token
@sqldb
def profile(c):
    user_id = g.user['userId']
    if request.method == 'GET':
        c.execute("SELECT id, full_name, email, created_at FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        return (jsonify(dict(user))) if user else (jsonify({"error": "User not found."}), 404)

    if request.method == 'PUT':
        data = request.get_json()
        full_name = data.get('fullName')
        email = data.get('email')

        if not all([full_name, email]):
             return jsonify({"error": "Full name and email are required."}), 400

        try:
            c.execute("UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user_id))
            c.execute("SELECT id, full_name, email FROM users WHERE id = ?", (user_id,))
            updated_user = c.fetchone()
            return jsonify({"message": "Profile updated successfully!", "user": dict(updated_user)})
        except sq.IntegrityError:
            return jsonify({"error": "This email is already taken by another user."}), 409
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/saved-courses', methods=['GET', 'POST'])
@authenticate_token
@sqldb
def saved_courses(c):
    user_id = g.user['userId']
    if request.method == 'GET':
        c.execute("SELECT id, course_title, course_data, saved_at FROM saved_courses WHERE user_id = ? ORDER BY saved_at DESC", (user_id,))
        courses = [dict(course) for course in c.fetchall()]
        return jsonify(courses)

    if request.method == 'POST':
        data = request.get_json()
        course_data = data.get('courseData')
        if not course_data or 'title' not in course_data:
            return jsonify({"error": "Valid course data is required."}), 400

        course_title = course_data['title']
        course_data_str = json.dumps(course_data)

        try:
            c.execute("INSERT INTO saved_courses(user_id, course_title, course_data) VALUES(?, ?, ?)", (user_id, course_title, course_data_str))
            return jsonify({"message": "Course saved successfully!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/generate-course-with-ai', methods=['POST'])
@authenticate_token
def generate_course():
    user_query = request.get_json().get('query')
    if not user_query:
        return jsonify({"error": "A query is required to generate a course."}), 400

    prompt = f"""
        You are an expert course creator.
        A user wants to learn about: "{user_query}".
        Generate a detailed course outline as a clean JSON object without any markdown formatting or explanations.
        The JSON object must strictly follow this structure:
        {{
          "title": "Course Title",
          "description": "A concise and engaging course description.",
          "duration": "Estimated duration (e.g., '6 Weeks')",
          "difficulty": "Beginner, Intermediate, or Advanced",
          "startingSalary": "A realistic starting salary in INR (e.g., '₹5L - ₹8L / yr')",
          "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
          "modules": [
              {{ "title": "Module 1: Introduction", "description": "Brief overview of the module." }},
              {{ "title": "Module 2: Core Concepts", "description": "Details about core concepts." }},
              {{ "title": "Module 3: Advanced Topics", "description": "Exploring advanced topics." }},
              {{ "title": "Module 4: Practical Application", "description": "Hands-on projects and case studies." }}
          ]
        }}
        """
    course_data, error = generate_ai_content(prompt)
    return (jsonify(error[0]), error[1]) if error else jsonify(course_data)

@app.route('/api/generate-career-path', methods=['POST'])
@authenticate_token
def generate_career_path():
    user_query = request.get_json().get('query')
    if not user_query:
        return jsonify({"error": "A query is required to generate a career path."}), 400

    prompt = f"""
        You are an expert career path creator.
        Generate a visual career progression for a "{user_query}".
        The output must be a clean JSON object, without any markdown formatting or explanations.
        The JSON object must have a "title", a "description", and a "flowchart" object.
        The "flowchart" object must contain only a "roles" array (no connections needed).
        The "roles" array should have 8-10 role objects, each with a unique integer "id", "title", "salary" (e.g., "₹8L - ₹12L / yr"), and "stage" ('Entry Level', 'Mid Career', or 'Late Career').
        """
    path_data, error = generate_ai_content(prompt)
    return (jsonify(error[0]), error[1]) if error else jsonify(path_data)


@app.route('/api/users', methods=['GET'])
@authenticate_admin
@sqldb
def get_all_users(c):
    c.execute("SELECT id, full_name, email, role, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    return jsonify([dict(user) for user in users])

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@authenticate_admin
@sqldb
def delete_user(c, user_id):
    if user_id == g.user['userId']:
        return jsonify({"error": "Admins cannot delete their own account."}), 403
    try:
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if c.rowcount == 0:
            return jsonify({"error": "User not found."}), 404
        return jsonify({"message": "User and all their data deleted successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
