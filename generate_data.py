import json
import os

sections_data = [
    {
        "id": "section_A",
        "name": "Section A",
        "dept": "Computer Science & Engineering",
        "year": "3rd Year",
        "sem": "5th Semester",
        "subjects": [
            {"code": "CS501", "name": "Java Programming", "short_name": "Java", "faculty": "Dr. Alan Turing"},
            {"code": "CS502", "name": "Database Management Systems", "short_name": "DBMS", "faculty": "Prof. Grace Hopper"},
            {"code": "CS503", "name": "Mathematics III", "short_name": "Maths", "faculty": "Dr. Carl Gauss"},
            {"code": "CS504", "name": "Computer Networks", "short_name": "CN", "faculty": "Prof. Vint Cerf"},
            {"code": "CS505", "name": "Web Technology", "short_name": "Web Tech", "faculty": "Dr. Tim Berners-Lee"},
            {"code": "CS506", "name": "Software Engineering", "short_name": "SE", "faculty": "Dr. Margaret Hamilton"}
        ],
        "schedule": {
            "Monday": ["CS501", "CS502", "CS503", "CS504", "CS505"],
            "Tuesday": ["CS502", "CS501", "CS506", "CS503", "CS504"],
            "Wednesday": ["CS503", "CS505", "CS501", "CS502", "CS506"],
            "Thursday": ["CS504", "CS506", "CS502", "CS501", "CS503"],
            "Friday": ["CS505", "CS504", "CS503", "CS506", "CS501"],
            "Saturday": ["CS501", "CS502", "CS505"]
        }
    },
    {
        "id": "section_B",
        "name": "Section B",
        "dept": "Computer Science & Engineering",
        "year": "2nd Year",
        "sem": "3rd Semester",
        "subjects": [
            {"code": "CS301", "name": "Data Structures", "short_name": "DS", "faculty": "Prof. Donald Knuth"},
            {"code": "CS302", "name": "Digital Logic Design", "short_name": "DLD", "faculty": "Dr. Claude Shannon"},
            {"code": "CS303", "name": "Discrete Mathematics", "short_name": "Discrete Math", "faculty": "Dr. Paul Erdős"},
            {"code": "CS304", "name": "Object Oriented C++", "short_name": "C++", "faculty": "Dr. Bjarne Stroustrup"},
            {"code": "CS305", "name": "Computer Organization", "short_name": "COA", "faculty": "Prof. John von Neumann"}
        ],
        "schedule": {
            "Monday": ["CS301", "CS302", "CS303", "CS304"],
            "Tuesday": ["CS304", "CS305", "CS301", "CS302"],
            "Wednesday": ["CS302", "CS303", "CS305", "CS301"],
            "Thursday": ["CS303", "CS304", "CS301", "CS305"],
            "Friday": ["CS305", "CS301", "CS302", "CS304"],
            "Saturday": ["CS301", "CS303"]
        }
    },
    {
        "id": "section_C",
        "name": "Section C",
        "dept": "Information Technology",
        "year": "3rd Year",
        "sem": "5th Semester",
        "subjects": [
            {"code": "IT501", "name": "Cloud Computing", "short_name": "Cloud", "faculty": "Dr. Werner Vogels"},
            {"code": "IT502", "name": "Operating Systems", "short_name": "OS", "faculty": "Prof. Linus Torvalds"},
            {"code": "IT503", "name": "Database Systems", "short_name": "DBS", "faculty": "Dr. Edgar Codd"},
            {"code": "IT504", "name": "Cyber Security", "short_name": "Cyber Sec", "faculty": "Prof. Bruce Schneier"},
            {"code": "IT505", "name": "Python Programming", "short_name": "Python", "faculty": "Dr. Guido van Rossum"}
        ],
        "schedule": {
            "Monday": ["IT501", "IT502", "IT503", "IT505"],
            "Tuesday": ["IT502", "IT504", "IT501", "IT503"],
            "Wednesday": ["IT503", "IT505", "IT502", "IT504"],
            "Thursday": ["IT504", "IT501", "IT505", "IT502"],
            "Friday": ["IT505", "IT503", "IT504", "IT501"],
            "Saturday": ["IT501", "IT505"]
        }
    },
    {
        "id": "section_D",
        "name": "Section D",
        "dept": "Information Technology",
        "year": "2nd Year",
        "sem": "3rd Semester",
        "subjects": [
            {"code": "IT301", "name": "Data Structures & Algos", "short_name": "DSA", "faculty": "Dr. Robert Sedgewick"},
            {"code": "IT302", "name": "Digital Systems", "short_name": "Digital Sys", "faculty": "Prof. Morris Mano"},
            {"code": "IT303", "name": "Probability & Statistics", "short_name": "Prob & Stat", "faculty": "Dr. Andrey Kolmogorov"},
            {"code": "IT304", "name": "Object Oriented Programming", "short_name": "OOP", "faculty": "Prof. James Gosling"},
            {"code": "IT305", "name": "Web Basics", "short_name": "Web Dev", "faculty": "Dr. Håkon Wium Lie"}
        ],
        "schedule": {
            "Monday": ["IT301", "IT302", "IT303", "IT304"],
            "Tuesday": ["IT302", "IT303", "IT305", "IT301"],
            "Wednesday": ["IT304", "IT305", "IT301", "IT302"],
            "Thursday": ["IT303", "IT301", "IT304", "IT305"],
            "Friday": ["IT305", "IT304", "IT302", "IT303"],
            "Saturday": ["IT301", "IT304"]
        }
    },
    {
        "id": "section_E",
        "name": "Section E",
        "dept": "Electronics & Communication",
        "year": "3rd Year",
        "sem": "5th Semester",
        "subjects": [
            {"code": "EC501", "name": "Signals & Systems", "short_name": "Signals", "faculty": "Dr. Alan Oppenheim"},
            {"code": "EC502", "name": "Analog Communication", "short_name": "Analog Comm", "faculty": "Prof. Simon Haykin"},
            {"code": "EC503", "name": "Microprocessors & Microcontrollers", "short_name": "MPMC", "faculty": "Dr. Ramesh Gaonkar"},
            {"code": "EC504", "name": "Electromagnetic Theory", "short_name": "EMT", "faculty": "Prof. James Clerk Maxwell"},
            {"code": "EC505", "name": "Control Systems", "short_name": "Control Sys", "faculty": "Dr. Katsuhiko Ogata"}
        ],
        "schedule": {
            "Monday": ["EC501", "EC502", "EC503", "EC504"],
            "Tuesday": ["EC502", "EC503", "EC505", "EC501"],
            "Wednesday": ["EC503", "EC504", "EC501", "EC505"],
            "Thursday": ["EC504", "EC505", "EC502", "EC503"],
            "Friday": ["EC505", "EC501", "EC504", "EC502"],
            "Saturday": ["EC501", "EC503"]
        }
    },
    {
        "id": "section_F",
        "name": "Section F",
        "dept": "Electronics & Communication",
        "year": "2nd Year",
        "sem": "3rd Semester",
        "subjects": [
            {"code": "EC301", "name": "Electronic Circuits", "short_name": "Circuits", "faculty": "Prof. Adel Sedra"},
            {"code": "EC302", "name": "Network Theory", "short_name": "Networks", "faculty": "Dr. Charles Desoer"},
            {"code": "EC303", "name": "Digital Electronics", "short_name": "Digital Elec", "faculty": "Dr. Thomas Floyd"},
            {"code": "EC304", "name": "Engineering Mathematics III", "short_name": "Maths III", "faculty": "Prof. Erwin Kreyszig"}
        ],
        "schedule": {
            "Monday": ["EC301", "EC302", "EC303", "EC304"],
            "Tuesday": ["EC302", "EC303", "EC304", "EC301"],
            "Wednesday": ["EC303", "EC304", "EC301", "EC302"],
            "Thursday": ["EC304", "EC301", "EC302", "EC303"],
            "Friday": ["EC301", "EC303", "EC304", "EC302"],
            "Saturday": ["EC302", "EC304"]
        }
    },
    {
        "id": "section_G",
        "name": "Section G",
        "dept": "Electrical & Electronics",
        "year": "3rd Year",
        "sem": "5th Semester",
        "subjects": [
            {"code": "EE501", "name": "Power Systems", "short_name": "Power Sys", "faculty": "Dr. Charles Steinmetz"},
            {"code": "EE502", "name": "Electrical Machines II", "short_name": "Machines", "faculty": "Prof. Nikola Tesla"},
            {"code": "EE503", "name": "Control Systems", "short_name": "Control", "faculty": "Dr. Richard Bellman"},
            {"code": "EE504", "name": "Power Electronics", "short_name": "Power Elec", "faculty": "Prof. Muhammad Rashid"},
            {"code": "EE505", "name": "Signal Processing", "short_name": "DSP", "faculty": "Dr. Sanjit Mitra"}
        ],
        "schedule": {
            "Monday": ["EE501", "EE502", "EE503", "EE504"],
            "Tuesday": ["EE502", "EE503", "EE505", "EE501"],
            "Wednesday": ["EE503", "EE504", "EE501", "EE505"],
            "Thursday": ["EE504", "EE505", "EE502", "EE503"],
            "Friday": ["EE505", "EE501", "EE504", "EE502"],
            "Saturday": ["EE501", "EE504"]
        }
    },
    {
        "id": "section_H",
        "name": "Section H",
        "dept": "Mechanical Engineering",
        "year": "3rd Year",
        "sem": "5th Semester",
        "subjects": [
            {"code": "ME501", "name": "Thermodynamics II", "short_name": "Thermo", "faculty": "Dr. Sadi Carnot"},
            {"code": "ME502", "name": "Fluid Mechanics", "short_name": "Fluid Mech", "faculty": "Prof. Osborne Reynolds"},
            {"code": "ME503", "name": "Kinematics of Machinery", "short_name": "KOM", "faculty": "Dr. Franz Reuleaux"},
            {"code": "ME504", "name": "Manufacturing Technology", "short_name": "Mfg Tech", "faculty": "Prof. Henry Ford"},
            {"code": "ME505", "name": "Heat Transfer", "short_name": "Heat Tr", "faculty": "Dr. Frank Incropera"}
        ],
        "schedule": {
            "Monday": ["ME501", "ME502", "ME503", "ME504"],
            "Tuesday": ["ME502", "ME503", "ME505", "ME501"],
            "Wednesday": ["ME503", "ME504", "ME501", "ME505"],
            "Thursday": ["ME504", "ME505", "ME502", "ME503"],
            "Friday": ["ME505", "ME501", "ME504", "ME502"],
            "Saturday": ["ME501", "ME502"]
        }
    },
    {
        "id": "section_I",
        "name": "Section I",
        "dept": "Civil Engineering",
        "year": "3rd Year",
        "sem": "5th Semester",
        "subjects": [
            {"code": "CE501", "name": "Structural Analysis", "short_name": "Structure", "faculty": "Dr. Hardy Cross"},
            {"code": "CE502", "name": "Geotechnical Engineering", "short_name": "Geotech", "faculty": "Prof. Karl Terzaghi"},
            {"code": "CE503", "name": "Hydraulics & Water Resources", "short_name": "Hydraulics", "faculty": "Dr. Daniel Bernoulli"},
            {"code": "CE504", "name": "Concrete Technology", "short_name": "Concrete", "faculty": "Prof. Joseph Aspdin"},
            {"code": "CE505", "name": "Transportation Engineering", "short_name": "Transport", "faculty": "Dr. John Loudon McAdam"}
        ],
        "schedule": {
            "Monday": ["CE501", "CE502", "CE503", "CE504"],
            "Tuesday": ["CE502", "CE503", "CE505", "CE501"],
            "Wednesday": ["CE503", "CE504", "CE501", "CE505"],
            "Thursday": ["CE504", "CE505", "CE502", "CE503"],
            "Friday": ["CE505", "CE501", "CE504", "CE502"],
            "Saturday": ["CE501", "CE503"]
        }
    },
    {
        "id": "section_J",
        "name": "Section J",
        "dept": "Artificial Intelligence & Data Science",
        "year": "3rd Year",
        "sem": "5th Semester",
        "subjects": [
            {"code": "AD501", "name": "Machine Learning", "short_name": "ML", "faculty": "Dr. Andrew Ng"},
            {"code": "AD502", "name": "Deep Learning", "short_name": "Deep L", "faculty": "Prof. Yann LeCun"},
            {"code": "AD503", "name": "Data Mining & Visualization", "short_name": "Data Mining", "faculty": "Dr. Jiawei Han"},
            {"code": "AD504", "name": "Big Data Analytics", "short_name": "Big Data", "faculty": "Prof. Doug Cutting"},
            {"code": "AD505", "name": "Natural Language Processing", "short_name": "NLP", "faculty": "Dr. Christopher Manning"},
            {"code": "AD506", "name": "AI Ethics & Policy", "short_name": "AI Ethics", "faculty": "Dr. Timnit Gebru"}
        ],
        "schedule": {
            "Monday": ["AD501", "AD502", "AD503", "AD504", "AD505"],
            "Tuesday": ["AD502", "AD501", "AD506", "AD503", "AD504"],
            "Wednesday": ["AD503", "AD505", "AD501", "AD502", "AD506"],
            "Thursday": ["AD504", "AD506", "AD502", "AD501", "AD503"],
            "Friday": ["AD505", "AD504", "AD503", "AD506", "AD501"],
            "Saturday": ["AD501", "AD502", "AD505"]
        }
    }
]

time_slots = [
    "09:00 - 10:00",
    "10:00 - 11:00",
    "11:15 - 12:15",
    "13:15 - 14:15",
    "14:15 - 15:15"
]

holidays = [
    "2026-10-02", # Gandhi Jayanti
    "2026-10-20", # Dussehra / Autumn Break
    "2026-11-01"  # College Foundation Day / Deepavali
]

for sec in sections_data:
    formatted_timetable = {}
    for day, sub_codes in sec["schedule"].items():
        day_periods = []
        for idx, code in enumerate(sub_codes):
            day_periods.append({
                "period": idx + 1,
                "time": time_slots[idx] if idx < len(time_slots) else f"Period {idx+1}",
                "subject_code": code
            })
        formatted_timetable[day] = day_periods
    
    file_content = {
        "section_id": sec["id"],
        "section_name": sec["name"],
        "department": sec["dept"],
        "year": sec["year"],
        "semester": sec["sem"],
        "subjects": sec["subjects"],
        "timetable": formatted_timetable,
        "holidays": holidays
    }
    
    filepath = os.path.join("data", f"{sec['id']}.json")
    with open(filepath, "w") as f:
        json.dump(file_content, f, indent=2)

print("Generated all 10 section json files successfully!")
