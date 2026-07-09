# app.py
# Main Flask application for the 10-Day Goal Tracker.

from flask import Flask, render_template, redirect, url_for, request
import json
import os
from datetime import date, timedelta
from weasyprint import HTML
from flask import Response

app = Flask(__name__)

DATA_DIR = "data"
CURRENT_CYCLE_FILE = os.path.join(DATA_DIR, "current_cycle.json")
SAVED_CYCLES_FILE = os.path.join(DATA_DIR, "saved_cycles.json")


def load_json(filepath):
    """Read and return JSON data from a file."""
    with open(filepath, "r") as f:
        return json.load(f)


def save_json(filepath, data):
    """Write JSON data to a file (pretty-printed for readability)."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


def get_cycle_dates(start_date_str, end_date_str):
    """Given a start_date and end_date, return every real calendar date
    in that range (inclusive) as strings like 'Jul 02'."""
    start = date.fromisoformat(start_date_str)
    end = date.fromisoformat(end_date_str)
    num_days = (end - start).days + 1
    return [(start + timedelta(days=i)).strftime("%b %d") for i in range(num_days)]


def cycle_length(cycle):
    """How many days long this cycle is, based on its start/end dates."""
    start = date.fromisoformat(cycle["start_date"])
    end = date.fromisoformat(cycle["end_date"])
    return (end - start).days + 1


def compute_streaks(days, start_date_str):
    """longest_streak = best run of checked days anywhere in the array
    (no date awareness -- easy to test by toggling any boxes).
    current_streak = consecutive checked days counting back from TODAY
    (date-aware -- this is the only definition of "current" that's
    actually meaningful; future/untouched days don't count)."""
    # Longest streak: pure array scan, ignores dates entirely
    longest = 0
    running = 0
    for checked in days:
        if checked:
            running += 1
            longest = max(longest, running)
        else:
            running = 0

    # Current streak: only counts up through today
    start = date.fromisoformat(start_date_str)
    today = date.today()
    days_elapsed = (today - start).days + 1
    days_elapsed = max(0, min(days_elapsed, len(days)))

    current = 0
    for checked in reversed(days[:days_elapsed]):
        if checked:
            current += 1
        else:
            break

    return current, longest

def compute_progress(cycle):
    """Given a cycle, return (goal_progress dict, overall cycle percent).
    goal_progress is keyed by goal id:
    {"checked": x, "total": y, "percent": z, "current_streak": a, "longest_streak": b}.
    Shared by the dashboard (per-goal + overall) and saved cycles (overall only)."""
    total_days = cycle_length(cycle)
    goal_progress = {}
    total_checked = 0
    total_cells = 0

    for goal in cycle["goals"]:
        checked = sum(goal["days"])
        percent = round(checked / total_days * 100) if total_days else 0
        current_streak, longest_streak = compute_streaks(goal["days"], cycle["start_date"])

        goal_progress[goal["id"]] = {
            "checked": checked,
            "total": total_days,
            "percent": percent,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
        }
        total_checked += checked
        total_cells += total_days

    cycle_percent = round(total_checked / total_cells * 100) if total_cells else 0
    return goal_progress, cycle_percent


@app.route("/")
@app.route("/dashboard")
def dashboard():
    cycle = load_json(CURRENT_CYCLE_FILE)

    if not cycle:
        return render_template("dashboard.html", cycle=None, dates=None)

    dates = get_cycle_dates(cycle["start_date"], cycle["end_date"])
    goal_progress, cycle_percent = compute_progress(cycle)

    return render_template(
        "dashboard.html",
        cycle=cycle,
        dates=dates,
        goal_progress=goal_progress,
        cycle_percent=cycle_percent,
    )


@app.route("/new_cycle", methods=["GET", "POST"])
def new_cycle():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        start_date_str = request.form.get("start_date", "")
        end_date_str = request.form.get("end_date", "")

        if not name:
            error = "Please enter a name for this cycle."
        elif not start_date_str or not end_date_str:
            error = "Please pick both a start and end date."
        else:
            start = date.fromisoformat(start_date_str)
            end = date.fromisoformat(end_date_str)

            if end < start:
                error = "End date can't be before the start date."
            else:
                saved_cycles = load_json(SAVED_CYCLES_FILE)
                name_taken = any(c.get("name") == name for c in saved_cycles)

                if name_taken:
                    error = f'A cycle named "{name}" already exists. Please choose a different name.'
                else:
                    new_cycle_data = {
                        "name": name,
                        "start_date": start_date_str,
                        "end_date": end_date_str,
                        "next_goal_id": 1,
                        "goals": [],
                    }
                    save_json(CURRENT_CYCLE_FILE, new_cycle_data)
                    return redirect(url_for("dashboard"))

    return render_template("new_cycle.html", error=error)


@app.route("/toggle/<goal_id>/<int:day_index>")
def toggle(goal_id, day_index):
    cycle = load_json(CURRENT_CYCLE_FILE)

    for goal in cycle["goals"]:
        if goal["id"] == goal_id:
            goal["days"][day_index] = not goal["days"][day_index]
            break

    save_json(CURRENT_CYCLE_FILE, cycle)
    return redirect(url_for("dashboard"))


@app.route("/add_goal", methods=["POST"])
def add_goal():
    goal_name = request.form.get("goal_name", "").strip()

    if goal_name:
        cycle = load_json(CURRENT_CYCLE_FILE)
        next_id = cycle.get("next_goal_id", 1)

        new_goal = {
            "id": f"goal_{next_id}",
            "name": goal_name,
            "days": [False] * cycle_length(cycle),
        }
        cycle["goals"].append(new_goal)
        cycle["next_goal_id"] = next_id + 1

        save_json(CURRENT_CYCLE_FILE, cycle)

    return redirect(url_for("dashboard"))


@app.route("/rename_goal/<goal_id>", methods=["POST"])
def rename_goal(goal_id):
    new_name = request.form.get("new_name", "").strip()

    if new_name:
        cycle = load_json(CURRENT_CYCLE_FILE)
        for goal in cycle["goals"]:
            if goal["id"] == goal_id:
                goal["name"] = new_name
                break
        save_json(CURRENT_CYCLE_FILE, cycle)

    return redirect(url_for("dashboard"))


@app.route("/delete_goal/<goal_id>")
def delete_goal(goal_id):
    cycle = load_json(CURRENT_CYCLE_FILE)
    cycle["goals"] = [g for g in cycle["goals"] if g["id"] != goal_id]
    save_json(CURRENT_CYCLE_FILE, cycle)
    return redirect(url_for("dashboard"))


@app.route("/move_goal_up/<goal_id>")
def move_goal_up(goal_id):
    # Swap this goal with the one directly above it in the list
    cycle = load_json(CURRENT_CYCLE_FILE)
    goals = cycle["goals"]

    for i, g in enumerate(goals):
        if g["id"] == goal_id:
            if i > 0:  # can't move the top goal any higher
                goals[i - 1], goals[i] = goals[i], goals[i - 1]
            break

    save_json(CURRENT_CYCLE_FILE, cycle)
    return redirect(url_for("dashboard"))


@app.route("/move_goal_down/<goal_id>")
def move_goal_down(goal_id):
    # Swap this goal with the one directly below it in the list
    cycle = load_json(CURRENT_CYCLE_FILE)
    goals = cycle["goals"]

    for i, g in enumerate(goals):
        if g["id"] == goal_id:
            if i < len(goals) - 1:  # can't move the bottom goal any lower
                goals[i + 1], goals[i] = goals[i], goals[i + 1]
            break

    save_json(CURRENT_CYCLE_FILE, cycle)
    return redirect(url_for("dashboard"))


@app.route("/saved")
def saved():
    saved_cycles = load_json(SAVED_CYCLES_FILE)

    # Attach an overall completion percent to each cycle for display
    for cycle in saved_cycles:
        _, cycle["percent"] = compute_progress(cycle)

    return render_template("saved.html", saved_cycles=saved_cycles)


@app.route("/saved/<cycle_id>")
def cycle_detail(cycle_id):
    saved_cycles = load_json(SAVED_CYCLES_FILE)
    cycle = None
    for c in saved_cycles:
        if c["id"] == cycle_id:
            cycle = c
            break

    dates = get_cycle_dates(cycle["start_date"], cycle["end_date"]) if cycle else None
    return render_template("cycle_detail.html", cycle=cycle, dates=dates)


@app.route("/delete_saved_cycle/<cycle_id>")
def delete_saved_cycle(cycle_id):
    # Permanently remove one archived cycle
    saved_cycles = load_json(SAVED_CYCLES_FILE)
    saved_cycles = [c for c in saved_cycles if c["id"] != cycle_id]
    save_json(SAVED_CYCLES_FILE, saved_cycles)
    return redirect(url_for("saved"))


@app.route("/end_cycle", methods=["GET", "POST"])
def end_cycle():
    # Archive the current cycle, then clear it -- used when a cycle is DONE
    cycle = load_json(CURRENT_CYCLE_FILE)
    cycle["id"] = cycle["name"]

    # Reflection answers are optional -- store whatever was filled in,
    # blank string if the user skipped a question
    cycle["reflection"] = {
        "achievement": request.form.get("achievement", "").strip(),
        "improvement": request.form.get("improvement", "").strip(),
        "lesson": request.form.get("lesson", "").strip(),
    }

    saved_cycles = load_json(SAVED_CYCLES_FILE)
    saved_cycles.append(cycle)
    save_json(SAVED_CYCLES_FILE, saved_cycles)

    save_json(CURRENT_CYCLE_FILE, {})

    return redirect(url_for("dashboard"))


@app.route("/cancel_cycle")
def cancel_cycle():
    # Discard the current cycle WITHOUT archiving it -- used for false
    # starts or test cycles you don't want cluttering saved_cycles.json
    save_json(CURRENT_CYCLE_FILE, {})
    return redirect(url_for("dashboard"))

@app.route("/export_pdf/<cycle_id>")
def export_pdf(cycle_id):
    # Find the saved cycle, same lookup as cycle_detail
    saved_cycles = load_json(SAVED_CYCLES_FILE)
    cycle = None
    for c in saved_cycles:
        if c["id"] == cycle_id:
            cycle = c
            break

    if not cycle:
        return redirect(url_for("saved"))

    dates = get_cycle_dates(cycle["start_date"], cycle["end_date"])

    # ?include_reflection=yes or =no, chosen by the user in the popup
    include_reflection = request.args.get("include_reflection", "no") == "yes"
    reflection = cycle.get("reflection", {})

    # Render the print-friendly template to an HTML string first
    html_string = render_template(
        "pdf_cycle.html",
        cycle=cycle,
        dates=dates,
        show_reflection=include_reflection,
        reflection=reflection,
    )

    # Convert that HTML string into PDF bytes
    pdf_bytes = HTML(string=html_string).write_pdf()

    # Send it back as a downloadable file, not displayed inline
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{cycle["name"]}.pdf"'
        },
    )


if __name__ == "__main__":
    app.run(debug=True)