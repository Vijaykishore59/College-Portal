from flask import Flask, render_template, request, redirect, session, url_for, flash
import random
from datetime import datetime 
from models import (
    init_db, add_user, get_user,
    create_test, add_question_to_test,
    record_attempt, get_question_count_for_test,
    get_test_by_id, get_exam_questions,
    get_question_by_id, update_question, delete_question,
    get_student_attempts, get_all_tests, get_questions_by_test,
    get_test_attempt_counts, get_current_test_id,get_user_by_username  # ✅ add this here
)
from datetime import timedelta, datetime
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'super_secret_key'
app.permanent_session_lifetime = timedelta(minutes=30)

if not os.path.exists('database.db'):
    init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']

        success = add_user(username, password, role)
        if success:
            flash("✅ Registered successfully! Please log in.")
            return redirect(url_for('login'))
        else:
            flash("❌ User already exists. Try a different username.")
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip().lower()
        password = request.form['password'].strip()
        role = request.form['role'].strip().lower()
        user = get_user(username, password, role)


        if not username or not password or not role:
            flash("❌ All fields are required.")
            return redirect(url_for('login'))

        user = get_user(username, password, role)
        if user:
            session['username'] = username
            session['role'] = role
            flash("✅ Login successful!")
            return redirect(url_for('faculty_dashboard') if role == 'faculty' else url_for('student_dashboard'))

        flash("❌ Invalid credentials.")
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'username' in session:
        session.clear()
        flash("✅ You have been logged out.")
    else:
        flash("ℹ️ You were not logged in.")
    return redirect(url_for('login'))


@app.route('/student_dashboard')
def student_dashboard():
    if 'username' in session and session['role'] == 'student':
        username = session['username']
        all_tests = get_all_tests()
        attempts = get_student_attempts(username)
        attempted_test_ids = {a[3] for a in attempts}  # a[3] is test_id in attempts

        latest_tests = {}
        for test in all_tests:
            test_id, category, total_qs, start_date, end_date, duration, published = test[:7]

            if published != 1:
                continue  # Skip unpublished tests

            # Keep only the latest published test for each category
            if category not in latest_tests or test_id > latest_tests[category][0]:
                latest_tests[category] = test

        now = datetime.now()
        test_info = []

        for test in latest_tests.values():
            test_id, category, total_qs, start_date, end_date, duration, published = test[:7]

            # Safely parse dates and validate they're in correct format
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                continue  # Skip malformed dates

            # Skip expired tests
            if now > end:
                continue

            # Determine time remaining message
            if now < start:
                remaining = f"Starts in {(start - now).days} day(s)"
            else:
                remaining = f"{(end - now).days} day(s) left"

            test_info.append({
                'test_id': test_id,
                'category': category,
                'attempted': test_id in attempted_test_ids,
                'remaining_time': remaining,
                'duration': duration
            })

        return render_template('student_dashboard.html', test_info=test_info)

    flash("Unauthorized access.")
    return redirect(url_for('login'))



@app.route('/exam/<category>', methods=['GET', 'POST'])
def exam(category):
    if 'username' not in session or session['role'] != 'student':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    username = session['username']
    test_id = get_current_test_id(category)

    if not test_id:
        flash("❌ Test not found or not published.")
        return redirect(url_for('student_dashboard'))

    # Check if already attempted
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM attempts WHERE username = ? AND test_id = ?", (username, test_id))
    attempt = cur.fetchone()
    conn.close()

    if attempt:
        return redirect(url_for('exam_result', category=category))

    # Get questions
    raw_questions = get_exam_questions(category)
    if not raw_questions:
        flash("❌ No questions available for this test.")
        return redirect(url_for('student_dashboard'))

    questions = [{'id': q['id'], 'question': q['question'], 'options': q['options']} for q in raw_questions]

    if request.method == 'POST':
        answers = {}
        for key in request.form:
            if key.startswith('q'):
                qid = int(key[1:])
                answers[qid] = request.form[key]

        try:
            score, total = record_attempt(username, category, answers)
            percentage = round((score / total) * 100, 2) if total else 0
            return render_template('exam_result.html', score=score, total=total, percentage=percentage)
        except Exception as e:
            flash(f"❌ Error submitting exam: {e}")
            return redirect(url_for('student_dashboard'))

    # Get test duration for timer (fallback: 30 mins)
    test = next((t for t in get_all_tests() if t[0] == test_id), None)
    duration = test[5] if test else 30

    return render_template('exam_page.html', questions=questions, category=category, duration=duration)






