from datetime import datetime, timedelta
from calculator.timetable import calculate_timetable_classes, get_section_data
from calculator.attendance import calculate_subject_attendance, calculate_overall_attendance

def simulate_leave(section_id, start_date_str, end_date_str, leave_type, current_subjects_data, plan_end_date="2026-11-29"):
    """
    Simulates taking leave between start_date_str and end_date_str.
    leave_type: 'Normal Leave', 'On-Duty (OD)', 'Medical Leave'
    """
    # 1. Calculate timetable classes occurring during the leave period
    leave_tt = calculate_timetable_classes(section_id, start_date_str, end_date_str)
    affected_counts = leave_tt["remaining_by_subject"]
    
    # 2. Calculate remaining classes for full planning window (Today -> plan_end_date)
    # Note: start_date_str for leave simulation is usually in the future
    full_tt = calculate_timetable_classes(section_id, start_date_str, plan_end_date)
    remaining_by_subject = full_tt["remaining_by_subject"]

    simulated_subjects = []
    affected_summary = []

    for sub in current_subjects_data:
        code = sub.get("code")
        conducted = int(sub.get("conducted", 0))
        attended = int(sub.get("attended", 0))
        rem_total = remaining_by_subject.get(code, 0)
        
        affected_classes = affected_counts.get(code, 0)
        
        # Apply leave rules to conducted/attended
        if leave_type == "Normal Leave":
            # Absent for affected classes during leave
            new_conducted = conducted + affected_classes
            new_attended = attended
            rem_after_leave = max(0, rem_total - affected_classes)
        elif leave_type == "On-Duty (OD)":
            # Counted as Present / OD Credit
            new_conducted = conducted + affected_classes
            new_attended = attended + affected_classes
            rem_after_leave = max(0, rem_total - affected_classes)
        elif leave_type == "Medical Leave":
            # Excused / Medical Exemption (Conducted & Attended unaffected, classes deducted from requirement)
            new_conducted = conducted
            new_attended = attended
            rem_after_leave = max(0, rem_total - affected_classes)
        else:
            # Default Normal Leave
            new_conducted = conducted + affected_classes
            new_attended = attended
            rem_after_leave = max(0, rem_total - affected_classes)

        sub_info = {
            "code": code,
            "name": sub.get("name"),
            "short_name": sub.get("short_name", sub.get("name")),
            "faculty": sub.get("faculty", ""),
            "conducted": new_conducted,
            "attended": new_attended
        }
        
        sim_res = calculate_subject_attendance(sub_info, rem_after_leave)
        
        # Original current calculation for comparison
        orig_res = calculate_subject_attendance(sub, rem_total)
        sim_res["pct_change"] = round(sim_res["current_pct"] - orig_res["current_pct"], 2)
        sim_res["affected_classes_count"] = affected_classes
        
        simulated_subjects.append(sim_res)
        
        if affected_classes > 0:
            affected_summary.append({
                "code": code,
                "name": sub.get("name"),
                "short_name": sub.get("short_name"),
                "affected_classes": affected_classes,
                "old_pct": orig_res["current_pct"],
                "new_pct": sim_res["current_pct"],
                "pct_change": sim_res["pct_change"],
                "is_danger": sim_res["status_code"] in ["DANGER", "IRRECOVERABLE"],
                "dropped_below_75": (orig_res["current_pct"] >= 75.0 and sim_res["current_pct"] < 75.0)
            })

    overall_sim = calculate_overall_attendance(simulated_subjects)
    
    # Calculate original overall for comparison
    orig_subjects = [calculate_subject_attendance(s, remaining_by_subject.get(s["code"], 0)) for s in current_subjects_data]
    orig_overall = calculate_overall_attendance(orig_subjects)
    
    overall_sim["pct_change"] = round(overall_sim["overall_current_pct"] - orig_overall["overall_current_pct"], 2)

    warnings = [item for item in affected_summary if item["dropped_below_75"] or item["is_danger"]]

    return {
        "leave_type": leave_type,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "total_affected_classes": sum(affected_counts.values()),
        "affected_subjects": affected_summary,
        "simulated_subjects": simulated_subjects,
        "overall": overall_sim,
        "warnings": warnings,
        "has_warnings": len(warnings) > 0
    }

