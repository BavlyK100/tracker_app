# 10-Day Goal Tracker
 
A personal habit-tracking web app built with **Flask** (Python). Create a cycle with your own start and end dates, add the goals you want to track, and check off each day as you go — with progress stats, streaks, daily notes, and reflection built right in.
 
Built as a learning project to understand how Flask actually works (routing, forms, templates, data flow) — not by copying a template, but by building every piece from scratch.
 
---
 
## What it does
 
- **Custom cycles** — pick any name, start date, and end date (not locked to 10 days)
- **Goals** — add, rename, delete, and reorder goals at any time during a cycle
- **Progress tracking** — see percent complete per goal and overall, plus current and best streaks
- **Daily Notes** — jot a short note for any day of the cycle (key wins, challenges, lessons learned) via a Notes panel next to Edit — helpful context for later reflection
- **Archive** — end a cycle to save it for later, or cancel one you don't want to keep
- **Reflection** — optionally answer 3 quick questions when a cycle ends (what went well, what didn't, what you learned)
- **PDF export** — download any saved cycle as a PDF, with the option to include reflection + daily notes or just the goals grid
- **Dark / light theme** — toggle in the nav bar, remembered across visits via a cookie
- **Safety popups** — confirms before anything gets permanently deleted or archived
## Tech used
 
- **Flask** — the web framework running everything
- **Jinja2** — Flask's templating language, used to build the HTML pages
- **WeasyPrint** — converts HTML into PDF files for the export feature
- **JSON files** — where all the data lives (no database — kept simple on purpose)
- **Plain CSS** — no JavaScript anywhere, even the popups and theme toggle are done with CSS-only tricks (checkbox hack) or a Flask cookie
## Project structure
 
```
tracker_app/
├── app.py                  # All the routes and logic live here
├── data/
│   ├── current_cycle.json  # The cycle you're actively working on
│   └── saved_cycles.json   # Archived cycles
├── templates/
│   ├── base.html           # Shared layout (nav bar, theme toggle, footer)
│   ├── dashboard.html      # Main page — active cycle, goals, and daily notes
│   ├── new_cycle.html      # Form to start a new cycle
│   ├── saved.html          # List of archived cycles
│   ├── cycle_detail.html   # View one archived cycle (goals, reflection, notes)
│   └── pdf_cycle.html      # Print-friendly version used for PDF export
└── static/
    └── css/
        └── style.css       # All the styling
```
 
## Running it locally
 
1. Install the requirements:
```
   pip install flask weasyprint
```
2. From the project folder, run:
```
   python app.py
```
3. Open your browser to `http://127.0.0.1:5000`
## Notes
 
This is a single-user app — it doesn't have logins or separate accounts, so it's meant for one person's personal use (or trying it out locally), not for multiple people sharing the same deployment.
 
---
 
Built by Bavly Kamel as a hands-on way to learn Flask, one feature at a time.