from datetime import datetime, timedelta
from calculator.timetable import calculate_timetable_classes

def generate_attendance_forecast(section_id, current_subject_data, start_date_str="2026-09-28", end_date_str="2026-11-29"):
    """
    Generates a forecast of overall attendance across key future checkpoint dates.
    Dates sampled: Today, Oct 15, Oct 30, Nov 15, Nov 29 (or custom range steps).
    """
    checkpoints = [
        "2026-09-28",
        "2026-10-15",
        "2026-10-30",
        "2026-11-15",
        "2026-11-29"
    ]
    
    # Filter checkpoints within requested start and end dates
    try:
        s_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except Exception:
        s_date = datetime.strptime("2026-09-28", "%Y-%m-%d").date()
        e_date = datetime.strptime("2026-11-29", "%Y-%m-%d").date()

    forecast_timeline = []
    
    # Calculate baseline total conducted and attended as of today
    base_conducted = sum(int(s.get("conducted", 0)) for s in current_subject_data)
    base_attended = sum(int(s.get("attended", 0)) for s in current_subject_data)

    for cp_str in checkpoints:
        cp_date = datetime.strptime(cp_str, "%Y-%m-%d").date()
        if cp_date < s_date or cp_date > e_date:
            continue
        
        # Calculate classes conducted from start_date up to checkpoint date
        tt = calculate_timetable_classes(section_id, start_date_str, cp_str)
        added_classes = tt["total_remaining"]
        
        # Best-case scenario (attend 100% of classes up to checkpoint)
        perfect_conducted = base_conducted + added_classes
        perfect_attended = base_attended + added_classes
        perfect_pct = round((perfect_attended / perfect_conducted * 100), 2) if perfect_conducted > 0 else 100.0
        
        # Average scenario (maintain current student attendance rate)
        current_rate = (base_attended / base_conducted) if base_conducted > 0 else 1.0
        avg_attended = base_attended + round(added_classes * current_rate)
        avg_pct = round((avg_attended / perfect_conducted * 100), 2) if perfect_conducted > 0 else 100.0

        forecast_timeline.append({
            "date": cp_str,
            "label": datetime.strptime(cp_str, "%Y-%m-%d").strftime("%d %b"),
            "added_classes": added_classes,
            "perfect_pct": perfect_pct,
            "avg_pct": avg_pct
        })
        
    return forecast_timeline

def generate_recovery_path(subject_res):
    """
    Generates milestone steps (75%, 80%, 85%, 90%) for a single subject or overall.
    Calculates number of consecutive remaining classes required to reach each target.
    """
    conducted = subject_res["conducted"]
    attended = subject_res["attended"]
    remaining = subject_res["remaining_classes"]
    total_classes = conducted + remaining
    current_pct = subject_res["current_pct"]

    milestones = [75, 80, 85, 90]
    path_steps = []

    for target in milestones:
        # Minimum total attended needed for this target
        req_total_attended = int(round(target / 100.0 * total_classes + 0.4999))
        req_additional = max(0, req_total_attended - attended)
        
        achievable = (req_additional <= remaining)
        
        path_steps.append({
            "target_pct": target,
            "required_classes": req_additional,
            "achievable": achievable,
            "reached": current_pct >= target,
            "classes_left_buffer": (remaining - req_additional) if achievable else None
        })

    return {
        "subject_code": subject_res.get("code"),
        "subject_name": subject_res.get("name"),
        "current_pct": current_pct,
        "remaining_classes": remaining,
        "milestones": path_steps
    }

def calculate_recovery_streak(subject_res, recent_attended_count=0):
    """
    Calculates attendance recovery streak progress towards 75% target.
    """
    req_75 = subject_res.get("required_75", 0)
    current_pct = subject_res.get("current_pct", 0)
    
    if current_pct >= 75.0 and req_75 == 0:
        return {
            "status": "Target Maintained",
            "progress_pct": 100,
            "attended": 0,
            "required": 0,
            "remaining_required": 0,
            "message": "You are currently maintaining safe attendance above 75%!"
        }
    
    # Progress towards required classes
    attended_streak = min(recent_attended_count, req_75)
    remaining_streak = max(0, req_75 - attended_streak)
    progress_pct = round((attended_streak / req_75 * 100), 1) if req_75 > 0 else 100

    return {
        "status": "In Progress" if remaining_streak > 0 else "Recovered",
        "progress_pct": progress_pct,
        "attended": attended_streak,
        "required": req_75,
        "remaining_required": remaining_streak,
        "message": f"{remaining_streak} more required classes to reach 75% target."
    }
