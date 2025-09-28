import sqlitecloud as sqlite3
import os

DATABASE_URL = os.environ.get("SQLITECLOUD_CONNECTION_STRING")

def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE_URL)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if commit:
                conn.commit()
                return cursor.lastrowid
                
            if fetchone:
                return cursor.fetchone()
            
            if fetchall:
                return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Database query error: {e}")
        return None
    finally:
        if conn:
            conn.close()

def create_tables():
    create_user_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      full_name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      avatar_url TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    create_saved_courses_table_sql = """
    CREATE TABLE IF NOT EXISTS saved_courses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      course_title TEXT NOT NULL,
      saved_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        execute_query(create_user_table_sql, commit=True)
        print("Users table created or already exists.")
        execute_query(create_saved_courses_table_sql, commit=True)
        print("Saved_courses table created or already exists.")
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

def init_db():
    print("Initializing database...")
    create_tables()
    print("Database initialized.")