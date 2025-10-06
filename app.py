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

def generate_ai_content(prompt, model=AI_MODEL, is_json_response=True):
    try:
        messages = [
            {"role": "user", "content": prompt}
        ]
        if is_json_response:
             messages.insert(0, {"role": "system", "content": "You are an expert content creator who only responds in valid JSON format."})
        
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            data=json.dumps({ "model": model, "messages": messages })
        )
        
        response.raise_for_status()
        
        response_data = response.json()
        response_text = response_data['choices'][0]['message']['content']
        
        if is_json_response:
            cleaned_text = re.sub(
                r'^```json\s*|\s*```\s*$', 
                '', 
                response_text, 
                flags=re.MULTILINE | re.DOTALL
            ).strip()
            data = json.loads(cleaned_text)
            return data, None
        
        return response_text, None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        return None, ({"error": f"API request failed with status code {e.response.status_code}"}, e.response.status_code)
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return None, ({"error": "The AI returned an unexpected format. Please try again."}, 500)
    except Exception as e:
        print(f"AI Error: {str(e)}")
        return None, ({"error": f"AI communication error: {str(e)}"}, 500)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

@app.route('/api/signup', methods=['POST'])
@sqldb
def signup(c):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided."}), 400
        
        full_name = data.get('fullName')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirmPassword')

        if not all([full_name, email, password, confirm_password]):
            return jsonify({"error": "Missing required fields."}), 400

        if password != confirm_password:
            return jsonify({"error": "Passwords do not match."}), 400

        if '@' not in email or '.' not in email:
            return jsonify({"error": "Invalid email format."}), 400

        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters."}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        c.execute(
            "INSERT INTO users(full_name, email, password) VALUES(?, ?, ?)", 
            (full_name, email, hashed_password)
        )
        
        return jsonify({"message": "Account created successfully!"}), 201
        
    except sq.IntegrityError:
        return jsonify({"error": "A user with this email already exists."}), 409
    except Exception as e:
        print(f"Signup Error: {str(e)}")
        return jsonify({"error": "An error occurred during registration."}), 500

