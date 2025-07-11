import os
import sys
import customtkinter as ctk
from PIL import Image, ImageTk
import json
from datetime import datetime
import tkinter.messagebox as mb
from gui.teacher_view import TeacherAttendanceView
from announcements import load_announcements, filter_announcements, PRIORITIES
import socket
import threading
import queue
from Discussion.functions import send_data, receive_data
import time
from gui.schedule_utils import load_class_codes, load_timetable_for_class

def is_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except:
            return False

def get_local_ips():
    """Get all local IP addresses"""
    ips = []
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        ips.append(local_ip)
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip != "127.0.0.1" and ip not in ips:
                ips.append(ip)
    except:
        pass
    return ips

class ChatServer:
    def __init__(self):
        self.host = '0.0.0.0'  # Listen on all interfaces
        self.port = 5001
        self.socket = None
        self.clients = []
        self.running = False
        self.message_queue = queue.Queue()
        self.announcements = []
    
    def start(self):
        """Start the server"""
        try:
            # Check if port is available
            if not is_port_available(self.port):
                return None, f"Error: Port {self.port} is already in use. Please choose a different port."

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            # Get server IP using gethostbyname
            try:
                hostname = socket.gethostname()
                server_ip = socket.gethostbyname(hostname)
            except:
                # Fallback to localhost if hostname resolution fails
                server_ip = "127.0.0.1"
            
            # Start accepting clients
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            return server_ip, None
        except PermissionError:
            return None, "Error: Permission denied. Try running with administrator privileges."
        except OSError as e:
            if "Address already in use" in str(e):
                return None, f"Error: Port {self.port} is already in use. Please choose a different port."
            return None, f"Error starting server: {str(e)}"
        except Exception as e:
            return None, f"Error starting server: {str(e)}"
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        # Disconnect all clients
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        self.clients.clear()
    
    def accept_clients(self):
        """Accept incoming client connections"""
        while self.running:
            try:
                client, address = self.socket.accept()
                self.clients.append(client)
                
                # Start receiving thread for this client
                receive_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client, address)
                )
                receive_thread.daemon = True
                receive_thread.start()
            except:
                break
    
    def handle_client(self, client, address):
        """Handle messages from a client"""
        # Send existing announcements to new client
        for announcement in self.announcements:
            try:
                send_data(client, {
                    "type": "announcement",
                    "data": announcement
                })
            except:
                pass

        while self.running:
            try:
                data = receive_data(client)
                if not data:
                    break
                
                # Process message
                if data["type"] == "message":
                    # Broadcast message to all clients except sender
                    for other_client in self.clients:
                        if other_client != client:
                            try:
                                send_data(other_client, data)
                            except:
                                continue
                    
                    # Add to message queue for server display
                    self.message_queue.put(data)
            except:
                break
        
        # Remove client when disconnected
        if client in self.clients:
            self.clients.remove(client)
            try:
                client.close()
            except:
                pass
    
    def broadcast_message(self, message):
        """Broadcast a message to all clients"""
        for client in self.clients:
            try:
                send_data(client, {
                    "type": "message",
                    "data": message
                })
            except:
                pass
    
    def broadcast_announcement(self, announcement):
        """Broadcast an announcement to all clients"""
        for client in self.clients:
            try:
                send_data(client, {
                    "type": "announcement",
                    "data": announcement
                })
            except:
                pass

