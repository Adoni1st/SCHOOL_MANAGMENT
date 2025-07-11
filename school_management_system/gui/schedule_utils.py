import os
import json

def get_timetable_path(class_code=None):
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    tt_dir = os.path.join(data_dir, 'timetables')
    if not os.path.exists(tt_dir):
        os.makedirs(tt_dir, exist_ok=True)
    if class_code:
        return os.path.join(tt_dir, f"{class_code}.json")
    return tt_dir

def load_timetable_for_class(class_code):
    path = get_timetable_path(class_code)
    if not os.path.exists(path):
        return {
            "mode": "auto",
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "periods_per_day": 6,
            "schedule": {day: ["Free"]*6 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]},
            "last_modified": None
        }
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load timetable for {class_code}: {e}")
        return {
            "mode": "auto",
            "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "periods_per_day": 6,
            "schedule": {day: ["Free"]*6 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]},
            "last_modified": None
        }

def load_class_codes():
    users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'classes.json')
    if not os.path.exists(users_file):
        return []
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            classes = json.load(f)
        return [c['code'] for c in classes if 'code' in c]
    except Exception as e:
        print(f"[ERROR] Failed to load class codes: {e}")
        return [] 