def simulate_what_if(scenario_type, params, section_id, current_subjects_data, plan_end_date="2026-11-29"):
    """
    Simulates custom user scenarios:
    - 'attend_all': Student attends every remaining class
    - 'miss_n_classes': Student misses N classes in target subject
    - 'attend_mon_tue_only': Student only attends classes occurring on Mondays and Tuesdays
    - 'custom_misses': Specific dict of missed classes per subject
    """
    today_str = params.get("start_date", "2026-09-28")
    full_tt = calculate_timetable_classes(section_id, today_str, plan_end_date)
    remaining_by_subject = full_tt["remaining_by_subject"]
    
    simulated_subjects = []
    
    for sub in current_subjects_data:
        code = sub.get("code")
        conducted = int(sub.get("conducted", 0))
        attended = int(sub.get("attended", 0))
        rem_total = remaining_by_subject.get(code, 0)
        
        if scenario_type == "attend_all":
            new_conducted = conducted + rem_total
            new_attended = attended + rem_total
            rem_left = 0
        elif scenario_type == "miss_n_classes":
            target_code = params.get("subject_code")
            miss_count = int(params.get("miss_count", 1))
            if code == target_code:
                # Add missed classes as conducted but not attended
                added_attended = max(0, rem_total - miss_count)
                new_conducted = conducted + rem_total
                new_attended = attended + added_attended
            else:
                new_conducted = conducted + rem_total
                new_attended = attended + rem_total
            rem_left = 0
        elif scenario_type == "attend_mon_tue_only":
            # Count how many classes fall on Mon/Tue vs others
            mon_tue_classes = 0
            other_classes = 0
            for dt, dt_info in full_tt["by_date"].items():
                if dt_info["day"] in ["Monday", "Tuesday"]:
                    for c in dt_info["classes"]:
                        if c["subject_code"] == code:
                            mon_tue_classes += 1
                else:
                    for c in dt_info["classes"]:
                        if c["subject_code"] == code:
                            other_classes += 1
            new_conducted = conducted + rem_total
            new_attended = attended + mon_tue_classes
            rem_left = 0
        else:
            # Default fallback
            new_conducted = conducted + rem_total
            new_attended = attended + rem_total
            rem_left = 0

        sub_info = {
            "code": code,
            "name": sub.get("name"),
            "short_name": sub.get("short_name", sub.get("name")),
            "faculty": sub.get("faculty", ""),
            "conducted": new_conducted,
            "attended": new_attended
        }
        
        sim_res = calculate_subject_attendance(sub_info, rem_left)
        simulated_subjects.append(sim_res)

    overall_sim = calculate_overall_attendance(simulated_subjects)

    return {
        "scenario_type": scenario_type,
        "description": params.get("description", "What-If Scenario"),
        "simulated_subjects": simulated_subjects,
        "overall": overall_sim
    }

def run_digital_twin_simulations(section_id, current_subjects_data, today_str="2026-09-28", plan_end_date="2026-11-29"):
    """
    Creates virtual twin simulations comparing 4 standard scenarios side-by-side:
    1. Baseline (Current Trend)
    2. Perfect Attendance (100% Future Classes Attended)
    3. 3-Day Sick Leave (Normal Leave)
    4. 2-Day OD Seminar (On-Duty Leave)
    """
    # 1. Baseline
    full_tt = calculate_timetable_classes(section_id, today_str, plan_end_date)
    base_subjects = [calculate_subject_attendance(s, full_tt["remaining_by_subject"].get(s["code"], 0)) for s in current_subjects_data]
    base_overall = calculate_overall_attendance(base_subjects)

    # 2. Perfect Attendance
    perfect_sim = simulate_what_if("attend_all", {"start_date": today_str}, section_id, current_subjects_data, plan_end_date)

    # 3. 3-Day Sick Leave (Starting tomorrow)
    tomorrow_dt = datetime.strptime(today_str, "%Y-%m-%d").date() + timedelta(days=1)
    end_sick_dt = tomorrow_dt + timedelta(days=2)
    sick_sim = simulate_leave(section_id, tomorrow_dt.strftime("%Y-%m-%d"), end_sick_dt.strftime("%Y-%m-%d"), "Normal Leave", current_subjects_data, plan_end_date)

    # 4. 2-Day OD Seminar
    end_od_dt = tomorrow_dt + timedelta(days=1)
    od_sim = simulate_leave(section_id, tomorrow_dt.strftime("%Y-%m-%d"), end_od_dt.strftime("%Y-%m-%d"), "On-Duty (OD)", current_subjects_data, plan_end_date)

    return {
        "baseline": {
            "title": "Current Baseline",
            "overall_pct": base_overall["overall_current_pct"],
            "max_pct": base_overall["overall_max_possible_pct"],
            "at_risk_count": base_overall["at_risk_count"]
        },
        "perfect": {
            "title": "Perfect Attendance (100%)",
            "overall_pct": perfect_sim["overall"]["overall_current_pct"],
            "max_pct": perfect_sim["overall"]["overall_max_possible_pct"],
            "at_risk_count": perfect_sim["overall"]["at_risk_count"]
        },
        "sick_leave": {
            "title": "3-Day Sick Leave",
            "overall_pct": sick_sim["overall"]["overall_current_pct"],
            "max_pct": sick_sim["overall"]["overall_max_possible_pct"],
            "at_risk_count": sick_sim["overall"]["at_risk_count"],
            "warnings": len(sick_sim["warnings"])
        },
        "od_seminar": {
            "title": "2-Day OD Seminar",
            "overall_pct": od_sim["overall"]["overall_current_pct"],
            "max_pct": od_sim["overall"]["overall_max_possible_pct"],
            "at_risk_count": od_sim["overall"]["at_risk_count"]
        }
    }
