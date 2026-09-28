import os
import json
import re
from datetime import datetime, timedelta
from calculator.timetable import calculate_timetable_classes, get_section_data
from calculator.attendance import calculate_subject_attendance, calculate_overall_attendance
from calculator.simulator import simulate_leave, simulate_what_if

def parse_user_intent(query):
    """
    Parses natural language user query to extract intent, subjects, leave days, dates.
    """
    query_lower = query.lower()
    intent_data = {
        "intent": "general_guidance",
        "subject_name": None,
        "days": None,
        "leave_type": "Normal Leave",
        "start_date": None,
        "target_date": None
    }
    
    # Check leave intent
    if "leave" in query_lower or "sick" in query_lower or "absent" in query_lower or "od" in query_lower:
        intent_data["intent"] = "simulate_leave"
        if "od" in query_lower or "on duty" in query_lower or "on-duty" in query_lower:
            intent_data["leave_type"] = "On-Duty (OD)"
        elif "medical" in query_lower or "sick" in query_lower:
            intent_data["leave_type"] = "Medical Leave"
        else:
            intent_data["leave_type"] = "Normal Leave"
            
        # Extract number of days
        days_match = re.search(r'(\d+)\s*(-|\s)?(day|days)', query_lower)
        if days_match:
            intent_data["days"] = int(days_match.group(1))
        else:
            intent_data["days"] = 3 # Default 3 days if not specified
            
    # Check safe miss intent
    elif "how many" in query_lower and ("miss" in query_lower or "skip" in query_lower or "bunk" in query_lower):
        intent_data["intent"] = "safe_miss"
        
    # Check 90% target intent
    elif "90" in query_lower or "90%" in query_lower:
        intent_data["intent"] = "target_90"
        
    # Check danger / risk explanation intent
    elif "danger" in query_lower or "warning" in query_lower or "why" in query_lower or "risk" in query_lower:
        intent_data["intent"] = "explain_risk"
        
    # Check recovery intent
    elif "recover" in query_lower or "restore" in query_lower or "reach 75" in query_lower or "needed" in query_lower:
        intent_data["intent"] = "recovery"

    return intent_data

def get_subject_match(query, subjects_list):
    """Matches subject mentioned in query to subject list."""
    q_lower = query.lower()
    for sub in subjects_list:
        code = sub.get("code", "").lower()
        name = sub.get("name", "").lower()
        short_name = sub.get("short_name", "").lower()
        
        if short_name and short_name in q_lower:
            return sub
        if name and name in q_lower:
            return sub
        if code and code in q_lower:
            return sub
            
    return None

