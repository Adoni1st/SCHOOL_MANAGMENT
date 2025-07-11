import customtkinter as ctk
import json
from datetime import datetime
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket
import pickle

class StudentView(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Student Attendance")
        self.geometry("400x500")
        
        # Load student data
        self.load_student_data()
        
        # Initialize verification codes
        self.verification_codes = {}
        
        # Setup UI
        self.setup_ui()

    def load_student_data(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.students = config.get('students', [])
        except FileNotFoundError:
            self.students = []

    def setup_ui(self):
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Mark Attendance",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=20)

        # Server IP input
        self.ip_frame = ctk.CTkFrame(self.main_frame)
        self.ip_frame.pack(fill="x", padx=10, pady=5)
        
        self.ip_label = ctk.CTkLabel(self.ip_frame, text="Teacher IP:")
        self.ip_label.pack(side="left", padx=5)
        
        self.ip_entry = ctk.CTkEntry(self.ip_frame)
        self.ip_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.connect_button = ctk.CTkButton(
            self.ip_frame,
            text="Connect",
            command=self.connect_to_server
        )
        self.connect_button.pack(side="right", padx=5)

        # Student ID input
        self.id_frame = ctk.CTkFrame(self.main_frame)
        self.id_frame.pack(fill="x", padx=10, pady=5)
        
        self.id_label = ctk.CTkLabel(self.id_frame, text="Student ID:")
        self.id_label.pack(side="left", padx=5)
        
        self.id_entry = ctk.CTkEntry(self.id_frame)
        self.id_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Code input
        self.code_frame = ctk.CTkFrame(self.main_frame)
        self.code_frame.pack(fill="x", padx=10, pady=5)
        
        self.code_label = ctk.CTkLabel(self.code_frame, text="Enter Code:")
        self.code_label.pack(side="left", padx=5)
        
        self.code_entry = ctk.CTkEntry(self.code_frame)
        self.code_entry.pack(side="left", padx=5, fill="x", expand=True)

        # Email verification section
        self.email_frame = ctk.CTkFrame(self.main_frame)
        self.email_frame.pack(fill="x", padx=10, pady=5)
        
        self.email_label = ctk.CTkLabel(self.email_frame, text="Email Code:")
        self.email_label.pack(side="left", padx=5)
        
        self.email_entry = ctk.CTkEntry(self.email_frame)
        self.email_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        self.send_code_button = ctk.CTkButton(
            self.email_frame,
            text="Send Code",
            command=self.send_verification_code
        )
        self.send_code_button.pack(side="right", padx=5)

        # Submit button
        self.submit_button = ctk.CTkButton(
            self.main_frame,
            text="Mark Attendance",
            command=self.mark_attendance
        )
        self.submit_button.pack(pady=20)

        # Status label
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=10)

    def connect_to_server(self):
        try:
            server_ip = self.ip_entry.get().strip()
            if not server_ip:
                self.status_label.configure(text="Please enter teacher's IP address", text_color="red")
                return

            # Connect to server
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((server_ip, 5000))
            
            # Receive TOTP code
            received_code = pickle.loads(client_socket.recv(1024))
            client_socket.close()
            
            # Update code entry
            self.code_entry.delete(0, 'end')
            self.code_entry.insert(0, received_code)
            
            self.status_label.configure(text="Connected to teacher's server", text_color="green")
        except Exception as e:
            self.status_label.configure(text=f"Connection failed: {str(e)}", text_color="red")

    def generate_verification_code(self):
        return ''.join(random.choices(string.digits, k=6))

    def send_verification_code(self):
        student_id = self.id_entry.get().strip()
        
        # Find student
        student = next((s for s in self.students if s['id'] == student_id), None)
        if not student:
            self.status_label.configure(text="Invalid student ID", text_color="red")
            return

        # Generate verification code
        verification_code = self.generate_verification_code()
        self.verification_codes[student_id] = {
            'code': verification_code,
            'timestamp': datetime.now()
        }

        # Send email
        try:
            # Configure your email settings here
            sender_email = "senderpr13@gmail.com"  # Your Gmail address
            sender_password = "uebg vhdy ikqr jojn"   # Your app password
            
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
            
            self.status_label.configure(
                text="Verification code sent to your email",
                text_color="green"
            )
        except Exception as e:
            self.status_label.configure(
                text=f"Failed to send verification code: {str(e)}",
                text_color="red"
            )

    def mark_attendance(self):
        student_id = self.id_entry.get().strip()
        code = self.code_entry.get().strip()
        email_code = self.email_entry.get().strip()
        
        # Find student
        student = next((s for s in self.students if s['id'] == student_id), None)
        if not student:
            self.status_label.configure(text="Invalid student ID", text_color="red")
            return

        # Verify email code
        if student_id not in self.verification_codes:
            self.status_label.configure(text="Please request a verification code first", text_color="red")
            return

        stored_code = self.verification_codes[student_id]
        if stored_code['code'] != email_code:
            self.status_label.configure(text="Invalid email verification code", text_color="red")
            return

        # Check if code is expired (5 minutes)
        if (datetime.now() - stored_code['timestamp']).total_seconds() > 300:
            self.status_label.configure(text="Email verification code expired", text_color="red")
            return

        # Save attendance
        try:
            with open('attendance.json', 'r') as f:
                attendance_data = json.load(f)
        except FileNotFoundError:
            attendance_data = {}

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if 'attendance' not in attendance_data:
            attendance_data['attendance'] = []
        
        # Check if already marked
        if any(entry['id'] == student_id and entry['date'] == timestamp.split()[0] 
               for entry in attendance_data['attendance']):
            self.status_label.configure(text="Attendance already marked today", text_color="orange")
            return
        
        # Add attendance record
        attendance_record = {
            'id': student_id,
            'name': student['name'],
            'code_used': code,
            'email_code_used': email_code,
            'timestamp': timestamp,
            'date': timestamp.split()[0]
        }
        
        attendance_data['attendance'].append(attendance_record)
        
        with open('attendance.json', 'w') as f:
            json.dump(attendance_data, f, indent=4)
        
        # Clear entries
        self.id_entry.delete(0, 'end')
        self.code_entry.delete(0, 'end')
        self.email_entry.delete(0, 'end')
        
        # Remove used verification code
        del self.verification_codes[student_id]
        
        self.status_label.configure(
            text=f"Attendance marked for {student['name']}",
            text_color="green"
        )

if __name__ == "__main__":
    app = StudentView()
    app.mainloop() 