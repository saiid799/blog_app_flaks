import psycopg2
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Load environment variables from .env file
load_dotenv()

# Get the DATABASE_URL from the environment variables
DATABASE_URL = os.getenv('postgres://postgres.vwuolxwnwaontkqlrnwd:Msaiid987654321ffF+@aws-0-eu-central-1.pooler.supabase.com:6543/postgres')

# Debugging: Print the DATABASE_URL to check its format
print(f"DATABASE_URL: {DATABASE_URL}")

# Check if DATABASE_URL is not None or empty
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set or empty")

# Connect to the database
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Execute the SQL statements to create the tables
cur.execute("""
DROP TABLE IF EXISTS posts;
DROP TABLE IF EXISTS users;

CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE
);
""")

# Insert a default admin user
cur.execute("INSERT INTO users (username, email, password, is_admin) VALUES (%s, %s, %s, %s)",
            ('admin', 'admin@blog.com', generate_password_hash('123456'), True))

# Commit the transaction and close the connection
conn.commit()
cur.close()
conn.close()
