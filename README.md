
# 📚 College Portal

A web-based portal for managing student aptitude exams, communication skill evaluations, and faculty question uploads. Built using Python with Flask, SQLite, and SQLAlchemy.

---

## 🚀 Features

- 👨‍🎓 **Student Login/Signup**  
- 👩‍🏫 **Faculty Login/Signup**  
- 📝 Students can attend:
  - Aptitude exams
  - Verbal exams
  - Communication skill evaluations
- 🕓 Exams are accessible for 24 hours only.
- 📊 Faculty can:
  - Upload questions weekly
  - Track student attempts
  - Monitor branch-wise exam participation

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Database**: SQLite (`database.db`)
- **Frontend**: HTML (can be extended with CSS/JS)
- **Others**: Git for version control

---
## Demo Screenshots
<img width="1884" height="910" alt="Screenshot 2025-07-18 010316" src="https://github.com/user-attachments/assets/452c9e73-d430-4b07-b1e7-7f1564b75bba" />
<img width="1896" height="835" alt="Screenshot 2025-07-18 010352" src="https://github.com/user-attachments/assets/b4e76b05-2174-4f52-a5f2-7339ebb6e4c8" />
<img width="1877" height="905" alt="Screenshot 2025-07-18 010455" src="https://github.com/user-attachments/assets/28617a25-0988-4f2f-997f-27fdd5e7f899" />
<img width="1884" height="894" alt="Screenshot 2025-07-18 010555" src="https://github.com/user-attachments/assets/4c2b63e8-b12e-4009-b48e-145901f7f334" />



## 📁 Project Structure

```
college_portal/
│
├── app.py               # Main Flask app with routes
├── models.py            # SQLAlchemy models for Student and Faculty
├── database.py          # Database initialization logic
├── database.db          # SQLite DB (auto-generated)
├── requirements.txt     # Required Python packages
└── .git/                # Git version control data
```

---

## 🔧 Installation

1. **Clone the Repository**
   ```bash
   git clone <your-repo-url>
   cd college_portal
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python app.py
   ```

5. Visit `http://localhost:5000` in your browser.

---

## 🗃️ Database Models

- `Student`: Stores student information and login details
- `Faculty`: Stores faculty login credentials and uploaded questions

---

## ✅ To Do / Enhancements

- Add frontend UI using HTML/CSS/JS
- Email notification system for exam alerts
- Timer-based exam interface
- Admin panel for portal-wide control

---

## 📄 License

This project is for educational/demo purposes. Modify and enhance freely.
