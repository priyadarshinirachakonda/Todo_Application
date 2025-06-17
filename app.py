import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, g

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'todo.db'

# --- DB Connection ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- Signup ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('signup.html', error="Username already exists.")

    return render_template('signup.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = get_db().cursor()
        cursor.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials.")

    return render_template('login.html')

# --- Home / Todos Page ---
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cursor = get_db().cursor()
    cursor.execute('SELECT todo_id, task FROM todos WHERE user_id = ?', (session['user_id'],))
    todos = cursor.fetchall()

    return render_template('todo.html', todos=todos)

# --- Add Todo ---
@app.route('/add', methods=['POST'])
def add_todo():
    if 'user_id' in session:
        task = request.form.get('todo')
        if task:
            user_id = session['user_id']
            cursor = get_db().cursor()

            # ✅ Get the next todo_id for this user
            cursor.execute('SELECT MAX(todo_id) FROM todos WHERE user_id = ?', (user_id,))
            max_todo_id = cursor.fetchone()[0]
            next_todo_id = 1 if max_todo_id is None else max_todo_id + 1

            # ✅ Insert the new todo with per-user todo_id
            cursor.execute(
                'INSERT INTO todos (user_id, todo_id, task) VALUES (?, ?, ?)',
                (user_id, next_todo_id, task)
            )
            get_db().commit()
    return redirect(url_for('home'))


# --- Delete Todo ---
@app.route('/delete/<int:todo_id>')
def delete_todo(todo_id):
    if 'user_id' in session:
        cursor = get_db().cursor()
        cursor.execute('DELETE FROM todos WHERE todo_id = ? AND user_id = ?', (todo_id, session['user_id']))
        get_db().commit()
    return redirect(url_for('home'))

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
