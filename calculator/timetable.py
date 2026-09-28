import json
import os
from datetime import datetime, timedelta

SEMESTER_START = datetime.strptime("2026-08-29", "%Y-%m-%d").date()
SEMESTER_END = datetime.strptime("2026-11-29", "%Y-%m-%d").date()

def get_section_data(section_id):
    """Load section data from data/{section_id}.json."""
    if not section_id.endswith(".json"):
        filename = f"{section_id}.json"
    else:
        filename = section_id
    
    filepath = os.path.join(os.path.dirname(__file__), "..", "data", filename)
    if not os.path.exists(filepath):
        # Fallback to section_A if not found
        filepath = os.path.join(os.path.dirname(__file__), "..", "data", "section_A.json")
    
    with open(filepath, "r") as f:
        return json.load(f)

def list_all_sections():
    """Returns metadata for all 10 section files."""
    sections_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    sections_list = []
    if os.path.exists(sections_dir):
        for fname in sorted(os.listdir(sections_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(sections_dir, fname)
                with open(fpath, "r") as f:
                    data = json.load(f)
                    sections_list.append({
                        "id": data.get("section_id", fname.replace(".json", "")),
                        "name": data.get("section_name", fname),
                        "department": data.get("department", "CSE"),
                        "year": data.get("year", "3rd Year"),
                        "semester": data.get("semester", "5th Semester"),
                        "subject_count": len(data.get("subjects", []))
                    })
    return sections_list

def calculate_timetable_classes(section_id, start_date_str, end_date_str):
    """
    Calculates remaining classes for each subject and day-by-day breakdown
    between start_date (inclusive) and end_date (inclusive).
    """
    section_data = get_section_data(section_id)
    timetable = section_data.get("timetable", {})
    holidays = set(section_data.get("holidays", []))
    
    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except Exception:
        start_date = datetime.strptime("2026-09-28", "%Y-%m-%d").date()
        
    try:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except Exception:
        end_date = SEMESTER_END

    # Clamp to semester bounds
    if start_date < SEMESTER_START:
        start_date = SEMESTER_START
    if end_date > SEMESTER_END:
        end_date = SEMESTER_END
    if start_date > end_date:
        start_date = end_date

    subject_counts = {s["code"]: 0 for s in section_data.get("subjects", [])}
    by_date = {}
    total_remaining_classes = 0

    curr_date = start_date
    while curr_date <= end_date:
        date_str = curr_date.strftime("%Y-%m-%d")
        day_name = curr_date.strftime("%A")
        
        # Check if holiday or Sunday
        if day_name == "Sunday" or date_str in holidays:
            by_date[date_str] = {
                "day": day_name,
                "is_holiday": date_str in holidays,
                "is_sunday": day_name == "Sunday",
                "classes": []
            }
        else:
            day_schedule = timetable.get(day_name, [])
            day_classes = []
            for item in day_schedule:
                sub_code = item.get("subject_code")
                day_classes.append({
                    "period": item.get("period"),
                    "time": item.get("time"),
                    "subject_code": sub_code
                })
                if sub_code in subject_counts:
                    subject_counts[sub_code] += 1
                else:
                    subject_counts[sub_code] = 1
                total_remaining_classes += 1
                
            by_date[date_str] = {
                "day": day_name,
                "is_holiday": False,
                "is_sunday": False,
                "classes": day_classes
            }
            
        curr_date += timedelta(days=1)

    return {
        "section_id": section_data.get("section_id"),
        "section_name": section_data.get("section_name"),
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "total_remaining": total_remaining_classes,
        "remaining_by_subject": subject_counts,
        "by_date": by_date,
        "semester_start": SEMESTER_START.strftime("%Y-%m-%d"),
        "semester_end": SEMESTER_END.strftime("%Y-%m-%d")
    }
