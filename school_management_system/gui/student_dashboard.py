import os
import sys
import customtkinter as ctk
from PIL import Image
import json
from datetime import datetime
from gui.student_view import StudentAttendanceView
from announcements import filter_announcements, PRIORITIES
import socket
import threading
import queue
from Discussion.functions import send_data, receive_data
import time
from gui.schedule_utils import load_class_codes, load_timetable_for_class
import tkinter as tk

class ChatClient:
    def __init__(self):
        self.host = 'localhost'
        self.port = 5001
        self.socket = None
        self.message_queue = queue.Queue()
        self.connected = False
        self.username = None
        self.announcements = []
        self.receive_thread = None
    
    def connect(self, host, port=5001):
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(3.0)  # Connection timeout only
            self.socket.connect((host, port))
            self.socket.settimeout(None)  # Remove timeout after connection
            self.host = host
            self.port = port
            self.connected = True
            
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
        except socket.timeout:
            return "Connection timed out"
        except ConnectionRefusedError:
            return "Connection refused"
        except Exception as e:
            return str(e)
    
    def disconnect(self):
        """Disconnect from the server"""
        if not self.connected:
            return
            
        self.connected = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Wait for receive thread to finish
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
    
    def receive_messages(self):
        """Receive messages from the server"""
        while self.connected:
            try:
                data = receive_data(self.socket)
                if not data:
                    if self.connected:  # Only notify if still connected
                        self.message_queue.put({
                            "type": "system",
                            "data": {
                                "content": "Server closed connection"
                            }
                        })
                    break
                
                if data["type"] == "announcement":
                    self.announcements.append(data["data"])
                
                self.message_queue.put(data)
            except socket.timeout:
                continue
            except:
                if self.connected:  # Only notify if still connected
                    self.message_queue.put({
                        "type": "system",
                        "data": {
                            "content": "Connection lost"
                        }
                    })
                break
        
        self.connected = False
    
    def send_message(self, message):
        """Send a message to the server"""
        if not self.connected:
            return False
        
        try:
            send_data(self.socket, {
                "type": "message",
                "data": message
            })
            return True
        except:
            return False

