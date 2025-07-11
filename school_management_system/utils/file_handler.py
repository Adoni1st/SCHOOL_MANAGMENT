import json
import os
from typing import Any

USERS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users.json')

def read_json(filepath: str) -> Any:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def write_json(filepath: str, data: Any) -> None:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def load_users():
    """
    Safely reads from data/users.json and returns a list of users.
    Returns an empty list if the file doesn't exist or is invalid/corrupted.
    """
    try:
        if not os.path.exists(USERS_PATH):
            print(f"[INFO] {USERS_PATH} does not exist. Returning empty user list.")
            return []
        with open(USERS_PATH, 'r', encoding='utf-8') as f:
            try:
                users = json.load(f)
                if not isinstance(users, list):
                    print(f"[WARNING] {USERS_PATH} does not contain a list. Returning empty user list.")
                    return []
                return users
            except json.JSONDecodeError:
                print(f"[WARNING] {USERS_PATH} is corrupted or invalid JSON. Returning empty user list.")
                return []
    except Exception as e:
        print(f"[ERROR] Failed to read {USERS_PATH}: {e}")
        return []

def save_user(new_user: dict):
    """
    Appends a new user to data/users.json, handling errors gracefully.
    Returns True if successful, False otherwise.
    """
    users = load_users()
    users.append(new_user)
    try:
        with open(USERS_PATH, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=4)
        print(f"[INFO] User {new_user.get('username')} saved successfully.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to write to {USERS_PATH}: {e}")
        return False
