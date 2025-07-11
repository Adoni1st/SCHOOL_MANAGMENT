import customtkinter as ctk
import pyotp
import json
import time
import threading
from datetime import datetime
import os.path
import smtplib
import random
import string
import socket
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

PERIODS = ['Period 1', 'Period 2', 'Period 3', 'Period 4', 'Period 5', 'Period 6', 'Period 7', 'Period 8']
TOTP_INTERVAL = 20
VERIFICATION_CODE_LENGTH = 6

class AttendanceSystem(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Attendance System")
        self.geometry("1000x800")
        
        self.current_period = ctk.StringVar(value=PERIODS[0])
        self.attendance_data = {}
        self.students = []
        self.verification_codes = {}
        
        self.load_config()
        self.load_attendance_data()
        
        self.setup_ui()
        
        self.start_totp_thread()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.students = config['students']
                self.totp = pyotp.TOTP(config.get('totp_secret', pyotp.random_base32()), interval=TOTP_INTERVAL)
        except FileNotFoundError:
            print("Config file not found. Using empty student list.")
            self.students = []
            self.totp = pyotp.TOTP(pyotp.random_base32(), interval=TOTP_INTERVAL)

    def setup_ui(self):
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.teacher_frame = ctk.CTkFrame(self.main_frame)
        self.teacher_frame.pack(fill="x", padx=10, pady=5)
        
        self.teacher_label = ctk.CTkLabel(self.teacher_frame, text="Teacher Controls:")
        self.teacher_label.pack(side="left", padx=5)
        
        self.new_totp_button = ctk.CTkButton(
            self.teacher_frame,
            text="Generate New TOTP Secret",
            command=self.generate_new_totp
        )
        self.new_totp_button.pack(side="right", padx=5)

        self.period_label = ctk.CTkLabel(self.main_frame, text="Select Period:")
        self.period_label.pack(pady=5)
        
        self.period_menu = ctk.CTkOptionMenu(
            self.main_frame,
            values=PERIODS,
            variable=self.current_period,
            command=self.period_changed
        )
        self.period_menu.pack(pady=5)

        self.totp_frame = ctk.CTkFrame(self.main_frame)
        self.totp_frame.pack(pady=20)
        
        self.totp_label = ctk.CTkLabel(self.totp_frame, text="Current TOTP:")
        self.totp_label.pack()
        
        self.totp_display = ctk.CTkLabel(self.totp_frame, text=self.totp.now(), font=("Arial", 24))
        self.totp_display.pack()
        
        self.progress_bar = ctk.CTkProgressBar(self.totp_frame)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(1.0)

        self.student_frame = ctk.CTkFrame(self.main_frame)
        self.student_frame.pack(fill="both", expand=True, pady=20)
        
        self.id_frame = ctk.CTkFrame(self.student_frame)
        self.id_frame.pack(fill="x", padx=10, pady=5)
        
        self.id_label = ctk.CTkLabel(self.id_frame, text="Student ID:")
        self.id_label.pack(side="left", padx=5)
        
        self.id_entry = ctk.CTkEntry(self.id_frame)
        self.id_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.mark_button = ctk.CTkButton(
            self.id_frame,
            text="Mark Attendance",
            command=self.mark_attendance
        )
        self.mark_button.pack(side="right", padx=5)

        self.verification_frame = ctk.CTkFrame(self.student_frame)
        self.verification_frame.pack(fill="x", padx=10, pady=5)
        
        self.verification_label = ctk.CTkLabel(self.verification_frame, text="Email Verification Code:")
        self.verification_label.pack(side="left", padx=5)
        
        self.verification_entry = ctk.CTkEntry(self.verification_frame)
        self.verification_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.send_code_button = ctk.CTkButton(
            self.verification_frame,
            text="Send Code",
            command=self.send_verification_code
        )
        self.send_code_button.pack(side="right", padx=5)

        self.attendance_label = ctk.CTkLabel(self.student_frame, text="Attendance List:")
        self.attendance_label.pack(pady=5)
        
        self.attendance_listbox = ctk.CTkTextbox(self.student_frame, height=300)
        self.attendance_listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.submit_button = ctk.CTkButton(
            self.main_frame,
            text="Submit Attendance",
            command=self.submit_attendance
        )
        self.submit_button.pack(pady=20)

        self.update_attendance_list()

    def generate_verification_code(self):
        return ''.join(random.choices(string.digits, k=VERIFICATION_CODE_LENGTH))

    def get_ip_address(self):
        try:
            response = requests.get('https://api.ipify.org?format=json')
            return response.json()['ip']
        except:
            return "Unknown"

    def send_verification_code(self):
        student_id = self.id_entry.get().strip()
        student = next((s for s in self.students if s['id'] == student_id), None)
        
        if not student:
            ctk.messagebox.showerror("Error", "Invalid student ID")
            return

        verification_code = self.generate_verification_code()
        self.verification_codes[student_id] = {
            'code': verification_code,
            'timestamp': datetime.now(),
            'ip': self.get_ip_address()
        }

        try:
            sender_email = "senderpr13@gmail.com"
            sender_password = "uebg vhdy ikqr jojn"
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = student['email']
            msg['Subject'] = "Attendance Verification Code"
            
            body = f"""
            Hello {student['name']},
            
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
            
            ctk.messagebox.showinfo("Success", "Verification code sent to your email")
        except Exception as e:
            ctk.messagebox.showerror("Error", f"Failed to send verification code: {str(e)}")

    def mark_attendance(self):
        student_id = self.id_entry.get().strip()
        verification_code = self.verification_entry.get().strip()
        current_totp = self.totp.now()
        
        student = next((s for s in self.students if s['id'] == student_id), None)
        if not student:
            ctk.messagebox.showerror("Error", "Invalid student ID")
            return

        if student_id not in self.verification_codes:
            ctk.messagebox.showerror("Error", "Please request a verification code first")
            return

        stored_code = self.verification_codes[student_id]
        if stored_code['code'] != verification_code:
            ctk.messagebox.showerror("Error", "Invalid verification code")
            return

        if (datetime.now() - stored_code['timestamp']).total_seconds() > 300:
            ctk.messagebox.showerror("Error", "Verification code expired")
            return

        period = self.current_period.get()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if period not in self.attendance_data:
            self.attendance_data[period] = []
        
        attendance_record = {
            'student_id': student_id,
            'name': student['name'],
            'timestamp': timestamp,
            'totp': current_totp,
            'ip': stored_code['ip']
        }
        
        self.attendance_data[period].append(attendance_record)
        self.save_attendance_data()
        self.update_attendance_list()
        
        ctk.messagebox.showinfo("Success", f"Attendance marked for {student['name']}")
        
        self.id_entry.delete(0, 'end')
        self.verification_entry.delete(0, 'end')
        del self.verification_codes[student_id]

    def update_attendance_list(self):
        self.attendance_listbox.delete("1.0", "end")
        period = self.current_period.get()
        
        if period in self.attendance_data:
            for record in self.attendance_data[period]:
                self.attendance_listbox.insert("end", f"{record['name']} ({record['student_id']}) - {record['timestamp']}\n")

    def submit_attendance(self):
        if not self.attendance_data:
            ctk.messagebox.showwarning("Warning", "No attendance records to submit")
            return
        
        try:
            with open('attendance.json', 'w') as f:
                json.dump(self.attendance_data, f, indent=4)
            ctk.messagebox.showinfo("Success", "Attendance data submitted successfully")
            self.attendance_data = {}
            self.update_attendance_list()
        except Exception as e:
            ctk.messagebox.showerror("Error", f"Failed to submit attendance: {str(e)}")

    def start_totp_thread(self):
        def update_totp():
            while True:
                time.sleep(1)
                try:
                    self.totp_display.configure(text=self.totp.now())
                    remaining = self.totp.interval - (int(time.time()) % self.totp.interval)
                    self.progress_bar.set(remaining / self.totp.interval)
                except Exception as e:
                    print(f"Error updating TOTP: {e}")
        
        thread = threading.Thread(target=update_totp, daemon=True)
        thread.start()

    def load_attendance_data(self):
        try:
            with open('attendance.json', 'r') as f:
                self.attendance_data = json.load(f)
        except FileNotFoundError:
            self.attendance_data = {}

    def save_attendance_data(self):
        with open('attendance.json', 'w') as f:
            json.dump(self.attendance_data, f, indent=4)

    def period_changed(self, period):
        self.update_attendance_list()

    def generate_new_totp(self):
        new_secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(new_secret, interval=TOTP_INTERVAL)
        
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            config['totp_secret'] = new_secret
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            ctk.messagebox.showinfo("Success", "New TOTP secret generated")
        except Exception as e:
            ctk.messagebox.showerror("Error", f"Failed to save new TOTP secret: {str(e)}")

if __name__ == "__main__":
    app = AttendanceSystem()
    app.mainloop() 