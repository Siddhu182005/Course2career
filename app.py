import os
import json
import re
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import jwt
import sqlitecloud as sq
from flask import Flask, request, jsonify, g, render_template
from flask_bcrypt import Bcrypt
import requests

load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
AI_MODEL = 'nousresearch/deephermes-3-llama-3-8b-preview:free'

SQLITECLOUD_CONNECTION = os.environ.get("SQLITECLOUD_CONNECTION_STRING")

if not app.config['SECRET_KEY']:
    raise ValueError("FATAL ERROR: JWT_SECRET environment variable is not set.")
if not OPENROUTER_API_KEY:
    raise ValueError("FATAL ERROR: OPENROUTER_API_KEY environment variable is not set.")
if not SQLITECLOUD_CONNECTION:
    raise ValueError("FATAL ERROR: SQLITECLOUD_CONNECTION_STRING environment variable is not set.")

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
    
    print("✓ Database initialized successfully.")

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

def generate_ai_content(messages, is_json_response=False):
    try:
        payload = {
            "model": AI_MODEL,
            "messages": messages
        }
        if is_json_response:
            payload["response_format"] = {"type": "json_object"}

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            json=payload
        )
        response.raise_for_status()
        
        response_data = response.json()
        response_text = response_data['choices'][0]['message']['content']
        
        if is_json_response:
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not match:
                raise json.JSONDecodeError("No valid JSON object found in the AI response.", response_text, 0)
            return json.loads(match.group(0)), None
        
        return response_text, None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.text}")
        return None, ({"error": f"API request failed: {e.response.reason}"}, e.response.status_code)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e.msg} - Response: {e.doc}")
        return None, ({"error": "The AI returned an invalid format. Please try again."}, 500)
    except Exception as e:
        print(f"An unexpected AI error occurred: {str(e)}")
        return None, ({"error": f"An AI communication error occurred."}, 500)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route('/api/signup', methods=['POST'])