@app.route('/result/<category>')
def exam_result(category):
    if 'username' not in session or session['role'] != 'student':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    username = session['username']
    test_id = get_current_test_id(category)

    if not test_id:
        flash("❌ No published test found for this category.")
        return redirect(url_for('student_dashboard'))

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # Check for attempt
    cur.execute("SELECT score FROM attempts WHERE username = ? AND test_id = ?", (username, test_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        flash("❌ You have not attempted this test.")
        return redirect(url_for('student_dashboard'))

    score = row[0]

    # Fetch total questions for the test
    cur.execute("SELECT total_qs FROM tests WHERE id = ?", (test_id,))
    result = cur.fetchone()
    conn.close()

    if not result:
        flash("⚠️ Test details not found.")
        return redirect(url_for('student_dashboard'))

    total_qs = result[0]
    percentage = round((score / total_qs) * 100, 2) if total_qs else 0

    return render_template('exam_result.html', score=score, total=total_qs, percentage=percentage)



@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'username' not in session or session['role'] != 'faculty':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    all_tests = get_all_tests()
    incomplete_tests = []
    complete_tests = []
    published_tests = []
    question_counts = {}

    for test in all_tests:
        test_id = test[0]
        total_qs = test[2]
        is_published = test[6]

        uploaded_qs = get_question_count_for_test(test_id)
        question_counts[test_id] = uploaded_qs

        if uploaded_qs < total_qs:
            incomplete_tests.append(test)
        elif is_published == 0:
            complete_tests.append(test)
        else:
            published_tests.append(test)

    analytics = get_test_attempt_counts()

    return render_template(
        'faculty_dashboard.html',
        tests=incomplete_tests,
        review_tests=complete_tests,
        live_tests=published_tests,
        analytics=analytics,
        question_counts=question_counts
    )

@app.route('/upload_question', methods=['POST'])
def upload_question():
    if 'username' not in session or session['role'] != 'faculty':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    question = request.form['question']
    options = request.form.getlist('options')
    answer = request.form['answer']
    test_id = request.form['test_id']

    try:
        # Add the question
        add_question_to_test(test_id, question, options, answer)
        flash("✅ Question uploaded successfully.")

        # Check progress
        uploaded = get_question_count_for_test(test_id)
        total = get_test_by_id(test_id)[2]

        if uploaded >= total:
            # Auto-publish test
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute("UPDATE tests SET published = 1 WHERE id = ?", (test_id,))
            conn.commit()
            conn.close()
            flash("✅ All questions uploaded. Test automatically published.")
            return redirect(url_for('faculty_dashboard'))

    except ValueError as ve:
        flash(f"❌ {str(ve)}")

    return redirect(url_for('review_test', test_id=test_id))




@app.route('/create_test', methods=['POST'])
def create_test_view():
    # Check for faculty authentication first
    if 'username' not in session or session['role'] != 'faculty':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    try:
        category = request.form['category']
        total_qs = int(request.form['total_qs'])
        duration = int(request.form['duration'])
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        created_by = session['username']

        test_id = create_test(category, total_qs, duration, start_date, end_date, created_by)

        if test_id:
            flash("✅ Test created successfully. Please upload questions now.")
            return redirect(url_for('review_test', test_id=test_id))
        else:
            flash("❌ Failed to create test.")

    except Exception as e:
        flash(f"❌ Error while creating test: {str(e)}")

    return redirect(url_for('faculty_dashboard'))




@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        old_password = request.form['old_password'].strip()
        new_password = request.form['new_password'].strip()
        confirm_password = request.form['confirm_password'].strip()

        if not old_password or not new_password or not confirm_password:
            flash("❌ All fields are required.")
            return redirect(url_for('change_password'))

        if new_password != confirm_password:
            flash("❌ New passwords do not match.")
            return redirect(url_for('change_password'))

        username = session['username']
        role = session['role']

        user = get_user(username, old_password, role)
        if not user:
            flash("❌ Old password is incorrect.")
            return redirect(url_for('change_password'))

        try:
            with sqlite3.connect('database.db') as conn:
                cur = conn.cursor()
                cur.execute(
                    "UPDATE users SET password = ? WHERE username = ? AND role = ?",
                    (new_password, username, role)
                )
                conn.commit()
            flash("✅ Password changed successfully.")
            return redirect(url_for('student_dashboard' if role == 'student' else 'faculty_dashboard'))
        except Exception as e:
            flash(f"❌ Error updating password: {str(e)}")
            return redirect(url_for('change_password'))

    return render_template('change_password.html')

@app.route('/review_test/<int:test_id>')
def review_test(test_id):
    if 'username' not in session or session['role'] != 'faculty':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    test = get_test_by_id(test_id)
    if not test:
        flash("❌ Test not found.")
        return redirect(url_for('faculty_dashboard'))

    test_id, category, total_qs, start_date, end_date, duration, published, created_by = test
    questions = get_questions_by_test(test_id)

    return render_template(
        'review_test.html',
        questions=questions,
        test_id=test_id,
        total_qs=total_qs,
        category=category,
        published=published
    )


@app.route('/edit_question/<int:qid>', methods=['GET', 'POST'])
def edit_question(qid):
    if 'username' not in session or session['role'] != 'faculty':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    question = get_question_by_id(qid)
    if not question:
        flash("❌ Question not found.")
        return redirect(url_for('faculty_dashboard'))

    question_id, test_id, question_text, options_str, correct_answer = question
    options = options_str.split('|')

    # Optional: Block editing if the test is already published
    test = get_test_by_id(test_id)
    if test and test[6] == 1:  # test[6] = published
        flash("⚠️ Test is already published. You cannot edit questions.")
        return redirect(url_for('review_test', test_id=test_id))

    if request.method == 'POST':
        new_question = request.form['question']
        new_options = request.form.getlist('options')
        new_answer = request.form['answer']

        update_question(qid, new_question, new_options, new_answer)
        flash("✅ Question updated successfully.")
        return redirect(url_for('review_test', test_id=test_id))

    return render_template(
    'edit_question.html',
    test_id=test_id,
    question=question_text,
    options=options,
    answer=correct_answer,
    total_qs=get_test_by_id(test_id)[2],
    questions=get_questions_by_test(test_id),
    can_edit=(test[6] == 0)  # Only allow editing if test is not published
)


@app.route('/delete_question/<int:qid>')
def delete_question_route(qid):
    if 'username' not in session or session['role'] != 'faculty':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    question = get_question_by_id(qid)
    if not question:
        flash("❌ Question not found.")
        return redirect(url_for('faculty_dashboard'))

    test_id = question[1]

    # Check if test is published; if so, prevent deletion
    test = get_test_by_id(test_id)
    if test and test[6] == 1:  # published column
        flash("⚠️ Cannot delete questions from a published test.")
        return redirect(url_for('review_test', test_id=test_id))

    delete_question(qid)
    flash("🗑️ Question deleted successfully.")
    return redirect(url_for('review_test', test_id=test_id))


@app.route('/confirm_publish/<int:test_id>', methods=['POST'])
def confirm_test_publish(test_id):
    if 'username' not in session or session['role'] != 'faculty':
        flash("❌ Unauthorized access.")
        return redirect(url_for('login'))

    test = get_test_by_id(test_id)
    if not test:
        flash("❌ Test not found.")
        return redirect(url_for('faculty_dashboard'))

    question_count = get_question_count_for_test(test_id)
    required_questions = test[2]  # total_qs

    if question_count == required_questions:
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("UPDATE tests SET published = 1 WHERE id = ?", (test_id,))
        conn.commit()
        conn.close()
        flash("✅ Test published successfully.")
    else:
        flash(f"❌ Cannot publish. {required_questions - question_count} more questions needed.")

    return redirect(url_for('faculty_dashboard'))

@app.route("/stats")
def stats():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    attempts = get_student_attempts(username)

    return render_template("stats.html", attempts=attempts)

from models import get_user_by_username

@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for("login"))

    student = get_user_by_username(session["username"])
    if not student:
        return "User not found", 404

    return render_template("profile.html", student=student)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)









