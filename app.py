import os
import json
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from calculator.timetable import list_all_sections, get_section_data, calculate_timetable_classes
from calculator.attendance import calculate_subject_attendance, calculate_overall_attendance
from calculator.prediction import generate_attendance_forecast, generate_recovery_path, calculate_recovery_streak
from calculator.simulator import simulate_leave, simulate_what_if, run_digital_twin_simulations
from chatbot.advisor import process_advisor_query

app = Flask(__name__)
CORS(app)

# Fixed list of allowed section IDs strictly corresponding to the 10 timetable dataset files
ALLOWED_SECTIONS = [
    "section_A",
    "section_B",
    "section_C",
    "section_D",
    "section_E",
    "section_F",
    "section_G",
    "section_H",
    "section_I",
    "section_J"
]

def is_valid_section(sec_id):
    return sec_id in ALLOWED_SECTIONS

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/setup")
def setup():
    return render_template("setup.html")

# --- API ENDPOINTS ---

@app.route("/api/sections", methods=["GET"])
def get_sections():
    """Returns list of all 10 available class sections."""
    sections = list_all_sections()
    # Ensure only allowed sections are returned
    filtered_sections = [s for s in sections if s["id"] in ALLOWED_SECTIONS]
    return jsonify({"sections": filtered_sections})

@app.route("/api/section/<section_id>", methods=["GET"])
def get_section_details(section_id):
    """Returns details for a specific section after strict validation."""
    if not is_valid_section(section_id):
        return jsonify({"error": "Invalid section. Please select one of the available class sections."}), 400

    data = get_section_data(section_id)
    return jsonify({"section": data})

@app.route("/api/calculate", methods=["POST"])
def calculate():
    """
    Main attendance calculation endpoint.
    Strictly validates selected section and loads data for that section only.
    """
    data = request.json or {}
    section_id = data.get("section_id", "section_A")
    if not is_valid_section(section_id):
        return jsonify({"error": "Invalid section. Please select one of the available class sections."}), 400

    start_date = data.get("start_date", "2026-09-28")
    target_date = data.get("target_date", "2026-11-29")
    subjects_input = data.get("subjects", [])

    section_info = get_section_data(section_id)

    # 1. Fetch timetable class counts for the selected section ONLY
    tt_calc = calculate_timetable_classes(section_id, start_date, target_date)
    remaining_by_subject = tt_calc["remaining_by_subject"]

    # 2. Filter or build subjects input to strictly belong to the selected section
    allowed_subject_codes = {s["code"] for s in section_info.get("subjects", [])}
    
    # If provided subjects belong to another section or are empty, reset to section default subjects
    if not subjects_input or any(sub.get("code") not in allowed_subject_codes for sub in subjects_input):
        subjects_input = []
        for s in section_info.get("subjects", []):
            subjects_input.append({
                "code": s["code"],
                "name": s["name"],
                "short_name": s.get("short_name", s["name"]),
                "faculty": s.get("faculty", ""),
                "conducted": 30,
                "attended": 24 # Default ~80% sample
            })
    else:
        # Keep only subjects that belong to this section
        subjects_input = [sub for sub in subjects_input if sub.get("code") in allowed_subject_codes]

    # 3. Calculate per-subject attendance stats
    evaluated_subjects = []
    for sub in subjects_input:
        sub_code = sub.get("code")
        meta = next((s for s in section_info.get("subjects", []) if s["code"] == sub_code), {})
        sub["faculty"] = sub.get("faculty") or meta.get("faculty", "")
        sub["short_name"] = sub.get("short_name") or meta.get("short_name", sub.get("name"))
        
        rem_classes = remaining_by_subject.get(sub_code, 0)
        res = calculate_subject_attendance(sub, rem_classes)
        
        res["recovery_path"] = generate_recovery_path(res)
        res["recovery_streak"] = calculate_recovery_streak(res)
        
        evaluated_subjects.append(res)

    # 4. Overall Attendance Calculation
    overall_summary = calculate_overall_attendance(evaluated_subjects)

    # 5. Attendance Forecast Trend
    forecast = generate_attendance_forecast(section_id, subjects_input, start_date, target_date)

    return jsonify({
        "section": {
            "id": section_info.get("section_id"),
            "name": section_info.get("section_name"),
            "department": section_info.get("department"),
            "year": section_info.get("year"),
            "semester": section_info.get("semester")
        },
        "timetable_summary": {
            "start_date": tt_calc["start_date"],
            "target_date": tt_calc["end_date"],
            "total_remaining_classes": tt_calc["total_remaining"],
            "semester_start": tt_calc["semester_start"],
            "semester_end": tt_calc["semester_end"],
            "by_date": tt_calc["by_date"]
        },
        "overall": overall_summary,
        "subjects": evaluated_subjects,
        "forecast": forecast
    })

@app.route("/api/simulate-leave", methods=["POST"])
def api_simulate_leave():
    """Simulates leave impact on attendance with section validation."""
    data = request.json or {}
    section_id = data.get("section_id", "section_A")
    if not is_valid_section(section_id):
        return jsonify({"error": "Invalid section. Please select one of the available class sections."}), 400

    start_date = data.get("start_date", "2026-09-29")
    end_date = data.get("end_date", "2026-10-01")
    leave_type = data.get("leave_type", "Normal Leave")
    subjects = data.get("subjects", [])
    plan_end_date = data.get("plan_end_date", "2026-11-29")

    res = simulate_leave(section_id, start_date, end_date, leave_type, subjects, plan_end_date)
    return jsonify(res)

@app.route("/api/simulate-what-if", methods=["POST"])
def api_simulate_what_if():
    """Simulates custom what-if scenarios with section validation."""
    data = request.json or {}
    section_id = data.get("section_id", "section_A")
    if not is_valid_section(section_id):
        return jsonify({"error": "Invalid section. Please select one of the available class sections."}), 400

    scenario_type = data.get("scenario_type", "attend_all")
    params = data.get("params", {})
    subjects = data.get("subjects", [])
    plan_end_date = data.get("plan_end_date", "2026-11-29")

    res = simulate_what_if(scenario_type, params, section_id, subjects, plan_end_date)
    return jsonify(res)

@app.route("/api/digital-twin", methods=["POST"])
def api_digital_twin():
    """Returns side-by-side digital twin scenario models."""
    data = request.json or {}
    section_id = data.get("section_id", "section_A")
    if not is_valid_section(section_id):
        return jsonify({"error": "Invalid section. Please select one of the available class sections."}), 400

    subjects = data.get("subjects", [])
    today_str = data.get("today_str", "2026-09-28")
    plan_end_date = data.get("plan_end_date", "2026-11-29")

    res = run_digital_twin_simulations(section_id, subjects, today_str, plan_end_date)
    return jsonify(res)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    """AI Attendance Advisor chatbot query endpoint."""
    data = request.json or {}
    section_id = data.get("section_id", "section_A")
    if not is_valid_section(section_id):
        return jsonify({"error": "Invalid section. Please select one of the available class sections."}), 400

    query = data.get("query", "")
    subjects = data.get("subjects", [])
    today_str = data.get("today_str", "2026-09-28")
    plan_end_date = data.get("plan_end_date", "2026-11-29")

    if not query.strip():
        return jsonify({"answer": "Please ask a question regarding your attendance!"})

    res = process_advisor_query(query, section_id, subjects, today_str, plan_end_date)
    return jsonify(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