class TeacherDashboard(ctk.CTk):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        self.title(f"Teacher Dashboard - {user_data.get('full_name', 'Teacher')}")
        try:
            self.state('zoomed')
        except Exception:
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            self.geometry(f"{width}x{height}")
        self.minsize(800, 600)
        self.configure(fg_color="#F0F4F8")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Create main container (use CTkFrame, not CTkScrollableFrame)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # Create header with user info and clock
        self.create_header()
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_container)
        self.tabview.pack(fill="both", expand=True)
        
        # Add tabs
        self.tabview.add("Dashboard")
        self.tabview.add("Attendance")
        self.tabview.add("Announcements")
        self.tabview.add("Profile")
        self.tabview.add("Discussion")
        self.tabview.add("Schedule")

        self.tabview.set("Dashboard")

        self.init_dashboard_tab()
        self.init_attendance_tab()
        self.init_announcements_tab()
        self.init_profile_tab()
        self.init_discussion_tab()
        self.init_schedule_tab()

        self.update_clock()
    
    def create_header(self):
        """Create header with user info and clock"""
        header = ctk.CTkFrame(self.main_container, height=70, fg_color="#f5f7fa", corner_radius=16)
        header.pack(fill="x", padx=24, pady=16)

        # User info
        user_frame = ctk.CTkFrame(header, fg_color="transparent")
        user_frame.pack(side="left", padx=24)

        # Profile avatar placeholder
        avatar = ctk.CTkLabel(user_frame, text="👨‍🏫", font=("Segoe UI", 28))
        avatar.pack(side="left", padx=(0, 12))

        ctk.CTkLabel(
            user_frame,
            text=f"Welcome, {self.user_data.get('full_name', 'Teacher')}",
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
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.clock_label.configure(text=current_time)
        self.after(1000, self.update_clock)  # Update every second
    
    def logout(self):
        """Handle logout"""
        if mb.askyesno("Logout", "Are you sure you want to logout?"):
            self.destroy()
            # Import and show login window
            from gui.login import LoginApp
            login = LoginApp()
            login.mainloop()
        
    def init_dashboard_tab(self):
        """Initialize the dashboard tab with welcome message and quick stats"""
        tab = self.tabview.tab("Dashboard")
        ctk.CTkLabel(
            tab,
            text="Welcome to Your Dashboard",
            font=("Segoe UI", 28, "bold"),
            text_color="#1976d2"
        ).pack(pady=32)

        stats_container = ctk.CTkFrame(tab, fg_color="#f5f7fa", corner_radius=16)
        stats_container.pack(fill="x", padx=32, pady=16)

        # Classes card
        classes_card = ctk.CTkFrame(stats_container, fg_color="#e3eafc", corner_radius=12)
        classes_card.pack(side="left", expand=True, fill="both", padx=16, pady=16)
        ctk.CTkLabel(
            classes_card,
            text="Assigned Classes",
            font=("Segoe UI", 18, "bold"),
            text_color="#1976d2"
        ).pack(pady=(15, 5))
        ctk.CTkLabel(
            classes_card,
            text=str(len(self.get_teacher_classes())),
            font=("Segoe UI", 24, "bold"),
            text_color="#1976d2"
        ).pack(pady=(0, 15))

        # Subjects card
        subjects_card = ctk.CTkFrame(stats_container, fg_color="#e3eafc", corner_radius=12)
        subjects_card.pack(side="left", expand=True, fill="both", padx=16, pady=16)
        ctk.CTkLabel(
            subjects_card,
            text="Assigned Subjects",
            font=("Segoe UI", 18, "bold"),
            text_color="#2e7d32"
        ).pack(pady=(15, 5))
        ctk.CTkLabel(
            subjects_card,
            text=str(len(self.get_teacher_subjects())),
            font=("Segoe UI", 24, "bold"),
            text_color="#2e7d32"
        ).pack(pady=(0, 15))
    
    def init_attendance_tab(self):
        """Initialize attendance tab with the teacher view"""
        tab = self.tabview.tab("Attendance")
        
        # Create main container
        main_frame = ctk.CTkFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create attendance view
        attendance_view = TeacherAttendanceView(main_frame, self.user_data)
        attendance_view.pack(fill="both", expand=True)
    
    def init_announcements_tab(self):
        """Initialize announcements tab with a modern card-based layout and relevant filtering"""
        tab = self.tabview.tab("Announcements")

        # Main container
        main_frame = ctk.CTkFrame(tab, fg_color="#f5f7fa", corner_radius=16)
        main_frame.pack(fill="both", expand=True, padx=32, pady=24)

        # Section header
        ctk.CTkLabel(
            main_frame,
            text="School Announcements",
            font=("Segoe UI", 24, "bold"),
            text_color="#1976d2"
        ).pack(anchor="w", pady=(8, 16), padx=16)

        # Filter announcements for this teacher
        try:
            from announcements import filter_announcements
            user_role = self.user_data.get('role', 'Teacher')
            announcements = filter_announcements(user_role=user_role, hide_expired=True)
        except Exception:
            announcements = []

        # Scrollable frame for announcements
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=8, pady=8)

        if not announcements:
            ctk.CTkLabel(
                scroll_frame,
                text="No announcements.",
                font=("Segoe UI", 16, "italic"),
                text_color="#888"
            ).pack(pady=40)
            return

        for ann in announcements:
            # Card color by priority
            priority_color = {
                "High": "#dc3545",
                "Medium": "#ffc107",
                "Low": "#28a745"
            }.get(ann.get("priority", "Low"), "#28a745")
            card = ctk.CTkFrame(scroll_frame, fg_color="#fff", corner_radius=14, border_width=1, border_color="#e3eafc")
            card.pack(fill="x", padx=12, pady=10)
            # Priority dot
            ctk.CTkLabel(card, text="●", text_color=priority_color, font=("Segoe UI", 22)).pack(side="left", padx=16, pady=16)
            # Content
            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.pack(side="left", fill="x", expand=True, padx=10, pady=10)
            ctk.CTkLabel(content_frame, text=ann.get("title", ""), font=("Segoe UI", 18, "bold"), text_color="#1976d2").pack(anchor="w")
            ctk.CTkLabel(content_frame, text=ann.get("content", ""), font=("Segoe UI", 15)).pack(anchor="w", pady=4)
            meta = f"Target: {ann.get('target', '-')}  |  Priority: {ann.get('priority', '-')}  |  Expires: {ann.get('expiry_date', '-')[:10]}"
            ctk.CTkLabel(content_frame, text=meta, font=("Segoe UI", 12, "italic"), text_color="#1976d2").pack(anchor="w", pady=(0, 2))
    
    def init_profile_tab(self):
        """Initialize profile tab with user information"""
        tab = self.tabview.tab("Profile")
        
        # Create main container
        main_frame = ctk.CTkFrame(tab, fg_color="#ffffff", corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Profile header
        ctk.CTkLabel(
            main_frame,
            text="Teacher Profile",
            font=("Segoe UI", 24, "bold"),
            text_color="#1976d2"
        ).pack(pady=20)
        
        # Profile details
        details_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=40, pady=20)
        
        # Display user information
        info_items = [
            ("Full Name", self.user_data.get('full_name', 'N/A')),
            ("Email", self.user_data.get('email', 'N/A')),
            ("Department", self.user_data.get('department', 'N/A')),
            ("Qualification", self.user_data.get('qualification', 'N/A')),
            ("Gender", self.user_data.get('gender', 'N/A')),
            ("Date of Birth", self.user_data.get('dob', 'N/A'))
        ]
        
        for label, value in info_items:
            item_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                item_frame,
                text=label,
                font=("Segoe UI", 14, "bold"),
                text_color="#424242"
            ).pack(side="left")
            
            ctk.CTkLabel(
                item_frame,
                text=value,
                font=("Segoe UI", 14),
                text_color="#757575"
            ).pack(side="right")

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
        
        # Server controls
        control_frame = ctk.CTkFrame(chat_frame)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        self.server_status_label = ctk.CTkLabel(
            control_frame,
            text="Server Status: Stopped",
            font=("Helvetica", 12)
        )
        self.server_status_label.pack(side="left", padx=10)
        
        self.start_button = ctk.CTkButton(
            control_frame,
            text="Start Server",
            command=self.toggle_server
        )
        self.start_button.pack(side="right", padx=10)
        
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
        
        # Initialize chat server
        self.chat_server = ChatServer()
        
        # Start message processing thread
        self.message_thread = threading.Thread(target=self.process_chat_messages)
        self.message_thread.daemon = True
        self.message_thread.start()

    def toggle_server(self):
        """Toggle server on/off"""
        if not self.chat_server.running:
            server_ip, error = self.chat_server.start()
            if error:
                self.add_system_message(error)
                return
            
            self.server_status_label.configure(text=f"Server Status: Running ({server_ip})")
            self.start_button.configure(text="Stop Server")
            self.add_system_message(f"Server started on {server_ip}")
        else:
            self.chat_server.stop()
            self.server_status_label.configure(text="Server Status: Stopped")
            self.start_button.configure(text="Start Server")
            self.add_system_message("Server stopped")

    def send_chat_message(self):
        """Send a message to all clients"""
        if not self.chat_server.running:
            self.add_system_message("Server is not running")
            return
        
        message = self.message_entry.get()
        if not message:
            return
        
        self.message_entry.delete(0, "end")
        self.chat_server.broadcast_message({
            "sender": self.user_data.get('full_name', 'Teacher'),
            "content": message
        })
        self.add_message(self.user_data.get('full_name', 'Teacher'), message)

    def add_message(self, sender, content):
        """Add a message to the chat display"""
        self.update_chat_display(f"{sender}: {content}")

    def add_system_message(self, content):
        """Add a system message to the chat display"""
        self.update_chat_display(f"System: {content}")

    def update_chat_display(self, message):
        """Update the chat display with a new message"""

        self.chat_display.configure(state="normal")
        

        self.chat_display.insert("end", message + "\n")
        
        self.chat_display.see("end")
        
        self.chat_display.configure(state="disabled")

    def process_chat_messages(self):
        """Process messages from the chat server"""
        while True:
            try:
                message = self.chat_server.message_queue.get()
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

    def get_teacher_classes(self):
        # Try to load classes assigned to this teacher by email
        try:
            with open(os.path.join("data", "classes.json"), "r", encoding="utf-8") as f:
                classes = json.load(f)
            # If your class objects have a 'teacher_email' field, filter by that
            return [
                c for c in classes
                if c.get('teacher_email') == self.user_data.get('email')
            ]
        except Exception:
            return []

    def get_teacher_subjects(self):
        # Try to load subjects assigned to this teacher by name or email
        try:
            with open(os.path.join("data", "subjects.json"), "r", encoding="utf-8") as f:
                subjects = json.load(f)
            # If your subject objects have a 'teacher' field, filter by that
            return [
                s for s in subjects
                if s.get('teacher') == self.user_data.get('full_name') or s.get('teacher') == self.user_data.get('email')
            ]
        except Exception:
            return []

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
        import tkinter as tk
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
