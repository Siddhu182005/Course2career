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

# Configuration
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
SQLITECLOUD_CONNECTION = os.environ.get("SQLITECLOUD_CONNECTION_STRING")
AI_MODEL = 'gemini-2.5-flash-lite'

# Validate required environment variables
if not app.config['SECRET_KEY']:
    raise ValueError("FATAL ERROR: JWT_SECRET environment variable is not set.")
if not GEMINI_API_KEY:
    raise ValueError("FATAL ERROR: GEMINI_API_KEY environment variable is not set.")
if not SQLITECLOUD_CONNECTION:
    raise ValueError("FATAL ERROR: SQLITECLOUD_CONNECTION_STRING environment variable is not set.")

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# Database Connection Management
def get_db():
    """Get database connection from Flask g object"""
    if 'db' not in g:
        g.db = sq.connect(SQLITECLOUD_CONNECTION)
        g.db.row_factory = sq.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Close database connection at the end of request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def sqldb(function):
    """Decorator to inject database cursor into function"""
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

# Database Initialization
@sqldb
def init_db(c):
    """Initialize database tables"""
    # Users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT DEFAULT 'user' NOT NULL
    );""")
    
    # Saved courses table
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

# Authentication Middleware
def authenticate_token(f):
    """Decorator to require valid JWT token"""
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
    """Decorator to require admin role"""
    @wraps(f)
    @authenticate_token
    def decorated_function(*args, **kwargs):
        if 'role' not in g.user or g.user['role'] != 'admin':
            return jsonify({"error": "Administrator access required."}), 403
        return f(*args, **kwargs)
    return decorated_function

# AI Content Generation
def generate_ai_content(prompt):
    """Generate content using Gemini AI"""
    try:
        model = genai.GenerativeModel(AI_MODEL)
        response = model.generate_content(prompt)
        
        # Clean the response text (remove markdown code blocks if present)
        cleaned_text = re.sub(
            r'^```json\s*|\s*```\s*$', 
            '', 
            response.text, 
            flags=re.MULTILINE | re.DOTALL
        ).strip()
        
        # Parse JSON
        data = json.loads(cleaned_text)
        return data, None
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
        return None, ({"error": "The AI returned an unexpected format. Please try again."}, 500)
    except Exception as e:
        print(f"AI Error: {str(e)}")
        return None, ({"error": f"AI communication error: {str(e)}"}, 500)

# Health Check Endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200

# Authentication Routes
@app.route('/api/signup', methods=['POST'])
@sqldb
def signup(c):
    """User registration endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided."}), 400
        
        full_name = data.get('fullName')
        email = data.get('email')
        password = data.get('password')

        if not all([full_name, email, password]):
            return jsonify({"error": "Missing required fields."}), 400

        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({"error": "Invalid email format."}), 400

        # Validate password length
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters."}), 400

        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Insert user
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
    """User login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided."}), 400
        
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required."}), 400

        # Find user
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()

        if user and bcrypt.check_password_hash(user['password'], password):
            # Create JWT token
            payload = {
                'userId': user['id'],
                'email': user['email'],
                'role': user['role'],
                'exp': datetime.utcnow() + timedelta(days=7)  # 7 days expiry
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

# Profile Routes
@app.route('/api/profile', methods=['GET', 'PUT'])
@authenticate_token
@sqldb
def profile(c):
    """Get or update user profile"""
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

            # Validate email
            if '@' not in email or '.' not in email:
                return jsonify({"error": "Invalid email format."}), 400

            # Update user
            c.execute(
                "UPDATE users SET full_name = ?, email = ? WHERE id = ?", 
                (full_name, email, user_id)
            )
            
            # Fetch updated user
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

# Saved Courses Routes
@app.route('/api/saved-courses', methods=['GET', 'POST'])
@authenticate_token
@sqldb
def saved_courses(c):
    """Get all saved courses or save a new course"""
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

            # Save course
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
    """Delete a saved course"""
    user_id = g.user['userId']
    
    try:
        # Verify course belongs to user
        c.execute(
            "SELECT id FROM saved_courses WHERE id = ? AND user_id = ?",
            (course_id, user_id)
        )
        course = c.fetchone()
        
        if not course:
            return jsonify({"error": "Course not found or unauthorized."}), 404
        
        # Delete course
        c.execute("DELETE FROM saved_courses WHERE id = ?", (course_id,))
        
        return jsonify({"message": "Course deleted successfully."}), 200
        
    except Exception as e:
        print(f"Delete Course Error: {str(e)}")
        return jsonify({"error": "Could not delete course."}), 500

# AI Generation Routes
@app.route('/api/generate-course-with-ai', methods=['POST'])
@authenticate_token
def generate_course():
    """Generate a course outline using AI"""
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
  "startingSalary": "A realistic starting salary in INR (e.g., '₹5L - ₹8L / yr')",
  "skills": ["Skill 1", "Skill 2", "Skill 3", "Skill 4", "Skill 5"],
  "modules": [
    {{ "title": "Module 1: Introduction", "description": "Brief overview of the module." }},
    {{ "title": "Module 2: Core Concepts", "description": "Details about core concepts." }},
    {{ "title": "Module 3: Advanced Topics", "description": "Exploring advanced topics." }},
    {{ "title": "Module 4: Practical Application", "description": "Hands-on projects and case studies." }}
  ]
}}

Important:
- Return ONLY valid JSON, no extra text
- Include 4-6 modules
- Include 5-7 relevant skills
- Make the description engaging and practical
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
    """Generate a career path visualization using AI"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided."}), 400
        
        user_query = data.get('query')
        
        if not user_query:
            return jsonify({"error": "A query is required to generate a career path."}), 400

        prompt = f"""
You are an expert career path creator. Generate a visual career progression for: "{user_query}".

The output must be a clean JSON object, without any markdown formatting or explanations.

The JSON object must have the following structure:
{{
  "title": "Career Path Title",
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
- Include 8-12 roles total
- Distribute roles across three stages: "Entry Level", "Mid Career", "Late Career"
- Each stage should have 2-4 roles
- Use realistic Indian salary ranges (in lakhs per year)
- Progress from junior to senior positions
- Return ONLY valid JSON
"""

        path_data, error = generate_ai_content(prompt)
        
        if error:
            return jsonify(error[0]), error[1]
        
        return jsonify(path_data), 200
        
    except Exception as e:
        print(f"Generate Career Path Error: {str(e)}")
        return jsonify({"error": "Could not generate career path."}), 500

# Admin Routes
@app.route('/api/users', methods=['GET'])
@authenticate_admin
@sqldb
def get_all_users(c):
    """Get all users (admin only)"""
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
    """Delete a user (admin only)"""
    try:
        # Prevent self-deletion
        if user_id == g.user['userId']:
            return jsonify({"error": "Admins cannot delete their own account."}), 403
        
        # Delete user (cascade will delete saved courses)
        c.execute("DELETE FROM users WHERE id = ?", (user_id,))
        
        if c.rowcount == 0:
            return jsonify({"error": "User not found."}), 404
        
        return jsonify({"message": "User and all their data deleted successfully."}), 200
        
    except Exception as e:
        print(f"Delete User Error: {str(e)}")
        return jsonify({"error": "Could not delete user."}), 500

# Frontend Routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Serve the frontend application"""
    return render_template("index.html")

# Application Entry Point
if __name__ == '__main__':
    with app.app_context():
        init_db()
    
    # Use PORT environment variable for Render deployment
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=False)
