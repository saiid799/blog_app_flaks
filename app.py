from flask import Flask, render_template, request, url_for, flash, redirect, session, abort
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ3dW9seHdud2FvbnRrcWxybndkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MTc2NTE5NjEsImV4cCI6MjAzMzIyNzk2MX0.BOrhlrIfnuF0rqXUrExLpeQMhAZ48jXHTjHtvfdQrTQ')

DATABASE_URL = os.getenv('DATABASE_URL', 'postgres://postgres.vwuolxwnwaontkqlrnwd:Msaiid987654321ffF+@aws-0-eu-central-1.pooler.supabase.com:6543/postgres')

def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def get_post(post_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
        post = cur.fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

def get_user_by_email(email):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cur.fetchone()
    conn.close()
    return user

@app.route("/")
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM posts')
        posts = cur.fetchall()
    conn.close()
    return render_template("index.html", posts=posts)

@app.route("/<int:post_id>")
def post(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    post = get_post(post_id)
    return render_template("post.html", post=post)

@app.route("/create", methods=('GET', 'POST'))
def create():
    if 'user_id' not in session:
        flash('Please log in to create a post.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash("Title is required!")
        else:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute("INSERT INTO posts (title, content) VALUES (%s, %s)", (title, content))
                conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template("create.html")

@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    if 'user_id' not in session:
        flash('Please log in to edit a post.')
        return redirect(url_for('login'))

    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            conn = get_connection()
            with conn.cursor() as cur:
                cur.execute('UPDATE posts SET title = %s, content = %s WHERE id = %s', (title, content, id))
                conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template("edit.html", post=post)

@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    if 'user_id' not in session:
        flash('Please log in to delete a post.')
        return redirect(url_for('login'))

    post = get_post(id)
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute('DELETE FROM posts WHERE id = %s', (id,))
        conn.commit()
    conn.close()
    flash(f'"{post["title"]}" was successfully deleted!')
    return redirect(url_for('index'))

@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_admin = 'is_admin' in request.form

        if not username or not email or not password:
            flash('All fields are required!')
        else:
            user = get_user_by_email(email)
            if user:
                flash('Email is already registered!')
            else:
                hashed_password = generate_password_hash(password)
                conn = get_connection()
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO users (username, email, password, is_admin) VALUES (%s, %s, %s, %s)",
                                (username, email, hashed_password, is_admin))
                    conn.commit()
                conn.close()
                return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
            if user['is_admin']:
                return redirect(url_for('admin'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password!')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        abort(403)

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM users')
        users = cur.fetchall()
    conn.close()
    return render_template('admin.html', users=users)

if __name__ == "__main__":
    app.run(debug=True)
