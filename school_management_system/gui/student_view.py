import os
import sys
import customtkinter as ctk
import socket
import json
import tkinter.messagebox as mb
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import pickle
from utils.attendance_utils import get_student_attendance, get_attendance_stats

class StudentAttendanceView(ctk.CTkFrame):
    def __init__(self, parent, user_data):
        super().__init__(parent, fg_color="transparent")
        self.user_data = user_data
        self.verification_codes = {}
        self.setup_ui()
        self.load_attendance_stats()

    def setup_ui(self):
        # Main vertical layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # --- INTERACTIVE UI CARD ---
        self.interactive_card = ctk.CTkFrame(self, fg_color="#f8f9fa", corner_radius=12)
        self.interactive_card.grid(row=0, column=0, sticky="ew", padx=30, pady=(24, 6))

        ctk.CTkLabel(
            self.interactive_card,
            text="Mark Attendance",
            font=("Arial", 22, "bold"),
            text_color="#1976d2"
        ).pack(pady=(12, 8))

        # Teacher IP
        ip_frame = ctk.CTkFrame(self.interactive_card, fg_color="transparent")
        ip_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(ip_frame, text="Teacher IP:").pack(side="left", padx=5)
        self.ip_entry = ctk.CTkEntry(ip_frame)
        self.ip_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(ip_frame, text="Connect", command=self.connect_to_server, width=90).pack(side="right", padx=5)

        # TOTP Code
        code_frame = ctk.CTkFrame(self.interactive_card, fg_color="transparent")
        code_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(code_frame, text="Enter Code:").pack(side="left", padx=5)
        self.code_entry = ctk.CTkEntry(code_frame)
        self.code_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Email Verification
        email_frame = ctk.CTkFrame(self.interactive_card, fg_color="transparent")
        email_frame.pack(fill="x", pady=4, padx=10)
        ctk.CTkLabel(email_frame, text="Email Code:").pack(side="left", padx=5)
        self.email_entry = ctk.CTkEntry(email_frame)
        self.email_entry.pack(side="left", padx=5, fill="x", expand=True)
        ctk.CTkButton(email_frame, text="Send Code", command=self.send_verification_code, width=110).pack(side="right", padx=5)

        # Submit button
        ctk.CTkButton(self.interactive_card, text="Mark Attendance", command=self.mark_attendance, width=180, fg_color="#1976d2", hover_color="#1565c0").pack(pady=12)

        # Status label
        self.status_label = ctk.CTkLabel(self.interactive_card, text="", font=("Arial", 12), text_color="#d32f2f")
        self.status_label.pack(pady=(0, 8))

        # --- SEPARATOR ---
        ctk.CTkLabel(self, text="", height=2, fg_color="#e0e0e0").grid(row=1, column=0, sticky="ew", padx=30)

        # --- STATS & HISTORY CARD ---
        self.stats_card = ctk.CTkFrame(self, fg_color="#fff", corner_radius=12)
        self.stats_card.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 24))
        self.stats_card.columnconfigure((0,1,2,3), weight=1)

        # Cards for stats
        self.percent_label = ctk.CTkLabel(self.stats_card, text="Attendance Percentage\n0.0%", font=("Segoe UI", 16), fg_color="#e3f2fd", corner_radius=10, justify="center")
        self.percent_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.present_label = ctk.CTkLabel(self.stats_card, text="Days Present\n0", font=("Segoe UI", 16), fg_color="#e8f5e9", corner_radius=10, justify="center")
        self.present_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.absent_label = ctk.CTkLabel(self.stats_card, text="Days Absent\n0", font=("Segoe UI", 16), fg_color="#ffebee", corner_radius=10, justify="center")
        self.absent_label.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        self.late_label = ctk.CTkLabel(self.stats_card, text="Days Late\n0", font=("Segoe UI", 16), fg_color="#fff3e0", corner_radius=10, justify="center")
        self.late_label.grid(row=0, column=3, padx=10, pady=10, sticky="ew")

        # Attendance History
        ctk.CTkLabel(self.stats_card, text="Attendance History", font=("Segoe UI", 18, "bold"), text_color="#1976d2").grid(row=1, column=0, columnspan=4, pady=(20, 10))
        self.history_scroll = ctk.CTkScrollableFrame(self.stats_card, height=260)
        self.history_scroll.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)

        # Refresh Button
        refresh_btn = ctk.CTkButton(self, text="Refresh", command=self.load_attendance_stats)
        refresh_btn.grid(row=3, column=0, pady=(0, 10))

    def load_attendance_stats(self):
        attendance_data = get_student_attendance(self.user_data.get('email'))
        stats = get_attendance_stats(attendance_data)
        self.percent_label.configure(text=f"Attendance Percentage\n{stats['percentage']:.1f}%")
        self.present_label.configure(text=f"Days Present\n{stats['present']}")
        self.absent_label.configure(text=f"Days Absent\n{stats['absent']}")
        self.late_label.configure(text=f"Days Late\n{stats['late']}")
        # Clear history
        for widget in self.history_scroll.winfo_children():
            widget.destroy()
        # Add history
        for date, status in sorted(attendance_data.items(), reverse=True):
            color = {"Present": "#388e3c", "Absent": "#d32f2f", "Late": "#fbc02d"}.get(status, "#757575")
            row = ctk.CTkFrame(self.history_scroll)
            row.pack(fill="x", pady=2, padx=5)
            ctk.CTkLabel(row, text=date, font=("Segoe UI", 14)).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=status, font=("Segoe UI", 14), text_color=color).pack(side="right", padx=10)

    def connect_to_server(self):
        try:
            server_ip = self.ip_entry.get().strip()
            if not server_ip:
                self.status_label.configure(text="Please enter teacher's IP address", text_color="red")
                return
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, 5000))
            received_code = pickle.loads(client_socket.recv(1024))
            client_socket.close()
            self.code_entry.delete(0, 'end')
            self.code_entry.insert(0, received_code)
            self.status_label.configure(text="Connected to teacher's server", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Connection failed: {str(e)}", text_color="red")

    def generate_verification_code(self):
        return ''.join(random.choices(string.digits, k=6))

    def send_verification_code(self):
        email = self.user_data.get('email')
        if not email:
            self.status_label.configure(text="No email found in user data", text_color="red")
            return
        verification_code = self.generate_verification_code()
        self.verification_codes[email] = {
            'code': verification_code,
            'timestamp': datetime.now()
        }
        try:
            sender_email = "senderpr13@gmail.com"
            sender_password = "uebg vhdy ikqr jojn"
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = email
            msg['Subject'] = "Attendance Verification Code"
            body = f"""
            Hello {self.user_data.get('full_name')},
            Your verification code for attendance is: {verification_code}
            This code will expire in 5 minutes.
            If you did not request this code, please ignore this email.
            """
            msg.attach(MIMEText(body, 'plain'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            self.status_label.configure(text="Verification code sent to your email", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Failed to send verification code: {str(e)}", text_color="red")

    def mark_attendance(self):
        email = self.user_data.get('email')
        code = self.code_entry.get().strip()
        email_code = self.email_entry.get().strip()
        if not email or not code or not email_code:
            self.status_label.configure(text="Please fill in all fields", text_color="red")
            return
        if email not in self.verification_codes:
            self.status_label.configure(text="Please request a verification code first", text_color="red")
            return
        stored_code = self.verification_codes[email]
        if stored_code['code'] != email_code:
            self.status_label.configure(text="Invalid email verification code", text_color="red")
            return
        if (datetime.now() - stored_code['timestamp']).total_seconds() > 300:
            self.status_label.configure(text="Email verification code expired", text_color="red")
            return
        
        # Create attendance directory if it doesn't exist
        attendance_dir = os.path.join(os.path.dirname(__file__), '../attendance')
        os.makedirs(attendance_dir, exist_ok=True)
        attendance_file = os.path.join(attendance_dir, 'attendance.json')
        
        try:
            if os.path.exists(attendance_file):
                with open(attendance_file, 'r') as f:
                    attendance_data = json.load(f)
            else:
                attendance_data = {'attendance': []}
                
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if any(entry.get('email') == email and entry.get('date') == timestamp.split()[0] for entry in attendance_data['attendance']):
                self.status_label.configure(text="Attendance already marked today", text_color="orange")
                return
                
            attendance_record = {
                'email': email,
                'name': self.user_data.get('full_name'),
                'code_used': code,
                'email_code_used': email_code,
                'timestamp': timestamp,
                'date': timestamp.split()[0]
            }
            attendance_data['attendance'].append(attendance_record)
            
            with open(attendance_file, 'w') as f:
                json.dump(attendance_data, f, indent=4)
                
            self.status_label.configure(text="Attendance marked successfully", text_color="green")
            self.code_entry.delete(0, 'end')
            self.email_entry.delete(0, 'end')
            self.load_attendance_stats()
            
        except Exception as e:
            self.status_label.configure(text=f"Error marking attendance: {str(e)}", text_color="red") 