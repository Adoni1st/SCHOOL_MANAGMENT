import os
import json
import shutil

# Define paths
old_path = r"C:/Users/hp/Downloads/school_manager/school_management_system/data/attendance.json"
new_path = os.path.join(os.path.dirname(__file__), 'attendance', 'attendance.json')

# Create attendance directory if it doesn't exist
os.makedirs(os.path.dirname(new_path), exist_ok=True)

# Copy the file
if os.path.exists(old_path):
    shutil.copy2(old_path, new_path)
    print(f"Successfully migrated attendance data to {new_path}")
else:
    print(f"Source file not found at {old_path}") 