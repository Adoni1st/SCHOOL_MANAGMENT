import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

def get_attendance_file_path() -> str:
    """Get the path to the attendance.json file"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'attendance', 'attendance.json')

def load_attendance_data() -> Dict[str, Dict[str, str]]:
    """Load attendance data from JSON file"""
    try:
        with open(get_attendance_file_path(), 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

def save_attendance_data(data: Dict[str, Dict[str, str]]) -> bool:
    """Save attendance data to JSON file"""
    try:
        with open(get_attendance_file_path(), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving attendance data: {e}")
        return False

def mark_attendance(email: str, date: str, status: str) -> bool:
    """
    Mark attendance for a student
    
    Args:
        email: Student's email
        date: Date in YYYY-MM-DD format
        status: One of "Present", "Absent", "Late"
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        return False
    
    # Validate status
    if status not in ["Present", "Absent", "Late"]:
        return False
    
    # Load current data
    data = load_attendance_data()
    
    # Initialize student's attendance if not exists
    if email not in data:
        data[email] = {}
    
    # Update attendance
    data[email][date] = status
    
    # Save changes
    return save_attendance_data(data)

def get_student_attendance(email: str) -> Dict[str, str]:
    """Get attendance records for a specific student"""
    try:
        with open(get_attendance_file_path(), 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    
    # Filter attendance records for this student
    student_records = {}
    for record in data.get('attendance', []):
        if record.get('email') == email:
            student_records[record['date']] = "Present"  # All records in attendance.json are present
    
    return student_records

def calculate_percentage(attendance_dict: Dict[str, str]) -> float:
    """Calculate attendance percentage"""
    if not attendance_dict:
        return 0.0
    
    total_days = len(attendance_dict)
    present_days = sum(1 for status in attendance_dict.values() if status == "Present")
    
    return (present_days / total_days) * 100

def get_attendance_stats(attendance_data: Dict[str, str]) -> Dict[str, Any]:
    """Calculate attendance statistics from attendance data"""
    if not attendance_data:
        return {
            'present': 0,
            'absent': 0,
            'late': 0,
            'percentage': 0.0
        }
    
    present = sum(1 for status in attendance_data.values() if status == "Present")
    absent = sum(1 for status in attendance_data.values() if status == "Absent")
    late = sum(1 for status in attendance_data.values() if status == "Late")
    total = present + absent + late
    
    percentage = (present / total * 100) if total > 0 else 0.0
    
    return {
        'present': present,
        'absent': absent,
        'late': late,
        'percentage': percentage
    }

def get_class_attendance(class_code: str, date: Optional[str] = None) -> Dict[str, str]:
    """
    Get attendance records for all students in a class
    
    Args:
        class_code: Class code to filter by
        date: Optional date to filter by (YYYY-MM-DD)
    
    Returns:
        Dict mapping student emails to their attendance status
    """
    # Load users to get class information
    users_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users.json')
    try:
        with open(users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except Exception:
        return {}
    
    # Get students in the class
    class_students = [
        user['email'] for user in users 
        if user.get('role') == 'Student' and user.get('class_code') == class_code
    ]
    
    # Load attendance data
    attendance_data = load_attendance_data()
    
    # Filter by date if specified
    if date:
        return {
            email: attendance_data.get(email, {}).get(date, "Not Marked")
            for email in class_students
        }
    
    # Return all attendance records for class students
    return {
        email: attendance_data.get(email, {})
        for email in class_students
    } 