from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'secret_key'
DB_FILE = 'database.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT CHECK(role IN ('student', 'faculty'))
        );

        CREATE TABLE IF NOT EXISTS Skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        );

        CREATE TABLE IF NOT EXISTS UserSkills (
            user_id INTEGER,
            skill_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES Users(id),
            FOREIGN KEY(skill_id) REFERENCES Skills(id)
        );

        CREATE TABLE IF NOT EXISTS Projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            status TEXT CHECK(status IN ('pending', 'approved', 'rejected')),
            posted_by INTEGER,
            FOREIGN KEY(posted_by) REFERENCES Users(id)
        );

        CREATE TABLE IF NOT EXISTS Applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            project_id INTEGER,
            status TEXT CHECK(status IN ('applied', 'accepted', 'rejected')),
            FOREIGN KEY(student_id) REFERENCES Users(id),
            FOREIGN KEY(project_id) REFERENCES Projects(id)
        );
        """)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            try:
                c.execute("INSERT INTO Users (name, email, password, role) VALUES (?, ?, ?, ?)",
                          (name, email, password, role))
                conn.commit()
                return redirect('/login')
            except sqlite3.IntegrityError:
                return "User already exists"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM Users WHERE email = ? AND password = ?", (email, password))
            user = c.fetchone()
            if user:
                session['user_id'] = user[0]
                return redirect('/dashboard')
            else:
                return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM Users WHERE id = ?", (session['user_id'],))
        user = c.fetchone()
        user_dict = {"id": user[0], "name": user[1], "email": user[2], "role": user[4]}
    return render_template('dashboard.html', user=user_dict)

@app.route('/apply')
def apply():
    if 'user_id' not in session:
        return redirect('/login')

    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        # Get projects not posted by the current user
        c.execute("""
            SELECT Projects.id, Projects.title, Projects.description, Users.name 
            FROM Projects 
            JOIN Users ON Projects.posted_by = Users.id 
            WHERE Projects.status = 'approved'
        """)
        projects = c.fetchall()

    return render_template('apply.html', projects=projects)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        posted_by = session['user_id']
        status = 'approved'  # or use 'pending' if you plan an approval system

        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO Projects (title, description, posted_by, status) 
                VALUES (?, ?, ?, ?)
            """, (title, description, posted_by, status))
            conn.commit()

        return redirect('/dashboard')

    return render_template('add_project.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    if not os.path.exists(DB_FILE):
        init_db()
    app.run(debug=True)
