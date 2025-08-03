🏓 Pickleball Reservation Automation — Project Overview
This project automates the daily workflow for Pickleball reservations using a combination of:

Google Forms → for collecting availability & time slot preferences

Google Sheets (linked to the form) → where all responses are stored

Python script (read_slots.py) → processes responses & manages reservations

GitHub Actions → runs automation jobs on a schedule and optionally saves results

Google Apps Script (optional) → emails the daily form to participants

🔄 How Everything Fits Together
1. Daily Form Distribution
A Google Form is used to collect who wants to play pickleball and their preferred time slots.

A Google Apps Script (sendPickleballFormDaily) sends the form link to all participants every day at 12 AM (or another time you configure).

This runs via a time-driven trigger in Google Apps Script.

Players click the link and fill in their preferences.

2. Form Responses
All form submissions are automatically stored in a linked Google Sheet.

This sheet is the single source of truth for availability each day.

3. Python Script — read_slots.py
The script connects to the Google Sheet and:

Reads the latest responses.

Processes availability.

Optionally makes reservations (via Playwright automation).

Writes results into an output file (e.g., slots.json).

4. Automation with GitHub Actions
A workflow file in .github/workflows/ runs read_slots.py automatically on a schedule (e.g., every day at midnight).

Workflow steps:

Checkout repo.

Install Python + dependencies.

Run read_slots.py.

Optionally commit results (e.g., slots.json) back to the repo so changes are tracked in Git.

5. Repository File Structure
bash
Copy
Edit
📂 your-repo/
 ┣ 📂 .github/
 ┃  ┗ 📂 workflows/
 ┃     ┗ 📄 run_read_slots.yml   # GitHub Actions workflow
 ┣ 📄 read_slots.py              # Main script that processes form responses
 ┣ 📄 requirements.txt           # Python dependencies (e.g., gspread, playwright)
 ┣ 📄 slots.json                 # Auto-updated file with daily results
 ┣ 📄 README.md                  # Project documentation
⚙️ Automation Summary
Google Apps Script → Sends the form link daily via email.

Google Form → Google Sheet → Collects and stores responses automatically.

Python Script (read_slots.py) → Processes responses and updates reservation info.

GitHub Actions → Runs read_slots.py daily on a schedule, commits results back if needed.

✅ Benefits
Fully automated daily reminder + data collection.

No manual checking of slots — script handles it.

Results tracked in GitHub (slots.json history).

Easy to extend (e.g., Slack/Discord notifications, auto-booking via Playwright).
