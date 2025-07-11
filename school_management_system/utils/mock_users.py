# mock_users.py
# This module provides a hardcoded list of users and utility functions for testing/demo purposes.

# List of mock users for the school management app
users = [
    {"username": "admin", "password": "admin123", "role": "Admin"},
    {"username": "teacher1", "password": "teacher123", "role": "Teacher"},
    {"username": "student1", "password": "student123", "role": "Student"},
]

def get_user_by_username(username: str):
    """
    Returns the user dictionary with the given username, or None if not found.
    """
    for user in users:
        if user["username"] == username:
            return user
    return None

def verify_user(username: str, password: str, role: str) -> bool:
    """
    Returns True if a user with matching username, plaintext password, and role exists.
    Otherwise, returns False.
    """
    for user in users:
        if user["username"] == username and user["password"] == password and user["role"] == role:
            return True
    return False 