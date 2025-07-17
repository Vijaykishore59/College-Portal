import sqlite3
from datetime import datetime

DB_NAME = 'database.db'

# ========== INIT DB ==========
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Users table
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )''')

    # Tests table
    cur.execute('''CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        total_qs INTEGER NOT NULL,
        start_date TEXT,
        end_date TEXT,
        duration INTEGER,
        published INTEGER DEFAULT 0,
        created_by TEXT
    )''')

    # Questions table
    cur.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER,
        question TEXT,
        options TEXT,
        answer TEXT,
        upload_time TEXT
    )''')

    # Attempts table
    cur.execute('''CREATE TABLE IF NOT EXISTS attempts (
        username TEXT NOT NULL,
        category TEXT NOT NULL,
        test_id INTEGER,
        score INTEGER NOT NULL,
        timestamp TEXT NOT NULL
    )''')

    conn.commit()
    conn.close()


# ========== DB Maintenance ==========
def add_score_column():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE attempts ADD COLUMN score INTEGER")
        print("✅ 'score' column added to 'attempts' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ 'score' column already exists.")
        else:
            raise e
    conn.commit()
    conn.close()

def add_test_id_column():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE attempts ADD COLUMN test_id INTEGER")
        print("✅ 'test_id' column added to 'attempts' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ 'test_id' column already exists.")
        else:
            raise
    conn.commit()
    conn.close()


# ========== USERS ==========
def add_user(username, password, role):
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username.lower().strip(), password.strip(), role.lower().strip())
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False
def get_user(username, password, role):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND role=?",
        (username.lower().strip(), password.strip(), role.lower().strip())
    )
    user = cur.fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "name": row[0].capitalize(),
            "username": row[0],
            "role": row[1]
        }
    else:
        return None



# ========== TESTS ==========
def create_test(category, total_qs, duration, start_date, end_date, created_by):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO tests (category, total_qs, duration, start_date, end_date, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (category, total_qs, duration, start_date, end_date, created_by))
    conn.commit()
    test_id = cur.lastrowid
    conn.close()
    return test_id

def get_all_tests():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tests ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_test_by_id(test_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tests WHERE id=?", (test_id,))
    test = cur.fetchone()
    conn.close()
    return test

def get_question_count_for_test(test_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions WHERE test_id=?", (test_id,))
    count = cur.fetchone()[0]
    conn.close()
    return count


# ========== QUESTIONS ==========
def is_duplicate_question(test_id, question_text):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM questions WHERE test_id=? AND question=?",
        (test_id, question_text.strip())
    )
    exists = cur.fetchone()
    conn.close()
    return exists is not None

def add_question_to_test(test_id, question, options_list, answer):
    options_cleaned = [opt.strip() for opt in options_list if opt.strip()]

    if len(options_cleaned) < 2:
        raise ValueError("At least two unique options are required.")
    if len(set(options_cleaned)) != len(options_cleaned):
        raise ValueError("Duplicate options found.")
    if answer.strip() not in options_cleaned:
        raise ValueError("Answer must match one of the options.")
    if is_duplicate_question(test_id, question):
        raise ValueError("Duplicate question found in the same test.")

    options_str = '|'.join(options_cleaned)
    upload_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        INSERT INTO questions (test_id, question, options, answer, upload_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (test_id, question.strip(), options_str, answer.strip(), upload_time))
    conn.commit()
    conn.close()

def get_question_by_id(qid):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, test_id, question, options, answer FROM questions WHERE id=?", (qid,))
    row = cur.fetchone()
    conn.close()
    return row

def update_question(qid, question, options_list, answer):
    options_str = '|'.join(options_list)
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        UPDATE questions SET question=?, options=?, answer=? WHERE id=?
    ''', (question.strip(), options_str, answer.strip(), qid))
    conn.commit()
    conn.close()

def delete_question(qid):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM questions WHERE id=?", (qid,))
    conn.commit()
    conn.close()

def get_questions_by_test(test_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE test_id = ?", (test_id,))
    questions = cur.fetchall()
    conn.close()
    return questions

def get_test_attempt_counts():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT category, COUNT(*) FROM attempts GROUP BY category
    ''')
    result = cur.fetchall()
    conn.close()
    return result


# ========== ATTEMPTS ==========
def record_attempt(username, category, answers):
    # 1. Get current test ID for the category
    test_id = get_current_test_id(category)
    if not test_id:
        return 0, 0  # No test found

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # 2. Fetch correct answers for all questions in this test
    cur.execute("SELECT id, answer FROM questions WHERE test_id = ?", (test_id,))
    correct_answers = dict(cur.fetchall())  # {question_id: correct_answer}

    # 3. Compare submitted answers to correct ones
    score = 0
    for qid, user_answer in answers.items():
        correct_answer = correct_answers.get(qid)
        if correct_answer and user_answer.strip().lower() == correct_answer.strip().lower():
            score += 1

    total = len(correct_answers)

    # 4. Record the attempt
    cur.execute(
        "INSERT INTO attempts (username, category, score, test_id, timestamp) VALUES (?, ?, ?, ?, datetime('now'))",
        (username, category, score, test_id)
    )
    conn.commit()
    conn.close()

    return score, total


def get_current_test_id(category):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id FROM tests WHERE category = ? AND published = 1 ORDER BY id DESC LIMIT 1", (category,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else None

def get_student_attempts(username):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        SELECT category, timestamp, score, test_id
        FROM attempts
        WHERE username = ?
    ''', (username,))
    result = cur.fetchall()
    conn.close()
    return result


# ========== EXAM QUESTIONS ==========
def get_exam_questions(category):
    test_id = get_current_test_id(category)
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM questions WHERE test_id = ?", (test_id,))
    questions = []
    for row in cur.fetchall():
        options = row['options'].split('|')  # Must split string into list
        questions.append({
            'id': row['id'],
            'question': row['question'],
            'options': options,
            'answer': row['answer']
        })
    conn.close()
    return questions

# ========== DB Maintenance ==========
def add_test_id_column():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE attempts ADD COLUMN test_id INTEGER")
        print("✅ 'test_id' column added to 'attempts' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("⚠️ 'test_id' column already exists.")
        else:
            raise
    conn.commit()
    conn.close()






