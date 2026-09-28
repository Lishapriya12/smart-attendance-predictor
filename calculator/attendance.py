import math

def calculate_subject_attendance(subject_info, remaining_classes):
    """
    Calculates detailed attendance stats for a single subject.
    subject_info: dict containing {code, name, short_name, conducted, attended}
    remaining_classes: integer count of future classes from timetable
    """
    code = subject_info.get("code")
    name = subject_info.get("name")
    short_name = subject_info.get("short_name", name)
    conducted = int(subject_info.get("conducted", 0))
    attended = int(subject_info.get("attended", 0))
    
    # Handle sanity edge cases
    if attended > conducted:
        attended = conducted

    remaining = max(0, int(remaining_classes))
    total_classes = conducted + remaining

    # 1. Current Attendance Percentage
    current_pct = round((attended / conducted * 100), 2) if conducted > 0 else 100.0

    # 2. Maximum Possible Attendance (Attending all remaining classes)
    max_possible_attended = attended + remaining
    max_possible_pct = round((max_possible_attended / total_classes * 100), 2) if total_classes > 0 else 100.0

    # 3. 75% Requirement Calculation
    target_75_needed_total = math.ceil(0.75 * total_classes)
    required_75 = max(0, target_75_needed_total - attended)
    is_75_achievable = (required_75 <= remaining)

    # Safe Miss Calculation for 75% target
    # Maximum classes student can miss out of remaining while keeping final % >= 75%
    if is_75_achievable:
        can_miss_75 = max(0, remaining - required_75)
    else:
        can_miss_75 = 0

    # Projected final attendance if student attends exact required_75 classes
    if is_75_achievable:
        projected_75_pct = round(((attended + required_75) / total_classes * 100), 2) if total_classes > 0 else 100.0
    else:
        projected_75_pct = max_possible_pct

    # 4. 90% Requirement Calculation
    target_90_needed_total = math.ceil(0.90 * total_classes)
    required_90 = max(0, target_90_needed_total - attended)
    is_90_achievable = (required_90 <= remaining)

    # 5. Risk Indicator & Irreversible Detention Determination
    is_detention = not is_75_achievable or (max_possible_pct < 75.0)

    if is_detention:
        status_code = "IRRECOVERABLE"
        status_label = "Irrecoverable"
        status_color = "black"
        status_icon = "⚫"
        risk_level = 4
    elif current_pct < 75.0 or can_miss_75 == 0:
        status_code = "DANGER"
        status_label = "Danger"
        status_color = "red"
        status_icon = "🔴"
        risk_level = 3
    elif current_pct < 80.0 or can_miss_75 <= 2:
        status_code = "WARNING"
        status_label = "Warning"
        status_color = "yellow"
        status_icon = "🟡"
        risk_level = 2
    else:
        status_code = "SAFE"
        status_label = "Safe"
        status_color = "green"
        status_icon = "🟢"
        risk_level = 1

    return {
        "code": code,
        "name": name,
        "short_name": short_name,
        "faculty": subject_info.get("faculty", ""),
        "conducted": conducted,
        "attended": attended,
        "absent": conducted - attended,
        "current_pct": current_pct,
        "remaining_classes": remaining,
        "total_classes": total_classes,
        "max_possible_pct": max_possible_pct,
        # 75% Metrics
        "required_75": required_75,
        "can_miss_75": can_miss_75,
        "is_75_achievable": is_75_achievable,
        "projected_75_pct": projected_75_pct,
        # 90% Metrics
        "required_90": required_90 if is_90_achievable else None,
        "is_90_achievable": is_90_achievable,
        "max_possible_if_missed_90": max_possible_pct,
        # Status
        "is_detention": is_detention,
        "status_code": status_code,
        "status_label": status_label,
        "status_color": status_color,
        "status_icon": status_icon,
        "risk_level": risk_level
    }

def calculate_overall_attendance(subjects_results):
    """Calculates overall attendance summary across all subjects."""
    total_conducted = sum(s["conducted"] for s in subjects_results)
    total_attended = sum(s["attended"] for s in subjects_results)
    total_remaining = sum(s["remaining_classes"] for s in subjects_results)
    total_classes = total_conducted + total_remaining

    overall_current_pct = round((total_attended / total_conducted * 100), 2) if total_conducted > 0 else 100.0
    overall_max_possible_pct = round(((total_attended + total_remaining) / total_classes * 100), 2) if total_classes > 0 else 100.0

    at_risk_count = sum(1 for s in subjects_results if s["status_code"] in ["DANGER", "IRRECOVERABLE"])
    warning_count = sum(1 for s in subjects_results if s["status_code"] == "WARNING")
    detention_count = sum(1 for s in subjects_results if s["is_detention"])
    total_safe_misses = sum(s["can_miss_75"] for s in subjects_results)

    return {
        "total_conducted": total_conducted,
        "total_attended": total_attended,
        "total_remaining": total_remaining,
        "overall_current_pct": overall_current_pct,
        "overall_max_possible_pct": overall_max_possible_pct,
        "at_risk_count": at_risk_count,
        "warning_count": warning_count,
        "detention_count": detention_count,
        "total_safe_misses": total_safe_misses,
        "has_detention_warning": detention_count > 0
    }
