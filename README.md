# 🧠 AutoJobApplier

Automated job application bot for LinkedIn (and soon Indeed), built with Python and Selenium. It logs into your account, searches for roles, and applies using "Easy Apply" (or similar) when available.

---

## 🚀 Features

- 🔐 Secure login via `secrets.config`
- 🔎 Automated job searching by title and location
- 📌 Resume auto-upload
- 🗒️ Google Sheets tracker (or CSV fallback)
- 🧠 Smart question detection with local database cache
- ✅ Modular and extensible (support for Indeed coming next)

---

## 📁 Folder Structure

```bash
AutoJobApplier/
├── linkedin_backend.py        # Core logic for LinkedIn
├── indeed_backend.py          # (Coming soon)
├── tracker_updater.py         # Updates Google Sheet or CSV
├── question_db.json           # Stores Q&A cache
├── secrets.config             # Your credentials and config
├── Resources/
│   ├── resume.pdf             # Your resume (for uploads)
│   └── tracker_backup.csv     # Fallback application tracker
├── linkedin.py                # Front-end runner for LinkedIn
├── indeed.py                  # (Coming soon)
└── README.md
```

---

## 💪 Setup

1. Clone this repo
2. Install dependencies (use virtualenv recommended):
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `secrets.config` file with:
   ```
   username_linkedin=your_email
   password_linkedin=your_password
   spreadsheet_tracker=https://docs.google.com/spreadsheets/d/your_sheet_id/edit
   ```
4. Put your resume in `Resources/resume.pdf`

---

## ▶️ Run the bot

```bash
python linkedin.py --debug
```

---

## 🧩 Tracker Details

After applying to a job, the following is logged:

- Company Name  
- Job Title  
- Job Level  
- Salary Range  
- Application Link  
- Status (`Applied` by default)

If Google Sheets is unreachable, it falls back to `Resources/tracker_backup.csv`.

---

## 🧠 Question Handler

If an application asks, e.g. _"How many years of experience with React?"_, the bot will:
- Check `question_db.json` for a known answer
- If not found, it will prompt you in the console
- Your answer is then saved for future reuse

---

## ⚠️ Notes

- Currently supports only **Safari WebDriver**
- You must be **logged into your system Safari** for seamless operation