@sqldb
def signup(c):
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided."}), 400
    
    full_name = data.get('fullName')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')

    if not all([full_name, email, password, confirm_password]):
        return jsonify({"error": "All fields are required."}), 400
    if password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400
    if '@' not in email or '.' not in email:
        return jsonify({"error": "Invalid email format."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    try:
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        c.execute("INSERT INTO users(full_name, email, password) VALUES(?, ?, ?)", (full_name, email, hashed_password))
        return jsonify({"message": "Account created successfully!"}), 201
    except sq.IntegrityError:
        return jsonify({"error": "A user with this email already exists."}), 409
    except Exception as e:
        print(f"Signup Error: {str(e)}")
        return jsonify({"error": "An error occurred during registration."}), 500

@app.route('/api/login', methods=['POST'])
@sqldb
def login(c):
    data = request.get_json()
    if not data: return jsonify({"error": "No data provided."}), 400
    
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        if user and bcrypt.check_password_hash(user['password'], password):
            payload = {'userId': user['id'], 'email': user['email'], 'role': user['role'], 'exp': datetime.utcnow() + timedelta(days=7)}
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({"message": "Login successful!", "token": token, "userId": user['id'], "role": user['role']}), 200
        else:
            return jsonify({"error": "Invalid email or password."}), 401
    except Exception as e:
        print(f"Login Error: {str(e)}")
        return jsonify({"error": "An error occurred during login."}), 500

@app.route('/api/profile', methods=['GET', 'PUT'])
@authenticate_token
@sqldb
def profile(c):
    user_id = g.user['userId']
    if request.method == 'GET':
        c.execute("SELECT id, full_name, email, created_at, role FROM users WHERE id = ?", (user_id,))
        user = c.fetchone()
        return jsonify(dict(user)) if user else (jsonify({"error": "User not found."}), 404)
    
    if request.method == 'PUT':
        data = request.get_json()
        if not data: return jsonify({"error": "No data provided."}), 400
        full_name, email = data.get('fullName'), data.get('email')
        if not all([full_name, email]): return jsonify({"error": "Full name and email are required."}), 400
        if '@' not in email or '.' not in email: return jsonify({"error": "Invalid email format."}), 400

        try:
            c.execute("UPDATE users SET full_name = ?, email = ? WHERE id = ?", (full_name, email, user_id))
            c.execute("SELECT id, full_name, email FROM users WHERE id = ?", (user_id,))
            updated_user = c.fetchone()
            return jsonify({"message": "Profile updated successfully!", "user": dict(updated_user)}), 200
        except sq.IntegrityError:
            return jsonify({"error": "This email is already taken by another user."}), 409
        except Exception as e:
            print(f"Profile PUT Error: {str(e)}")
            return jsonify({"error": "Could not update profile."}), 500

@app.route('/api/saved-courses', methods=['GET', 'POST'])
@authenticate_token
@sqldb
def saved_courses(c):
    user_id = g.user['userId']
    if request.method == 'GET':
        c.execute("SELECT id, course_title, course_data, saved_at FROM saved_courses WHERE user_id = ? ORDER BY saved_at DESC", (user_id,))
        courses = [dict(course) for course in c.fetchall()]
        return jsonify(courses), 200
    
    if request.method == 'POST':
        data = request.get_json()
        if not data: return jsonify({"error": "No data provided."}), 400
        course_data = data.get('courseData')
        if not course_data or 'title' not in course_data: return jsonify({"error": "Valid course data is required."}), 400
        
        try:
            c.execute("INSERT INTO saved_courses(user_id, course_title, course_data) VALUES(?, ?, ?)",(user_id, course_data['title'], json.dumps(course_data)))
            return jsonify({"message": "Course saved successfully!"}), 201
        except Exception as e:
            print(f"Saved Courses POST Error: {str(e)}")
            return jsonify({"error": "Could not save course."}), 500

@app.route('/api/saved-courses/<int:course_id>', methods=['DELETE'])
@authenticate_token
@sqldb
def delete_saved_course(c, course_id):
    user_id = g.user['userId']
    c.execute("SELECT id FROM saved_courses WHERE id = ? AND user_id = ?", (course_id, user_id))
    if not c.fetchone(): return jsonify({"error": "Course not found or unauthorized."}), 404
    
    c.execute("DELETE FROM saved_courses WHERE id = ?", (course_id,))
    return jsonify({"message": "Course deleted successfully."}), 200

@app.route('/api/generate-course-with-ai', methods=['POST'])
@authenticate_token
def generate_course():
    data = request.get_json()
    if not data or not data.get('query'): return jsonify({"error": "A query is required."}), 400
    user_query = data.get('query')

    prompt = f"""
        You are an expert course creator who ONLY responds in valid JSON.
        A user wants a detailed course about: "{user_query}".
        Create a comprehensive course outline with the following JSON structure. Each module must contain 8 chapters, and each chapter must contain 6 pages. The 'content' for each page should be a detailed, educational paragraph.

        {{
        "title": "Course Title", "description": "Engaging 2-3 sentence description.",
        "duration": "e.g., '8 Weeks'", "difficulty": "Beginner, Intermediate, or Advanced",
        "startingSalary": "Realistic starting salary in INR (e.g., '₹4L - ₹6L / yr')",
        "skills": ["5-7 relevant skills"],
        "modules": [
            {{
            "title": "Module 1: [Module Title]", "description": "Brief overview of the module.",
            "chapters": [
                {{
                "title": "Chapter 1.1: [Chapter Title]",
                "pages": [
                    {{"title": "Page 1: [Page Title]", "content": "Detailed, paragraph-form educational content for this page."}},
                    {{"title": "Page 2: [Page Title]", "content": "Detailed, paragraph-form educational content for this page."}},
                    {{"title": "Page 3: [Page Title]", "content": "Detailed, paragraph-form educational content for this page."}},
                    {{"title": "Page 4: [Page Title]", "content": "Detailed, paragraph-form educational content for this page."}},
                    {{"title": "Page 5: [Page Title]", "content": "Detailed, paragraph-form educational content for this page."}},
                    {{"title": "Page 6: [Page Title]", "content": "Detailed, paragraph-form educational content for this page."}}
                ]
                }}
              ]
            }}
          ]
        }}
    """
    messages = [{"role": "system", "content": "You are a course creation expert that only outputs JSON."}, {"role": "user", "content": prompt}]
    course_data, error = generate_ai_content(messages=messages, is_json_response=True)
    return jsonify(error[0] if error else course_data), error[1] if error else 200

@app.route('/api/generate-career-path', methods=['POST'])
@authenticate_token
def generate_career_path():
    data = request.get_json()
    if not data or not data.get('query'): return jsonify({"error": "A query is required."}), 400
    user_query = data.get('query')

    prompt = f"""
        You are a career path expert for the Indian job market who ONLY responds in valid JSON.
        Generate a career progression for "{user_query}".
        The JSON must follow this structure:
        {{
        "title": "Career Path for {user_query}", "description": "Brief 2-3 sentence description.",
        "flowchart": {{"roles": [ {{"id": 1, "title": "Job Title", "salary": "₹XL - ₹YL / yr", "stage": "Entry Level, Mid Career, or Late Career"}} ] }}
        }}
        Include 8-12 total roles distributed across the three stages.
    """
    messages = [{"role": "system", "content": "You are a career path expert that only outputs JSON."}, {"role": "user", "content": prompt}]
    path_data, error = generate_ai_content(messages=messages, is_json_response=True)
    return jsonify(error[0] if error else path_data), error[1] if error else 200

@app.route('/api/chatbot', methods=['POST'])
@authenticate_token
def chatbot():
    data = request.get_json()
    if not data or 'query' not in data: return jsonify({"error": "Query is required."}), 400
    
    user_query = data.get('query')
    history = data.get('history', [])
    
    system_prompt = """
        You are Course2Career Assistant. Your #1 rule is to NEVER mention or suggest external websites like Coursera or Udemy. Your entire focus is on the tools available on THIS website.

        **Your Task:**
        1. Give a direct, concise answer to the user's question.
        2. If the question is about learning a skill or a career, add this EXACT sentence to the end of your response: "For a detailed plan, use the **Course Search** and **Career Path Visualizer** tools on our site."
        3. Use simple HTML for formatting: `<p>`, `<strong>`, `<ul>`, `<li>`. Do NOT include `<html>` or `<body>` tags.

        Remember: Do not mention any other websites.
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_query})

    response_text, error = generate_ai_content(messages=messages, is_json_response=False)
    
    if error:
        return jsonify(error[0]), error[1]
    return jsonify({"response": response_text}), 200

@app.route('/api/users', methods=['GET'])
@authenticate_admin
@sqldb
def get_all_users(c):
    c.execute("SELECT id, full_name, email, role, created_at FROM users ORDER BY created_at DESC")
    users = c.fetchall()
    return jsonify([dict(user) for user in users]), 200

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@authenticate_admin
@sqldb
def delete_user(c, user_id):
    if user_id == g.user['userId']: return jsonify({"error": "Admins cannot delete their own account."}), 403
    
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    if c.rowcount == 0: return jsonify({"error": "User not found."}), 404
    
    return jsonify({"message": "User and all their data deleted successfully."}), 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")

if __name__ == '__main__':
    with app.app_context():
        init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