def process_advisor_query(query, section_id, current_subjects_data, today_str="2026-09-28", plan_end_date="2026-11-29"):
    """
    Main pipeline:
    1. Parse Intent & Extract Parameters
    2. Run Mathematical Calculation Engine
    3. Construct Structured Facts
    4. Call Gemini LLM (or fallback deterministic bot) to return natural response
    """
    intent_data = parse_user_intent(query)
    matched_subject = get_subject_match(query, current_subjects_data)
    
    # 1. Fetch full timetable calculation
    tt_calc = calculate_timetable_classes(section_id, today_str, plan_end_date)
    rem_by_sub = tt_calc["remaining_by_subject"]
    
    # 2. Compute exact current attendance stats
    evaluated_subjects = [calculate_subject_attendance(s, rem_by_sub.get(s["code"], 0)) for s in current_subjects_data]
    overall = calculate_overall_attendance(evaluated_subjects)
    
    calculation_results = {}
    
    # Execute specific intent calculation
    if intent_data["intent"] == "simulate_leave":
        num_days = intent_data["days"] or 3
        tomorrow = datetime.strptime(today_str, "%Y-%m-%d").date() + timedelta(days=1)
        end_leave = tomorrow + timedelta(days=num_days - 1)
        
        sim_res = simulate_leave(section_id, tomorrow.strftime("%Y-%m-%d"), end_leave.strftime("%Y-%m-%d"), intent_data["leave_type"], current_subjects_data, plan_end_date)
        calculation_results["simulated_leave"] = sim_res
        
    elif intent_data["intent"] == "safe_miss":
        if matched_subject:
            sub_res = next((s for s in evaluated_subjects if s["code"] == matched_subject["code"]), None)
            calculation_results["target_subject"] = sub_res
        else:
            calculation_results["all_safe_misses"] = [
                {"name": s["name"], "short_name": s["short_name"], "can_miss": s["can_miss_75"], "current_pct": s["current_pct"]}
                for s in evaluated_subjects
            ]
            
    elif intent_data["intent"] == "target_90":
        calculation_results["target_90_summary"] = [
            {
                "name": s["name"],
                "short_name": s["short_name"],
                "current_pct": s["current_pct"],
                "is_90_achievable": s["is_90_achievable"],
                "required_90": s["required_90"],
                "remaining": s["remaining_classes"],
                "max_possible": s["max_possible_pct"]
            }
            for s in evaluated_subjects
        ]
        
    elif intent_data["intent"] == "explain_risk" or intent_data["intent"] == "recovery":
        if matched_subject:
            sub_res = next((s for s in evaluated_subjects if s["code"] == matched_subject["code"]), None)
            calculation_results["risk_subject"] = sub_res
        else:
            calculation_results["at_risk_subjects"] = [s for s in evaluated_subjects if s["status_code"] in ["WARNING", "DANGER", "IRRECOVERABLE"]]

    # Attempt calling Gemini API if GEMINI_API_KEY is available
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            system_prompt = f"""
You are the AI Attendance Advisor for a college student.
Use ONLY the mathematical calculation results provided below to answer the student's question accurately.
Do not calculate numbers yourself — rely strictly on the calculated facts.

Student Question: "{query}"
Current Overall Attendance: {overall['overall_current_pct']}%
Section ID: {section_id}
Today Date: {today_str}

Calculated Math Facts:
{json.dumps(calculation_results, indent=2)}

Guidelines:
- Give a direct, encouraging, clear answer.
- Highlight whether attendance will drop below 75% or remain safe.
- Mention exact numbers of classes required or safe to miss.
- Keep the response concise, helpful, and formatted with bullet points if helpful.
"""
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=system_prompt
            )
            if response and response.text:
                return {
                    "answer": response.text.strip(),
                    "source": "AI Advisor (Gemini Powered)",
                    "intent": intent_data["intent"],
                    "calculation_facts": calculation_results
                }
        except Exception as e:
            # Fallback to deterministic AI synthesis below
            pass

    # Deterministic AI Advisor Response Generator (if API key missing or call fails)
    answer = generate_fallback_response(query, intent_data, matched_subject, calculation_results, evaluated_subjects, overall)

    return {
        "answer": answer,
        "source": "AI Attendance Advisor",
        "intent": intent_data["intent"],
        "calculation_facts": calculation_results
    }