class StudentDashboard(ctk.CTk):
    def __init__(self, user_data):
        super().__init__()
        
        # Configure window
        self.title("Student Dashboard")
        try:
            self.state('zoomed')
        except Exception:
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            self.geometry(f"{width}x{height}")
        self.minsize(800, 600)
        
        # Store user data
        self.user_data = user_data
        
        # Configure appearance
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True)
        
        # Create header
        self.create_header()
        
        # Create tab view
        self.tabview = ctk.CTkTabview(self.main_container)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add tabs
        self.tabview.add("Dashboard")
        self.tabview.add("Attendance")
        self.tabview.add("Announcements")
        self.tabview.add("Profile")
        self.tabview.add("Discussion")
        self.tabview.add("Schedule")
        
        # Initialize tabs
        self.init_dashboard_tab()
        self.init_attendance_tab()
        self.init_announcements_tab()
        self.init_profile_tab()
        self.init_discussion_tab()
        self.init_schedule_tab()
        
        # Start clock update
        self.update_clock()
    
    def create_header(self):
        """Create the header with user info and clock"""
        header = ctk.CTkFrame(self.main_container, height=70, fg_color="#f5f7fa", corner_radius=16)
        header.pack(fill="x", padx=24, pady=16)
        
        # User info
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="left", padx=24)
        
        # Profile avatar placeholder
        avatar = ctk.CTkLabel(user_frame, text="👤", font=("Segoe UI", 28))
        avatar.pack(side="left", padx=(0, 12))
        
        ctk.CTkLabel(
            user_frame,
            text=f"Welcome, {self.user_data.get('full_name', 'Student')}",
            font=("Segoe UI", 18, "bold"),
            text_color="#1976d2"
        ).pack(side="left")
        
        # Clock
        self.clock_label = ctk.CTkLabel(
            header,
            text="",
            font=("Segoe UI", 16),
            text_color="#1976d2"
        )
        self.clock_label.pack(side="right", padx=24)
        
        # Logout button
        logout_btn = ctk.CTkButton(
            header,
            text="Logout",
            command=self.logout,
            width=110,
            fg_color="#e3eafc",
            hover_color="#d1e0fc",
            text_color="#1976d2",
            font=("Segoe UI", 14, "bold"),
            corner_radius=8
        )
        logout_btn.pack(side="right", padx=24)
    
    def update_clock(self):
        """Update the clock display"""
        current_time = datetime.now().strftime("%I:%M:%S %p")
        self.clock_label.configure(text=current_time)
        self.after(1000, self.update_clock)
    
    def logout(self):
        """Handle logout"""
        self.quit()
    
    def init_dashboard_tab(self):
        """Initialize the dashboard tab"""
        tab = self.tabview.tab("Dashboard")
        
        # Welcome message
        ctk.CTkLabel(
            tab,
            text="Welcome to Your Dashboard",
            font=("Segoe UI", 28, "bold"),
            text_color="#1976d2"
        ).pack(pady=32)
        
        # Quick stats in cards
        stats_frame = ctk.CTkFrame(tab, fg_color="#f5f7fa", corner_radius=16)
        stats_frame.pack(fill="x", padx=32, pady=16)
        
        # Class info card
        class_card = ctk.CTkFrame(stats_frame, fg_color="#e3eafc", corner_radius=12)
        class_card.pack(side="left", padx=16, pady=16, fill="x", expand=True)
        ctk.CTkLabel(
            class_card,
            text="Class",
            font=("Segoe UI", 18, "bold"),
            text_color="#1976d2"
        ).pack(pady=8)
        ctk.CTkLabel(
            class_card,
            text=self.user_data.get('class', 'N/A'),
            font=("Segoe UI", 16)
        ).pack(pady=8)
        
        # Roll number card
        roll_card = ctk.CTkFrame(stats_frame, fg_color="#e3eafc", corner_radius=12)
        roll_card.pack(side="left", padx=16, pady=16, fill="x", expand=True)
        ctk.CTkLabel(
            roll_card,
            text="Roll Number",
            font=("Segoe UI", 18, "bold"),
            text_color="#1976d2"
        ).pack(pady=8)
        roll_number = (
            self.user_data.get('roll_number')
            or self.user_data.get('roll')
            or self.user_data.get('roll_no')
            or 'N/A'
        )
        ctk.CTkLabel(
            roll_card,
            text=str(roll_number),
            font=("Segoe UI", 16)
        ).pack(pady=8)
    
    def init_attendance_tab(self):
        """Initialize the attendance tab"""
        tab = self.tabview.tab("Attendance")
        # Make the whole attendance view scrollable
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True)
        attendance_view = StudentAttendanceView(scroll_frame, self.user_data)
        attendance_view.pack(fill="both", expand=True)
    
    def init_announcements_tab(self):
        """Initialize the announcements tab"""
        tab = self.tabview.tab("Announcements")
        # Filter announcements for this user
        try:
            from announcements import filter_announcements
            user_role = self.user_data.get('role', 'Student')
            user_class = self.user_data.get('class', None)
            announcements = filter_announcements(user_role=user_role, user_class=user_class, hide_expired=True)
        except Exception:
            announcements = []
        # Create scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(tab)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        if not announcements:
            ctk.CTkLabel(scroll_frame, text="No announcements.", font=("Segoe UI", 14, "italic"), text_color="#888").pack(pady=30)
            return
        for ann in announcements:
            # Card color by priority
            priority_color = {
                "High": "#dc3545",
                "Medium": "#ffc107",
                "Low": "#28a745"
            }.get(ann.get("priority", "Low"), "#28a745")
            card = ctk.CTkFrame(scroll_frame, fg_color="#fff", corner_radius=10)
            card.pack(fill="x", padx=10, pady=8)
            # Priority dot
            ctk.CTkLabel(card, text="●", text_color=priority_color, font=("Segoe UI", 20)).pack(side="left", padx=10, pady=10)
            # Content
            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            ctk.CTkLabel(content_frame, text=ann.get("title", ""), font=("Segoe UI", 16, "bold")).pack(anchor="w")
            ctk.CTkLabel(content_frame, text=ann.get("content", ""), font=("Segoe UI", 14)).pack(anchor="w", pady=5)
            meta = f"Target: {ann.get('target', '-')}, Priority: {ann.get('priority', '-')}, Expires: {ann.get('expiry_date', '-')[:10]}"
            ctk.CTkLabel(content_frame, text=meta, font=("Segoe UI", 11, "italic"), text_color="#1976d2").pack(anchor="w", pady=(0, 2))
    
    def init_profile_tab(self):
        """Initialize the profile tab"""
        tab = self.tabview.tab("Profile")
        
        # Profile card (now scrollable)
        profile_card = ctk.CTkScrollableFrame(tab, fg_color="#f5f7fa", corner_radius=16)
        profile_card.pack(fill="both", expand=True, padx=32, pady=32)
        
        # Profile header
        ctk.CTkLabel(
            profile_card,
            text="Student Profile",
            font=("Segoe UI", 28, "bold"),
            text_color="#1976d2"
        ).pack(pady=24)
        
        # Profile details
        details_frame = ctk.CTkFrame(profile_card, fg_color="transparent")
        details_frame.pack(fill="x", padx=24, pady=12)
        
        # Avatar
        avatar = ctk.CTkLabel(details_frame, text="👤", font=("Segoe UI", 36))
        avatar.pack(anchor="w", pady=8)
        
        # Full name
        ctk.CTkLabel(
            details_frame,
            text="Full Name:",
            font=("Segoe UI", 16, "bold"),
            text_color="#1976d2"
        ).pack(anchor="w", pady=6)
        
        ctk.CTkLabel(
            details_frame,
            text=self.user_data.get('full_name', 'N/A'),
            font=("Segoe UI", 16)
        ).pack(anchor="w", pady=6)
        
        # Email
        ctk.CTkLabel(
            details_frame,
            text="Email:",
            font=("Segoe UI", 16, "bold"),
            text_color="#1976d2"
        ).pack(anchor="w", pady=6)
        
        ctk.CTkLabel(
            details_frame,
            text=self.user_data.get('email', 'N/A'),
            font=("Segoe UI", 16)
        ).pack(anchor="w", pady=6)
        
        # Class
        ctk.CTkLabel(
            details_frame,
            text="Class:",
            font=("Segoe UI", 16, "bold"),
            text_color="#1976d2"
        ).pack(anchor="w", pady=6)
        
        ctk.CTkLabel(
            details_frame,
            text=self.user_data.get('class', 'N/A'),
            font=("Segoe UI", 16)
        ).pack(anchor="w", pady=6)
        
        # Roll number
        ctk.CTkLabel(
            details_frame,
            text="Roll Number:",
            font=("Segoe UI", 16, "bold"),
            text_color="#1976d2"
        ).pack(anchor="w", pady=6)
        roll_number = (
            self.user_data.get('roll_number')
            or self.user_data.get('roll')
            or self.user_data.get('roll_no')
            or 'N/A'
        )
        ctk.CTkLabel(
            details_frame,
            text=str(roll_number),
            font=("Segoe UI", 16)
        ).pack(anchor="w", pady=6)
        
        # Gender
        ctk.CTkLabel(
            details_frame,
            text="Gender:",
            font=("Segoe UI", 16, "bold"),
            text_color="#1976d2"
        ).pack(anchor="w", pady=6)
        
        ctk.CTkLabel(
            details_frame,
            text=self.user_data.get('gender', 'N/A'),
            font=("Segoe UI", 16)
        ).pack(anchor="w", pady=6)
        
        # Date of birth
        ctk.CTkLabel(
            details_frame,
            text="Date of Birth:",
            font=("Segoe UI", 16, "bold"),
            text_color="#1976d2"
        ).pack(anchor="w", pady=6)
        
        ctk.CTkLabel(
            details_frame,
            text=self.user_data.get('dob', 'N/A'),
            font=("Segoe UI", 16)
        ).pack(anchor="w", pady=6)

    def init_feedback_tab(self):
        """Initialize the feedback tab"""
        tab = self.tabview.tab("Feedback")
        # Empty placeholder for now
        pass

    def init_discussion_tab(self):
        """Initialize the discussion tab"""
        discussion_tab = self.tabview.tab("Discussion")
        
        # Create chat frame
        chat_frame = ctk.CTkFrame(discussion_tab)
        chat_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Connection controls
        control_frame = ctk.CTkFrame(chat_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Server address input
        self.server_entry = ctk.CTkEntry(
            control_frame,
            placeholder_text="Enter server IP",
            font=("Helvetica", 12)
        )
        self.server_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.server_entry.insert(0, "localhost")
        
        self.connect_button = ctk.CTkButton(
            control_frame,
            text="Connect",
            command=self.toggle_chat_connection
        )
        self.connect_button.pack(side="right")
        
        # Chat display
        self.chat_display = ctk.CTkTextbox(
            chat_frame,
            wrap="word",
            font=("Helvetica", 12),
            state="disabled"  # Start as disabled
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Message input
        input_frame = ctk.CTkFrame(chat_frame)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.message_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type a message...",
            font=("Helvetica", 12)
        )
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Send",
            command=self.send_chat_message
        )
        self.send_button.pack(side="right")
        
        # Bind Enter key to send message
        self.message_entry.bind("<Return>", lambda e: self.send_chat_message())
        
        # Initialize chat client
        self.chat_client = ChatClient()
        
        # Start message processing thread
        self.message_thread = threading.Thread(target=self.process_chat_messages)
        self.message_thread.daemon = True
        self.message_thread.start()

    def toggle_chat_connection(self):
        """Toggle chat connection"""
        if not self.chat_client.connected:
            server = self.server_entry.get()
            if not server:
                self.add_system_message("Please enter server address")
                return
            
            if self.chat_client.connect(server):
                self.connect_button.configure(text="Disconnect")
                self.add_system_message("Connected to server")
            else:
                self.add_system_message("Failed to connect to server")
        else:
            self.chat_client.disconnect()
            self.connect_button.configure(text="Connect")
            self.add_system_message("Disconnected from server")

    def send_chat_message(self):
        """Send a message to the server"""
        if not self.chat_client.connected:
            self.add_system_message("Not connected to server")
            return
        
        message = self.message_entry.get()
        if not message:
            return
        
        self.message_entry.delete(0, "end")
        if self.chat_client.send_message({
            "sender": self.user_data.get('full_name', 'Student'),
            "content": message
        }):
            self.add_message(self.user_data.get('full_name', 'Student'), message)
        else:
            self.add_system_message("Failed to send message")

    def add_message(self, sender, content):
        """Add a message to the chat display"""
        self.update_chat_display(f"{sender}: {content}")

    def add_system_message(self, content):
        """Add a system message to the chat display"""
        self.update_chat_display(f"System: {content}")

    def update_chat_display(self, message):
        """Update the chat display with a new message"""
        # Enable writing temporarily
        self.chat_display.configure(state="normal")
        
        # Insert new message
        self.chat_display.insert("end", message + "\n")
        
        # Auto-scroll to bottom
        self.chat_display.see("end")
        
        # Immediately disable editing
        self.chat_display.configure(state="disabled")

    def process_chat_messages(self):
        """Process messages from the chat client"""
        while True:
            try:
                message = self.chat_client.message_queue.get()
                if message["type"] == "message":
                    self.add_message(
                        message["data"]["sender"],
                        message["data"]["content"]
                    )
                elif message["type"] == "system":
                    self.add_system_message(message["data"]["content"])
            except:
                pass
            time.sleep(0.1)  # Prevent high CPU usage

    def init_schedule_tab(self):
        tab = self.tabview.tab("Schedule")
        # Main layout: left = class list, right = schedule grid
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        # Class list
        class_list_frame = ctk.CTkScrollableFrame(main_frame, width=200, fg_color="#f5f7fa", corner_radius=12)
        class_list_frame.pack(side="left", fill="y", padx=(0, 16), pady=4, expand=False)
        ctk.CTkLabel(class_list_frame, text="Classes", font=("Segoe UI", 16, "bold"), text_color="#1976d2").pack(pady=(8, 8))
        # Schedule display (now horizontally scrollable)
        schedule_canvas = ctk.CTkFrame(main_frame, fg_color="#fff", corner_radius=12)
        schedule_canvas.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        canvas = tk.Canvas(schedule_canvas, bg="#fff", highlightthickness=0)
        canvas.pack(side="top", fill="both", expand=True)
        h_scroll = tk.Scrollbar(schedule_canvas, orient="horizontal", command=canvas.xview)
        h_scroll.pack(side="bottom", fill="x")
        canvas.configure(xscrollcommand=h_scroll.set)
        # Frame inside canvas for grid
        grid_frame = ctk.CTkFrame(canvas, fg_color="#fff")
        canvas.create_window((0,0), window=grid_frame, anchor="nw")
        def on_grid_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        grid_frame.bind("<Configure>", on_grid_configure)
        # State
        self._schedule_selected_class = None
        self._schedule_class_buttons = {}
        def render_schedule(class_code):
            for w in grid_frame.winfo_children():
                w.destroy()
            ttdata = load_timetable_for_class(class_code)
            periods = ttdata.get("periods_per_day", 6)
            days = ttdata.get("working_days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            schedule = ttdata.get("schedule", {})
            ctk.CTkLabel(grid_frame, text=f"Timetable for {class_code}", font=("Segoe UI", 20, "bold"), text_color="#1976d2").grid(row=0, column=0, columnspan=periods+1, pady=(8, 16))
            ctk.CTkLabel(grid_frame, text="", width=100).grid(row=1, column=0, padx=5, pady=5)
            for col, period in enumerate([f"Period {i+1}" for i in range(periods)]):
                ctk.CTkLabel(grid_frame, text=period, font=("Segoe UI", 13, "bold"), width=100, fg_color="#e3eaf6", corner_radius=8).grid(row=1, column=col+1, padx=2, pady=2)
            for row, day in enumerate(days):
                ctk.CTkLabel(grid_frame, text=day, font=("Segoe UI", 13, "bold"), width=100, fg_color="#e3eaf6", corner_radius=8).grid(row=row+2, column=0, padx=2, pady=2)
                for col in range(periods):
                    val = schedule.get(day, [""]*periods)[col] if day in schedule and len(schedule[day]) > col else "Free"
                    cell_text = val if val else "Free"
                    fg = "#b3e5fc" if cell_text != "Free" else "#fff"
                    if cell_text == "CONFLICT":
                        fg = "#ffb3b3"
                    ctk.CTkLabel(grid_frame, text=cell_text, font=("Segoe UI", 15), width=120, height=36, fg_color=fg, corner_radius=8).grid(row=row+2, column=col+1, padx=2, pady=2)
            ctk.CTkLabel(grid_frame, text="Unused slots are set as 'Free'. Conflicts are marked in red.", font=("Segoe UI", 10, "italic"), text_color="#888").grid(row=len(days)+3, column=0, columnspan=periods+1, sticky="w", padx=10, pady=(4,0))
        def on_class_select(class_code):
            self._schedule_selected_class = class_code
            for c, btn in self._schedule_class_buttons.items():
                btn.configure(fg_color="#e3eafc" if c == class_code else "#f5f7fa")
            render_schedule(class_code)
        # Populate class list
        class_codes = load_class_codes()
        for c in class_codes:
            btn = ctk.CTkButton(class_list_frame, text=c, font=("Segoe UI", 15), width=160, height=40, corner_radius=10, fg_color="#f5f7fa", hover_color="#e3eafc", command=lambda cc=c: on_class_select(cc))
            btn.pack(fill="x", padx=10, pady=6)
            self._schedule_class_buttons[c] = btn
        # Auto-select first class if available
        if class_codes:
            on_class_select(class_codes[0])