@app.route('/api/login', methods=['POST'])
@sqldb
def login(c):
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided."}), 400
        
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required."}), 400

        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            payload = {
                'userId': user['id'],
                'email': user['email'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(days=7)
            }
            token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
            
            return jsonify({
                "message": "Login successful!",
                "token": token,
                "userId": user['id'],
                "role": user['role']
            }), 200
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
        try:
            c.execute(
                "SELECT id, full_name, email, created_at, role FROM users WHERE id = ?", 
                (user_id,)
            )
            user = c.fetchone()
            
            if user:
                return jsonify(dict(user)), 200
            else:
                return jsonify({"error": "User not found."}), 404
                
        except Exception as e:
            print(f"Profile GET Error: {str(e)}")
            return jsonify({"error": "Could not fetch profile."}), 500

    if request.method == 'PUT':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No data provided."}), 400
            
            full_name = data.get('fullName')
            email = data.get('email')

            if not all([full_name, email]):
                return jsonify({"error": "Full name and email are required."}), 400

            if '@' not in email or '.' not in email:
                return jsonify({"error": "Invalid email format."}), 400

            c.execute(
                "UPDATE users SET full_name = ?, email = ? WHERE id = ?", 
                (full_name, email, user_id)
            )
            
            c.execute(
                "SELECT id, full_name, email FROM users WHERE id = ?", 
                (user_id,)
            )
            updated_user = c.fetchone()
            
            return jsonify({
                "message": "Profile updated successfully!",
                "user": dict(updated_user)
            }), 200
            
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
        try:
            c.execute(
                """SELECT id, course_title, course_data, saved_at 
                   FROM saved_courses 
                   WHERE user_id = ? 
                   ORDER BY saved_at DESC""", 
                (user_id,)
            )
            courses = [dict(course) for course in c.fetchall()]
            return jsonify(courses), 200
            
        except Exception as e:
            print(f"Saved Courses GET Error: {str(e)}")
            return jsonify({"error": "Could not fetch saved courses."}), 500

    if request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No data provided."}), 400
            
            course_data = data.get('courseData')
            
            if not course_data or 'title' not in course_data:
                return jsonify({"error": "Valid course data is required."}), 400

            course_title = course_data['title']
            course_data_str = json.dumps(course_data)

            c.execute(
                "INSERT INTO saved_courses(user_id, course_title, course_data) VALUES(?, ?, ?)",
                (user_id, course_title, course_data_str)
            )
            
            return jsonify({"message": "Course saved successfully!"}), 201
            
        except Exception as e:
            print(f"Saved Courses POST Error: {str(e)}")
            return jsonify({"error": "Could not save course."}), 500

@app.route('/api/saved-courses/<int:course_id>', methods=['DELETE'])
@authenticate_token
@sqldb
def delete_saved_course(c, course_id):
    user_id = g.user['userId']
    
    try:
        c.execute(
            "SELECT id FROM saved_courses WHERE id = ? AND user_id = ?",
            (course_id, user_id)
        )
        course = c.fetchone()
        
        if not course:
            return jsonify({"error": "Course not found or unauthorized."}), 404
        
        c.execute("DELETE FROM saved_courses WHERE id = ?", (course_id,))
        
        return jsonify({"message": "Course deleted successfully."}), 200
        
    except Exception as e:
        print(f"Delete Course Error: {str(e)}")
        return jsonify({"error": "Could not delete course."}), 500

@app.route('/api/generate-course-with-ai', methods=['POST'])
@authenticate_token
def generate_course():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided."}), 400
        
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({"error": "A query is required to generate a course."}), 400

        prompt = f"""
You are an expert course creator. A user wants to learn about: "{user_query}".

Generate a detailed course outline as a clean JSON object without any markdown formatting or explanations.
The JSON object must strictly follow this structure:
{{
  "title": "Course Title",
  "description": "A concise and engaging course description (2-3 sentences).",
  "duration": "Estimated duration (e.g., '6 Weeks', '3 Months')",
  "difficulty": "Beginner, Intermediate, or Advanced",
  "startingSalary": "A realistic starting salary in Indian Rupees (INR) (e.g., '₹5L - ₹8L / yr')",
  "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
  "modules": [
    {{ "title": "Module 1: Introduction", "description": "Brief overview of the module." }},
    {{ "title": "Module 2: Core Concepts", "description": "Details about core concepts." }},
    {{ "title": "Module 3: Advanced Topics", "description": "Exploring advanced topics." }},
    {{ "title": "Module 4: Practical Application", "description": "Hands-on projects and case studies." }}
  ]
}}

Important:
- Return ONLY valid JSON, no extra text.
- The 'startingSalary' MUST be in Indian Rupees (INR) and formatted like '₹5L - ₹8L / yr'.
- Include 4-6 modules.
- Include 5-7 relevant skills.
- Make the description engaging and practical for the Indian job market.
"""

        course_data, error = generate_ai_content(prompt)
        
        if error:
            return jsonify(error[0]), error[1]
        
        return jsonify(course_data), 200
        
    except Exception as e:
        print(f"Generate Course Error: {str(e)}")
        return jsonify({"error": "Could not generate course."}), 500

@app.route('/api/generate-career-path', methods=['POST'])
@authenticate_token
def generate_career_path():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided."}), 400
        
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({"error": "A query is required to generate a career path."}), 400

        prompt = f"""
You are an expert career path creator for the Indian job market. 
Generate a visual career progression for: "{user_query}".

The output must be a clean JSON object, without any markdown formatting or explanations.
The JSON object must have the following structure:
{{
  "title": "Career Path Title for {user_query}",
  "description": "A brief description of this career field (2-3 sentences)",
  "flowchart": {{
    "roles": [
      {{
        "id": 1,
        "title": "Job Title",
        "salary": "₹XL - ₹YL / yr",
        "stage": "Entry Level"
      }}
    ]
  }}
}}

Important:
- Return ONLY valid JSON.
- Include 8-12 roles total.
- Distribute roles across three stages: "Entry Level", "Mid Career", "Late Career".
- Each stage must have 2-4 roles.
- Use realistic Indian salary ranges in Indian Rupees (Lakhs per year, e.g., '₹8L - ₹12L / yr').
- Progress from junior to senior positions logically.
"""

        path_data, error = generate_ai_content(prompt)
        
        if error:
            return jsonify(error[0]), error[1]
        
        return jsonify(path_data), 200
        
    except Exception as e:
        print(f"Generate Career Path Error: {str(e)}")
        return jsonify({"error": "Could not generate career path."}), 500

@app.route('/api/chatbot', methods=['POST'])
@authenticate_token
def chatbot():
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Query is required."}), 400
        
        user_query = data.get('query')
       prompt = f"""
You are Course2Career Assistant, a friendly and helpful AI guide for the Course2Career website. Your personality is encouraging and clear.

A user has asked: "{user_query}"

**Your Primary Goal:**
First and foremost, always try to connect the user's question to the features available on the Course2Career website. Your main job is to show users how our tools can help them.

**Response Guidelines:**
1.  **Promote First:** If the user is asking about learning a skill, finding a course, or exploring career paths (e.g., "how to learn python", "what is a data scientist salary"), your FIRST step is to recommend the **"AI Course Generator"** and the **"Career Path Visualizer"**. Explain that these tools give instant, personalized answers.
2.  **Be Helpful:** After promoting our tools, provide a direct and helpful answer to the user's question.
3.  **Use Simple HTML:** Format your response with clean HTML. Use `<p>`, `<strong>`, `<ul>`, and `<li>` tags to make it easy to read. If you include external links, use `<a href="..." target="_blank">`. Do not include `<html>` or `<body>` tags.
4.  **Suggest External Resources Last:** If helpful, you can suggest other websites (like Coursera, Udemy, etc.) but only AFTER you have explained how Course2Career's tools can help.

Keep your answer concise, friendly, and focused on helping the user on their career journey.
"""
        
        response_text, error = generate_ai_content(prompt, is_json_response=False)
        
        if error:
            return jsonify(error[0]), error[1]
            
        return jsonify({"response": response_text}), 200

    except Exception as e:
        print(f"Chatbot Error: {str(e)}")
        return jsonify({"error": "An error occurred in the chatbot."}), 500

@app.route('/api/users', methods=['GET'])
@authenticate_admin
@sqldb
def get_all_users(c):
    try:
        c.execute(
            """SELECT id, full_name, email, role, created_at 
               FROM users 
               ORDER BY created_at DESC"""
        )
        users = c.fetchall()
        return jsonify([dict(user) for user in users]), 200
        
    except Exception as e:
        print(f"Get Users Error: {str(e)}")
        return jsonify({"error": "Could not fetch users."}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@authenticate_admin
@sqldb
def delete_user(c, user_id):
    try:
        if user_id == g.user['userId']:
            return jsonify({"error": "Admins cannot delete their own account."}), 403
        
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        if c.rowcount == 0:
            return jsonify({"error": "User not found."}), 404
        
        return jsonify({"message": "User and all their data deleted successfully."}), 200
        
    except Exception as e:
        print(f"Delete User Error: {str(e)}")
        return jsonify({"error": "Could not delete user."}), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")

if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='0.0.0.0', port=port, debug=False)
