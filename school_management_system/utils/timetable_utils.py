import os
import json
import random
from collections import defaultdict, Counter
from typing import Dict, List, Any

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
NEW_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# --- MIGRATION/VALIDATION HELPERS ---
def is_modern_period_list(periods):
    """Check if a day's periods are in the modern format (list of dicts with period, subject, teacher)."""
    return isinstance(periods, list) and all(isinstance(p, dict) and 'period' in p and 'subject' in p and 'teacher' in p for p in periods)

def migrate_day_periods(day_periods, periods_per_day=8):
    """Convert a day's periods to the modern format."""
    if is_modern_period_list(day_periods):
        return day_periods
    result = []
    for i in range(periods_per_day):
        if isinstance(day_periods, list) and len(day_periods) > i:
            val = day_periods[i]
            if isinstance(val, dict):
                subj = val.get('subject', '')
                teacher = val.get('teacher', '')
            else:
                subj = val if val else "Free"
                teacher = ""
        else:
            subj = "Free"
            teacher = ""
        result.append({"period": i+1, "subject": subj, "teacher": teacher})
    return result

def migrate_timetable(timetable: Dict[str, Any], periods_per_day=8) -> Dict[str, List[Dict]]:
    """Migrate a timetable dict to the modern format for all days."""
    return {day: migrate_day_periods(timetable.get(day, []), periods_per_day) for day in DAYS}

def migrate_all_timetables(data: Dict[str, Any], periods_per_day=8) -> Dict[str, Dict[str, List[Dict]]]:
    """Migrate all class timetables in the data to the modern format."""
    return {class_code: migrate_timetable(timetable, periods_per_day) for class_code, timetable in data.items()}

# --- LOAD/SAVE WITH MIGRATION ---
def to_new_format(old_timetable, periods_per_day=8, working_days=None):
    """Convert old timetable dict to new format."""
    if working_days is None:
        working_days = NEW_DAYS
    new_tt = {}
    for day in working_days:
        periods = old_timetable.get(day, [])
        if periods and isinstance(periods[0], dict):
            new_tt[day] = [p.get('subject', '') for p in periods]
        else:
            new_tt[day] = [p if isinstance(p, str) else '' for p in periods]
        while len(new_tt[day]) < periods_per_day:
            new_tt[day].append("")
    return new_tt

def from_new_format(new_tt, periods_per_day=8, working_days=None):
    """Convert new format timetable to old (list of dicts per day)."""
    if working_days is None:
        working_days = NEW_DAYS
    old_tt = {}
    for day in working_days:
        periods = new_tt.get(day, [])
        old_tt[day] = [{"period": i+1, "subject": subj or "Free", "teacher": ""} for i, subj in enumerate(periods)]
    return old_tt

def load_timetable(path, class_code, default_periods=8, default_days=None):
    if default_days is None:
        default_days = NEW_DAYS
    if not os.path.exists(path):
        return {
            "periods_per_day": default_periods,
            "working_days": default_days,
            "timetable": {day: ["" for _ in range(default_periods)] for day in default_days}
        }
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    entry = data.get(class_code)
    if entry and all(k in entry for k in ("periods_per_day", "working_days", "timetable")):
        return entry
    periods_per_day = default_periods
    working_days = default_days
    timetable = entry if entry else {day: [] for day in default_days}
    new_tt = to_new_format(timetable, periods_per_day, working_days)
    return {
        "periods_per_day": periods_per_day,
        "working_days": working_days,
        "timetable": new_tt
    }

def save_timetable(path, class_code, timetable_data):
    periods_per_day = timetable_data.get("periods_per_day", 8)
    working_days = timetable_data.get("working_days", NEW_DAYS)
    timetable = timetable_data.get("timetable", {day: ["" for _ in range(periods_per_day)] for day in working_days})
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}
    data[class_code] = {
        "periods_per_day": periods_per_day,
        "working_days": working_days,
        "timetable": timetable
    }
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# --- SUBJECT/TEACHER HELPERS ---
def get_teacher_for_subject(subject_name, all_subjects):
    for subj in all_subjects:
        if subj.get('name') == subject_name:
            return subj.get('teacher', '')
    return ""

def get_subjects_and_teachers(all_subjects):
    """Return a dict {subject: [teacher1, teacher2, ...]} for all subjects."""
    subj_teachers = defaultdict(list)
    for subj in all_subjects:
        name = subj.get('name')
        teacher = subj.get('teacher', '')
        if name:
            if teacher:
                subj_teachers[name].append(teacher)
            else:
                subj_teachers[name].append("")
    return dict(subj_teachers)

# --- LEGACY AUTO-GENERATOR (to be replaced by advanced one) ---
# (Removed legacy auto_generate_timetable. Use utils/auto_scheduler.py:auto_generate_timetable instead.)

# --- LEGACY AUTO-GENERATOR (to be replaced by advanced one) ---
# (Removed legacy auto_generate_timetable. Use utils/auto_scheduler.py:auto_generate_timetable instead.) 