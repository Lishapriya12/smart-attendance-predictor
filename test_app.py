import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from calculator.timetable import list_all_sections, get_section_data, calculate_timetable_classes
from calculator.attendance import calculate_subject_attendance, calculate_overall_attendance
from calculator.prediction import generate_attendance_forecast, generate_recovery_path
from calculator.simulator import simulate_leave, simulate_what_if, run_digital_twin_simulations
from chatbot.advisor import process_advisor_query

print("=== 1. Testing Sections List ===")
sections = list_all_sections()
print(f"Found {len(sections)} sections.")
assert len(sections) == 10, "Should have 10 sections"

print("=== 2. Testing Timetable Calculator ===")
tt = calculate_timetable_classes("section_A", "2026-09-28", "2026-11-29")
print(f"Remaining classes for Section A: {tt['total_remaining']}")
print(f"Remaining by subject: {tt['remaining_by_subject']}")

print("=== 3. Testing Attendance Math (Subject & Overall) ===")
sample_sub = {"code": "CS501", "name": "Java Programming", "conducted": 40, "attended": 32}
sub_res = calculate_subject_attendance(sample_sub, tt['remaining_by_subject'].get("CS501", 0))
print("Java Stats:")
print(f"  Current %: {sub_res['current_pct']}%")
print(f"  Req for 75%: {sub_res['required_75']} classes")
print(f"  Safe to miss: {sub_res['can_miss_75']} classes")
print(f"  Status: {sub_res['status_icon']} {sub_res['status_label']}")

print("=== 4. Testing Irreversible Detention Handling ===")
bad_sub = {"code": "CS504", "name": "Computer Networks", "conducted": 40, "attended": 10} # 25% current
bad_res = calculate_subject_attendance(bad_sub, 10) # 10 remaining -> max possible (10+10)/50 = 40% < 75%
print("Bad Sub Stats:")
print(f"  Max possible: {bad_res['max_possible_pct']}%")
print(f"  Detention alert: {bad_res['is_detention']}")
assert bad_res['is_detention'] == True, "Should flag detention"

print("=== 5. Testing Leave Simulation ===")
sample_subjects = [
    {"code": "CS501", "name": "Java Programming", "conducted": 40, "attended": 32},
    {"code": "CS502", "name": "Database Management Systems", "conducted": 40, "attended": 31},
    {"code": "CS504", "name": "Computer Networks", "conducted": 40, "attended": 29}
]
sim = simulate_leave("section_A", "2026-09-29", "2026-10-01", "Normal Leave", sample_subjects)
print(f"Leave affected classes: {sim['total_affected_classes']}")
print(f"New overall %: {sim['overall']['overall_current_pct']}%")

print("=== 6. Testing Digital Twin ===")
twins = run_digital_twin_simulations("section_A", sample_subjects)
print(f"Digital Twin baseline: {twins['baseline']['overall_pct']}% | Perfect: {twins['perfect']['overall_pct']}%")

print("=== 7. Testing AI Advisor Query Processing ===")
adv_res = process_advisor_query("If I take 3 days leave starting tomorrow, will Chemistry fall below 75%?", "section_A", sample_subjects)
print("AI Advisor Response Output:")
print(adv_res['answer'])

print("\n✅ All Backend Test Assertions Passed Successfully!")
