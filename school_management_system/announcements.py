import os
import json
import uuid
import datetime

ANNOUNCEMENTS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'announcements.json')

ANNOUNCEMENT_FIELDS = [
    'id', 'title', 'content', 'target', 'expiry_date', 'priority', 'created_by', 'created_at'
]

PRIORITIES = ['High', 'Medium', 'Low']


def load_announcements():
    try:
        if not os.path.exists(ANNOUNCEMENTS_PATH):
            with open(ANNOUNCEMENTS_PATH, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []
        with open(ANNOUNCEMENTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load announcements: {e}")
        return []

def save_announcements(data):
    try:
        with open(ANNOUNCEMENTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save announcements: {e}")
        return False

# --- CRUD Operations ---
def add_announcement(title, content, target, created_by, priority='Medium', expiry_date=None):
    announcements = load_announcements()
    ann = {
        'id': str(uuid.uuid4()),
        'title': title,
        'content': content,
        'target': target,  # e.g. 'All', 'Teacher', 'Student', 'Class:10A'
        'expiry_date': expiry_date,  # ISO string or None
        'priority': priority,
        'created_by': created_by,
        'created_at': datetime.datetime.now().isoformat()
    }
    announcements.append(ann)
    save_announcements(announcements)
    return ann

def edit_announcement(ann_id, **kwargs):
    announcements = load_announcements()
    for ann in announcements:
        if ann['id'] == ann_id:
            for k, v in kwargs.items():
                if k in ANNOUNCEMENT_FIELDS and v is not None:
                    ann[k] = v
            break
    save_announcements(announcements)
    return True

def delete_announcement(ann_id):
    announcements = load_announcements()
    announcements = [a for a in announcements if a['id'] != ann_id]
    save_announcements(announcements)
    return True

def filter_announcements(user_role=None, user_class=None, hide_expired=True):
    announcements = load_announcements()
    now = datetime.datetime.now().isoformat()
    filtered = []
    for ann in announcements:
        if hide_expired and ann.get('expiry_date') and ann['expiry_date'] < now:
            continue
        tgt = ann.get('target', 'All')
        if tgt == 'All':
            filtered.append(ann)
        elif tgt == user_role:
            filtered.append(ann)
        elif tgt.startswith('Class:') and user_class and tgt == f'Class:{user_class}':
            filtered.append(ann)
    # Sort by priority and date
    def sort_key(a):
        p = PRIORITIES.index(a.get('priority', 'Medium')) if a.get('priority', 'Medium') in PRIORITIES else 1
        return (p, a.get('created_at', ''))
    filtered.sort(key=sort_key)
    return filtered 