def generate_fallback_response(query, intent_data, matched_subject, calc_facts, evaluated_subjects, overall):
    """
    Generates intelligent natural language response using precise calculated facts.
    """
    intent = intent_data["intent"]
    
    if intent == "simulate_leave":
        sim = calc_facts.get("simulated_leave", {})
        l_type = sim.get("leave_type", "Leave")
        tot_aff = sim.get("total_affected_classes", 0)
        has_warn = sim.get("has_warnings", False)
        warns = sim.get("warnings", [])
        
        resp = f"### 📊 Leave Impact Analysis ({l_type})\n\n"
        resp += f"If you take a **{l_type}** for {intent_data.get('days', 3)} days starting tomorrow, **{tot_aff} classes** across your timetable will be affected.\n\n"
        
        if has_warn:
            resp += "⚠️ **Warning: This leave will impact your safety buffer!**\n"
            for w in warns:
                resp += f"- **{w['name']} ({w['short_name']})**: Attendance drops from **{w['old_pct']}%** to **{w['new_pct']}%** ({w['affected_classes']} classes missed).\n"
            resp += "\n**Recommendation**: Make sure to attend the upcoming recovery classes for these subjects immediately after your leave!"
        else:
            resp += "✅ **Good news!** Taking this leave will keep all your subjects above the 75% requirement.\n"
            resp += f"Your projected overall attendance after the leave will be **{sim['overall']['overall_current_pct']}%**."
            
        return resp

    elif intent == "safe_miss":
        target = calc_facts.get("target_subject")
        if target:
            can_m = target.get("can_miss_75", 0)
            curr = target.get("current_pct", 0)
            req = target.get("required_75", 0)
            s_name = target.get("name")
            
            resp = f"### 🛡️ Safe Miss Allowance for **{s_name}**\n\n"
            resp += f"- **Current Attendance**: {curr}%\n"
            if can_m > 0:
                resp += f"- **Safe Classes You Can Miss**: You can safely miss **{can_m} upcoming class(es)** while maintaining at least 75%.\n"
                resp += f"- ⚠️ *Note: Missing more than {can_m} class(es) will cause your attendance to fall below 75%.*\n"
            else:
                resp += f"- 🔴 **No Buffer Available!** You cannot miss any upcoming classes. You must attend at least **{req} more classes** to recover to 75%."
            return resp
        else:
            resp = "### 🛡️ Safe Classes You Can Miss (By Subject)\n\n"
            for s in evaluated_subjects:
                icon = "🟢" if s['can_miss_75'] > 2 else ("🟡" if s['can_miss_75'] > 0 else "🔴")
                resp += f"- {icon} **{s['name']} ({s['short_name']})**: Current **{s['current_pct']}%** | Can safely miss: **{s['can_miss_75']} class(es)**\n"
            return resp

    elif intent == "target_90":
        resp = "### 🎯 90% Attendance Target Assessment\n\n"
        targets = calc_facts.get("target_90_summary", [])
        for t in targets:
            if t["is_90_achievable"]:
                resp += f"- 🟢 **{t['name']}**: Currently **{t['current_pct']}%**. Need to attend **{t['required_90']} out of {t['remaining']} remaining classes** to reach 90%.\n"
            else:
                resp += f"- ❌ **{t['name']}**: Currently **{t['current_pct']}%**. **90% Target Not Achievable** (Maximum possible attendance is **{t['max_possible']}%** even with 100% future attendance).\n"
        return resp

    elif intent == "explain_risk" or intent == "recovery":
        target = calc_facts.get("risk_subject")
        if target:
            resp = f"### 🔍 Recovery Status for **{target['name']}**\n\n"
            resp += f"- **Current Attendance**: {target['current_pct']}%\n"
            resp += f"- **Status**: {target['status_icon']} {target['status_label']}\n"
            resp += f"- **Classes Conducted**: {target['conducted']} | **Attended**: {target['attended']}\n"
            resp += f"- **Remaining Classes**: {target['remaining_classes']}\n"
            resp += f"- **Classes Required for 75%**: **{target['required_75']} classes**\n"
            if target['is_detention']:
                resp += "\n🚨 **IRREVERSIBLE DETENTION ALERT**: Mathematically, even attending all remaining classes cannot restore this subject to 75%."
            return resp
        else:
            at_risk = calc_facts.get("at_risk_subjects", [])
            if not at_risk:
                return "✅ **All your subjects are currently in the safe zone (>= 80%)!** Keep up the great work and maintain regular attendance."
            resp = "### ⚠️ Subjects Requiring Attention\n\n"
            for s in at_risk:
                resp += f"- {s['status_icon']} **{s['name']}**: Currently **{s['current_pct']}%**. Must attend **{s['required_75']} remaining classes** to reach 75% safety target.\n"
            return resp

    # General fallback
    return f"Based on your current timetable, your overall attendance is **{overall['overall_current_pct']}%** with **{overall['at_risk_count']} subjects at risk**. Feel free to ask about specific leaves, safe misses, or recovery paths!"
