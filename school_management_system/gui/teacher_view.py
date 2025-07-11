import customtkinter as ctk
from datetime import datetime
import json
import os
from utils.attendance_utils import (
    mark_attendance,
    get_class_attendance,
    get_attendance_stats
)
import pyotp
import time
import threading
import socket
import pickle
import tkinter.messagebox as mb

class TeacherAttendanceView(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color="transparent")
        self.user_data = user_data
        self.setup_ui()
        self.start_server()

    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Server info
        server_frame = ctk.CTkFrame(self.main_frame, fg_color="#f8f9fa", corner_radius=12)
        server_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            server_frame,
            text="Server Information",
            font=("Arial", 22, "bold"),
            text_color="#1976d2"
        ).pack(pady=(12, 8))

        # IP Address
        ip_frame = ctk.CTkFrame(server_frame, fg_color="transparent")
        ip_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(ip_frame, text="Server IP:").pack(side="left", padx=5)
        self.ip_label = ctk.CTkLabel(ip_frame, text="Loading...")
        self.ip_label.pack(side="left", padx=5)

        # TOTP Code
        totp_frame = ctk.CTkFrame(server_frame, fg_color="transparent")
        totp_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(totp_frame, text="Current Code:").pack(side="left", padx=5)
        self.totp_label = ctk.CTkLabel(totp_frame, text="Loading...")
        self.totp_label.pack(side="left", padx=5)

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(totp_frame)
        self.progress_bar.pack(side="right", padx=5, fill="x", expand=True)
        self.progress_bar.set(0)

        # Attendance Records
        records_frame = ctk.CTkFrame(self.main_frame, fg_color="#fff", corner_radius=12)
        records_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            records_frame,
            text="Today's Attendance Records",
            font=("Arial", 22, "bold"),
            text_color="#1976d2"
        ).pack(pady=(12, 8))

        self.attendance_scroll = ctk.CTkScrollableFrame(records_frame)
        self.attendance_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # Refresh Button
        refresh_btn = ctk.CTkButton(self.main_frame, text="Refresh", command=self.load_attendance_records)
        refresh_btn.pack(pady=5)

        # Start updating TOTP
        self.update_totp()

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(('0.0.0.0', 5000))
            self.server_socket.listen(5)
            
            # Get server IP
            hostname = socket.gethostname()
            self.ip_label.configure(text=socket.gethostbyname(hostname))
            
            # Start server thread
            import threading
            self.server_thread = threading.Thread(target=self.handle_connections, daemon=True)
            self.server_thread.start()
        except Exception as e:
            self.ip_label.configure(text=f"Error: {str(e)}")

    def handle_connections(self):
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                # Send current TOTP code
                client_socket.send(pickle.dumps(self.current_totp))
                client_socket.close()
            except:
                continue

    def update_totp(self):
        try:
            # Generate new TOTP code
            import pyotp
            self.current_totp = pyotp.TOTP('JBSWY3DPEHPK3PXP').now()
            self.totp_label.configure(text=self.current_totp)
            
            # Reset progress bar
            self.progress_bar.set(0)
            
            # Start progress bar animation
            self.animate_progress()
        except Exception as e:
            self.totp_label.configure(text=f"Error: {str(e)}")
        
        # Schedule next update
        self.after(20000, self.update_totp)  # Update every 20 seconds

    def animate_progress(self):
        current = self.progress_bar.get()
        if current >= 1:
            return
        
        self.progress_bar.set(current + 0.01)
        self.after(200, self.animate_progress)  # Update every 200ms

    def load_attendance_records(self):
        try:
            attendance_file = os.path.join(os.path.dirname(__file__), '../attendance/attendance.json')
            with open(attendance_file, 'r') as f:
                attendance_data = json.load(f)
        except FileNotFoundError:
            attendance_data = {'attendance': []}
        
        # Clear existing records
        for widget in self.attendance_scroll.winfo_children():
            widget.destroy()
        
        # Get today's records
        today = datetime.now().strftime("%Y-%m-%d")
        today_records = [
            record for record in attendance_data.get('attendance', [])
            if record.get('date') == today
        ]
        
        if not today_records:
            ctk.CTkLabel(
                self.attendance_scroll,
                text="No attendance records for today",
                font=("Segoe UI", 14),
                text_color="#757575"
            ).pack(pady=20)
            return
        
        # Display records
        for record in today_records:
            # Create record card
            card = ctk.CTkFrame(self.attendance_scroll, fg_color="#f5f5f5", corner_radius=5)
            card.pack(fill="x", pady=5)
            
            # Student info
            ctk.CTkLabel(
                card,
                text=f"Student: {record.get('name', 'N/A')} ({record.get('email', 'N/A')})",
                font=("Segoe UI", 14, "bold"),
                text_color="#424242"
            ).pack(anchor="w", padx=10, pady=(10, 5))
            
            # Time
            ctk.CTkLabel(
                card,
                text=f"Time: {record.get('timestamp', 'N/A')}",
                font=("Segoe UI", 12),
                text_color="#757575"
            ).pack(anchor="w", padx=10, pady=(0, 5))
            
            # Verification info
            ctk.CTkLabel(
                card,
                text=f"TOTP Code: {record.get('code_used', 'N/A')}",
                font=("Segoe UI", 12),
                text_color="#757575"
            ).pack(anchor="w", padx=10, pady=(0, 10))

    def get_teacher_classes(self):
        """Get list of classes assigned to the teacher"""
        try:
            classes_file = os.path.join(os.path.dirname(__file__), '../data/classes.json')
            with open(classes_file, 'r', encoding='utf-8') as f:
                classes = json.load(f)
            
            # Filter classes for this teacher
            teacher_classes = [
                class_info['code'] for class_info in classes
                if class_info.get('teacher_email') == self.user_data.get('email')
            ]
            return teacher_classes
        except Exception as e:
            print(f"Error loading classes: {e}")
            return []
    
    def load_students(self, *args):
        """Load students for the selected class"""
        # Clear existing entries
        for widget in self.students_scroll.winfo_children():
            widget.destroy()
        self.student_entries.clear()
        
        # Get selected class
        class_code = self.class_var.get()
        if not class_code:
            return
        
        # Load students
        try:
            users_file = os.path.join(os.path.dirname(__file__), '../data/users.json')
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            # Filter students in the class
            class_students = [
                user for user in users
                if user.get('role') == 'Student' and user.get('class_code') == class_code
            ]
            
            # Create entries for each student
            for student in class_students:
                self.create_student_attendance_entry(student)
                
        except Exception as e:
            print(f"Error loading students: {e}")
    
    def create_student_attendance_entry(self, student):
        """Create attendance entry for a student"""
        entry_frame = ctk.CTkFrame(self.students_scroll, fg_color="#f5f5f5", corner_radius=8)
        entry_frame.pack(fill="x", pady=5)
        
        # Student info
        info_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=f"{student.get('full_name', 'N/A')}",
            font=("Segoe UI", 12, "bold"),
            text_color="#424242"
        ).pack(side="left")
        
        ctk.CTkLabel(
            info_frame,
            text=f"Roll No: {student.get('roll_number', 'N/A')}",
            font=("Segoe UI", 12),
            text_color="#757575"
        ).pack(side="left", padx=(10, 0))
        
        # Attendance status
        status_var = ctk.StringVar(value="Present")
        status_frame = ctk.CTkFrame(entry_frame, fg_color="transparent")
        status_frame.pack(side="right", padx=15, pady=10)
        
        # Create radio buttons for status
        for status in ["Present", "Absent", "Late"]:
            ctk.CTkRadioButton(
                status_frame,
                text=status,
                variable=status_var,
                value=status,
                font=("Segoe UI", 12)
            ).pack(side="left", padx=10)
        
        # Store the entry
        self.student_entries[student['email']] = {
            'frame': entry_frame,
            'status_var': status_var
        }
    
    def save_attendance(self):
        """Save attendance for all students"""
        date = self.date_entry.get().strip()
        class_code = self.class_var.get()
        
        if not date or not class_code:
            return
        
        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return
        
        # Save attendance for each student
        for email, entry in self.student_entries.items():
            status = entry['status_var'].get()
            mark_attendance(email, date, status)
        
        # Refresh the view
        self.load_students() 