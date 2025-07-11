import os
import sys
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw
import tkinter.messagebox as mb
import json
import re
import hashlib
from datetime import datetime
from gui.components.custom_widgets import TableRow


LOGO_PATH = os.path.join(os.path.dirname(__file__), '../../assets/logo.png')
ROLES = ["Admin", "Teacher", "Student"]

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("School Management System - Login")
        self.geometry("900x800")
        self.minsize(600, 600)
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.main_container = ctk.CTkFrame(self, fg_color="#F0F4F8")
        self.main_container.pack(fill="both", expand=True)

        self.logo_img = self.load_logo()
        logo_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        logo_frame.pack(pady=(50, 30))
        if self.logo_img:
            logo_label = ctk.CTkLabel(logo_frame, image=self.logo_img, text="")
            logo_label.pack()
        else:
            logo_label = ctk.CTkLabel(logo_frame, text="School Logo", font=("Segoe UI", 28, "bold"), text_color="#1976d2")
            logo_label.pack()

        self.card_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.card_container.pack(expand=True, fill="both", padx=50, pady=30)
        
        self.card_frame = ctk.CTkScrollableFrame(
            self.card_container,
            fg_color="#ffffff",
            corner_radius=24,
            border_width=1,
            border_color="#e3eaf6"
        )
        self.card_frame.pack(expand=True, fill="both", padx=25, pady=25)
        
        toggle_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        toggle_frame.pack(pady=(40, 35))
        
        self.signin_btn = ctk.CTkButton(
            toggle_frame,
            text="Sign In",
            width=180,
            height=45,
            corner_radius=22,
            font=("Segoe UI", 15, "bold"),
            command=self.show_signin,
            fg_color="#1976d2",
            hover_color="#1565c0"
        )
        self.signup_btn = ctk.CTkButton(
            toggle_frame,
            text="Sign Up",
            width=180,
            height=45,
            corner_radius=22,
            font=("Segoe UI", 15, "bold"),
            command=self.show_signup,
            fg_color="#e0e0e0",
            text_color="#1976d2",
            hover_color="#bdbdbd"
        )
        self.signin_btn.grid(row=0, column=0, padx=20)
        self.signup_btn.grid(row=0, column=1, padx=20)
        
        self.panel_frame = ctk.CTkFrame(self.card_frame, fg_color="#ffffff", corner_radius=20)
        self.panel_frame.pack(padx=45, pady=(0, 45), fill="both", expand=True)
        
        self.active_panel = None
        self.error_label = None
        self.success_label = None
        self.users = self.load_users()
        self.all_users = self.users.copy()
        self.filtered_users = self.all_users.copy()
        
        self.show_signin()


    def load_logo(self):
        # Load and mask the logo image to a circle
        try:
            img = Image.open(LOGO_PATH).resize((100, 100), Image.LANCZOS)
            mask = Image.new('L', (100, 100), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 100, 100), fill=255)
            img.putalpha(mask)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def create_widgets(self):
        # Logo at the top
        logo_frame = ctk.CTkFrame(self.center_container, fg_color="transparent")
        logo_frame.pack(pady=(0, 20))
        if self.logo_img:
            logo_label = ctk.CTkLabel(logo_frame, image=self.logo_img, text="")
            logo_label.pack()
        else:
            logo_label = ctk.CTkLabel(logo_frame, text="School Logo", font=("Segoe UI", 24, "bold"), text_color="#1976d2")
            logo_label.pack()
        
        # Card shadow (using a frame behind the card)
        self.shadow_frame = ctk.CTkFrame(
            self.center_container,
            fg_color="#dbeafe",
            corner_radius=24,
        )
        self.shadow_frame.pack(expand=True)
        
        # Responsive card: no fixed width/height
        self.card_frame = ctk.CTkFrame(
            self.center_container,
            fg_color="#ffffff",
            corner_radius=20,
            border_width=1,
            border_color="#e3eaf6"
        )
        self.card_frame.pack(expand=True, padx=20, pady=20)
        
        # Toggle buttons for Sign In / Sign Up
        toggle_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        toggle_frame.pack(pady=(32, 32))
        
        self.signin_btn = ctk.CTkButton(
            toggle_frame,
            text="Sign In",
            width=160,
            corner_radius=20,
            font=("Segoe UI", 14, "bold"),
            command=self.show_signin,
            fg_color="#1976d2",
            hover_color="#1565c0"
        )
        self.signup_btn = ctk.CTkButton(
            toggle_frame,
            text="Sign Up",
            width=160,
            corner_radius=20,
            font=("Segoe UI", 14, "bold"),
            command=self.show_signup,
            fg_color="#e0e0e0",
            text_color="#1976d2",
            hover_color="#bdbdbd"
        )
        self.signin_btn.grid(row=0, column=0, padx=16)
        self.signup_btn.grid(row=0, column=1, padx=16)
        
        # Main panel for forms
        self.panel_frame = ctk.CTkFrame(self.card_frame, fg_color="#ffffff", corner_radius=20)
        self.panel_frame.pack(padx=40, pady=(0, 40), fill="both", expand=True)
        
        self.show_signin()

    def clear_panel(self):
        for widget in self.panel_frame.winfo_children():
            try:
                widget.destroy()
            except Exception as e:
                print(f"[DEBUG] Error destroying widget: {e}")
        self.error_label = None
        self.success_label = None

    def show_signin(self):
        self.clear_panel()
        self.signin_btn.configure(fg_color="#1976d2", text_color="white")
        self.signup_btn.configure(fg_color="#e0e0e0", text_color="#1976d2")
        
        # Username label and field with improved styling
        ctk.CTkLabel(self.panel_frame, text="Username", anchor="w", font=("Segoe UI", 15)).pack(pady=(35, 0), padx=25, fill="x")
        user_entry = ctk.CTkEntry(
            self.panel_frame,
            placeholder_text="Enter your username",
            height=45,
            corner_radius=12,
            font=("Segoe UI", 14),
            border_width=2,
            border_color="#e3eaf6"
        )
        user_entry.pack(pady=(2, 12), padx=25, fill="x")
        
        # Password label and field with improved styling
        ctk.CTkLabel(self.panel_frame, text="Password", anchor="w", font=("Segoe UI", 15)).pack(pady=(0, 0), padx=25, fill="x")
        pass_var = ctk.StringVar()
        pass_entry = ctk.CTkEntry(
            self.panel_frame,
            placeholder_text="Enter your password",
            show="*",
            height=45,
            corner_radius=12,
            font=("Segoe UI", 14),
            border_width=2,
            border_color="#e3eaf6",
            textvariable=pass_var
        )
        pass_entry.pack(pady=(2, 12), padx=25, fill="x")
        
        # Show/Hide password toggle with improved styling
        show_pw_var = ctk.BooleanVar(value=False)
        def toggle_pw():
            pass_entry.configure(show="" if show_pw_var.get() else "*")
        show_pw_btn = ctk.CTkCheckBox(
            self.panel_frame,
            text="Show Password",
            variable=show_pw_var,
            command=toggle_pw,
            font=("Segoe UI", 13),
            checkbox_width=20,
            checkbox_height=20
        )
        show_pw_btn.pack(anchor="w", padx=25, pady=(0, 10))
        
        # Role label and dropdown with improved styling
        ctk.CTkLabel(self.panel_frame, text="Role", anchor="w", font=("Segoe UI", 15)).pack(pady=(0, 0), padx=25, fill="x")
        role_menu = ctk.CTkOptionMenu(
            self.panel_frame,
            values=ROLES,
            height=45,
            corner_radius=12,
            font=("Segoe UI", 14),
            button_color="#1976d2",
            button_hover_color="#1565c0"
        )
        role_menu.pack(pady=(2, 12), padx=25, fill="x")
        
        # Login button with improved styling
        login_btn = ctk.CTkButton(
            self.panel_frame,
            text="Login",
            height=48,
            corner_radius=12,
            font=("Segoe UI", 15, "bold"),
            fg_color="#1976d2",
            hover_color="#1565c0",
            command=lambda: self.handle_login(user_entry.get(), pass_var.get(), role_menu.get())
        )
        login_btn.pack(pady=(20, 12), padx=25, fill="x")
        
        # Error label with improved styling
        self.error_label = ctk.CTkLabel(
            self.panel_frame,
            text="",
            text_color="#d32f2f",
            font=("Segoe UI", 13)
        )
        self.error_label.pack(pady=(5, 0))
        
        # Toggle to signup with improved styling
        toggle_link = ctk.CTkLabel(
            self.panel_frame,
            text="Don't have an account? Sign Up",
            font=("Segoe UI", 13, "underline"),
            text_color="#1976d2",
            cursor="hand2"
        )
        toggle_link.pack(pady=(20, 0))
        toggle_link.bind("<Button-1>", lambda e: self.show_signup())
        toggle_link.bind("<Enter>", lambda e: toggle_link.configure(text_color="#1565c0"))
        toggle_link.bind("<Leave>", lambda e: toggle_link.configure(text_color="#1976d2"))
        
        self.panel_frame.after(10, lambda: self.panel_frame.focus_set())

    def show_signup(self):
        self.clear_panel()
        self.signup_btn.configure(fg_color="#1976d2", text_color="white")
        self.signin_btn.configure(fg_color="#e0e0e0", text_color="#1976d2")

        import json
        import re
        import hashlib
        from datetime import datetime
        # Load class codes for students
        try:
            with open(os.path.join(os.path.dirname(__file__), '../data/classes.json'), 'r', encoding='utf-8') as f:
                class_data = json.load(f)
            class_codes = [c['code'] for c in class_data]
        except Exception:
            class_codes = []
        # Load users for username uniqueness
        try:
            with open(os.path.join(os.path.dirname(__file__), '../data/users.json'), 'r', encoding='utf-8') as f:
                users = json.load(f)
        except Exception:
            users = []

        # --- FIELD VARIABLES ---
        full_name_var = ctk.StringVar()
        username_var = ctk.StringVar()
        email_var = ctk.StringVar()
        phone_var = ctk.StringVar()
        password_var = ctk.StringVar()
        confirm_var = ctk.StringVar()
        role_var = ctk.StringVar(value="Student")
        # Teacher fields
        subject_var = ctk.StringVar()
        available_days_vars = {day: ctk.BooleanVar() for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]}
        max_periods_var = ctk.StringVar(value="1")
        # Student fields
        class_code_var = ctk.StringVar()
        roll_var = ctk.StringVar()
        gender_var = ctk.StringVar()
        dob_var = ctk.StringVar()

        # --- ERROR VARIABLES ---
        errors = {k: ctk.StringVar() for k in [
            'full_name', 'username', 'email', 'phone', 'password', 'confirm', 'role',
            'subject', 'available_days', 'max_periods', 'class_code', 'roll', 'gender', 'dob']}

        # --- SCROLLABLE FORM FRAME ---
        scroll_frame = ctk.CTkScrollableFrame(self.panel_frame, fg_color="#f7fafd", corner_radius=18, width=600, height=700)
        scroll_frame.pack(pady=18, padx=36, fill="both", expand=True)
        form = scroll_frame  # Use scroll_frame as the parent for all form widgets
        ctk.CTkLabel(form, text="Sign Up", font=("Arial Rounded MT Bold", 28, "bold"), text_color="#1976d2").pack(pady=(18, 12))

        def labeled_entry(parent, label, var, error_var, **kwargs):
            ctk.CTkLabel(parent, text=label, anchor="w", font=("Arial", 14)).pack(pady=(12, 0), padx=18, fill="x")
            entry = ctk.CTkEntry(parent, textvariable=var, height=44, corner_radius=10, border_width=2, border_color="#e3eaf6", fg_color="#ffffff", font=("Arial", 13), **kwargs)
            entry.pack(pady=(2, 0), padx=18, fill="x")
            err = ctk.CTkLabel(parent, textvariable=error_var, text_color="#d32f2f", font=("Arial", 10), anchor="w")
            err.pack(pady=(0, 0), padx=20, fill="x")
            return entry

        # --- COMMON FIELDS ---
        labeled_entry(form, "Full Name", full_name_var, errors['full_name'])
        labeled_entry(form, "Username", username_var, errors['username'])
        labeled_entry(form, "Email", email_var, errors['email'])
        labeled_entry(form, "Phone (optional)", phone_var, errors['phone'])
        labeled_entry(form, "Password", password_var, errors['password'], show="*")
        labeled_entry(form, "Confirm Password", confirm_var, errors['confirm'], show="*")

        # --- ROLE DROPDOWN ---
        ctk.CTkLabel(form, text="Role", anchor="w", font=("Arial", 14)).pack(pady=(12, 0), padx=18, fill="x")
        role_menu = ctk.CTkOptionMenu(form, values=["Admin", "Teacher", "Student"], variable=role_var, height=44, corner_radius=10, fg_color="#e3eaf6", button_color="#1976d2", button_hover_color="#90caf9", dropdown_fg_color="#f7fafd", dropdown_hover_color="#e3eaf6", dropdown_text_color="#1976d2", text_color="#1976d2", font=("Arial", 13))
        role_menu.pack(pady=(2, 0), padx=18, fill="x")
        ctk.CTkLabel(form, textvariable=errors['role'], text_color="#d32f2f", font=("Arial", 10), anchor="w").pack(pady=(0, 0), padx=20, fill="x")

        # --- DYNAMIC FIELDS FRAME ---
        dynamic_frame = ctk.CTkFrame(form, fg_color="#f7fafd")
        dynamic_frame.pack(pady=(0, 0), padx=0, fill="x")

        def update_dynamic_fields(*_):
            for widget in dynamic_frame.winfo_children():
                try:
                    widget.destroy()
                except Exception as e:
                    print(f"[DEBUG] Error destroying widget: {e}")
            for k in ['subject', 'available_days', 'max_periods', 'class_code', 'roll', 'gender', 'dob']:
                errors[k].set("")
            role = role_var.get()
            if role == "Teacher":
                labeled_entry(dynamic_frame, "Subject Specialization", subject_var, errors['subject'])
                ctk.CTkLabel(dynamic_frame, text="Available Days", anchor="w", font=("Arial", 14)).pack(pady=(12, 0), padx=18, fill="x")
                days_frame = ctk.CTkFrame(dynamic_frame, fg_color="#f7fafd")
                days_frame.pack(pady=(2, 0), padx=18, fill="x")
                for day, var in available_days_vars.items():
                    cb = ctk.CTkCheckBox(days_frame, text=day, variable=var, corner_radius=8, fg_color="#e3eaf6", hover_color="#90caf9", border_color="#e3eaf6", font=("Arial", 12))
                    cb.pack(side="left", padx=6, pady=2)
                ctk.CTkLabel(dynamic_frame, textvariable=errors['available_days'], text_color="#d32f2f", font=("Arial", 10), anchor="w").pack(pady=(0, 0), padx=20, fill="x")
                labeled_entry(dynamic_frame, "Max Periods Per Day", max_periods_var, errors['max_periods'])
            elif role == "Student":
                ctk.CTkLabel(dynamic_frame, text="Class Code", anchor="w", font=("Arial", 14)).pack(pady=(12, 0), padx=18, fill="x")
                class_menu = ctk.CTkOptionMenu(dynamic_frame, values=class_codes, variable=class_code_var, height=44, corner_radius=10, fg_color="#e3eaf6", button_color="#1976d2", button_hover_color="#90caf9", dropdown_fg_color="#f7fafd", dropdown_hover_color="#e3eaf6", dropdown_text_color="#1976d2", text_color="#1976d2", font=("Arial", 13))
                class_menu.pack(pady=(2, 0), padx=18, fill="x")
                ctk.CTkLabel(dynamic_frame, textvariable=errors['class_code'], text_color="#d32f2f", font=("Arial", 10), anchor="w").pack(pady=(0, 0), padx=20, fill="x")
                labeled_entry(dynamic_frame, "Roll Number", roll_var, errors['roll'])
                ctk.CTkLabel(dynamic_frame, text="Gender", anchor="w", font=("Arial", 14)).pack(pady=(12, 0), padx=18, fill="x")
                gender_menu = ctk.CTkOptionMenu(dynamic_frame, values=["Male", "Female", "Other"], variable=gender_var, height=44, corner_radius=10, fg_color="#e3eaf6", button_color="#1976d2", button_hover_color="#90caf9", dropdown_fg_color="#f7fafd", dropdown_hover_color="#e3eaf6", dropdown_text_color="#1976d2", text_color="#1976d2", font=("Arial", 13))
                gender_menu.pack(pady=(2, 0), padx=18, fill="x")
                ctk.CTkLabel(dynamic_frame, textvariable=errors['gender'], text_color="#d32f2f", font=("Arial", 10), anchor="w").pack(pady=(0, 0), padx=20, fill="x")
                labeled_entry(dynamic_frame, "Date of Birth (YYYY-MM-DD)", dob_var, errors['dob'])
        update_dynamic_fields()
        role_var.trace_add('write', update_dynamic_fields)

        # --- BUTTONS ---
        button_frame = ctk.CTkFrame(form, fg_color="#f7fafd")
        button_frame.pack(pady=(32, 24), padx=60, fill="x")

        def validate_fields():
            valid = True
            # Clear previous errors
            for k in errors:
                errors[k].set("")
            # Full name
            if not full_name_var.get().strip():
                errors['full_name'].set("Full name is required.")
                valid = False
            # Username
            uname = username_var.get().strip()
            if not uname:
                errors['username'].set("Username is required.")
                valid = False
            elif any(u['username'] == uname for u in users):
                errors['username'].set("Username already exists.")
                valid = False
            # Email
            email = email_var.get().strip()
            if not email:
                errors['email'].set("Email is required.")
                valid = False
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                errors['email'].set("Invalid email format.")
                valid = False
            elif any(u.get('email', '').lower() == email.lower() for u in users):
                errors['email'].set("Email already registered.")
                valid = False
            # Password
            pw = password_var.get()
            if not pw or len(pw) < 6:
                errors['password'].set("Password must be at least 6 characters.")
                valid = False
            # Confirm password
            if pw != confirm_var.get():
                errors['confirm'].set("Passwords do not match.")
                valid = False
            # Role
            role = role_var.get()
            if not role:
                errors['role'].set("Role is required.")
                valid = False
            # Teacher fields
            if role == "Teacher":
                if not subject_var.get().strip():
                    errors['subject'].set("Subject is required.")
                    valid = False
                if not any(var.get() for var in available_days_vars.values()):
                    errors['available_days'].set("Select at least one day.")
                    valid = False
                try:
                    if int(max_periods_var.get()) < 1:
                        errors['max_periods'].set("Must be at least 1.")
                        valid = False
                except Exception:
                    errors['max_periods'].set("Enter a valid number.")
                    valid = False
            # Student fields
            if role == "Student":
                if not class_code_var.get().strip():
                    errors['class_code'].set("Class code is required.")
                    valid = False
                if not roll_var.get().strip():
                    errors['roll'].set("Roll number is required.")
                    valid = False
                if not gender_var.get().strip():
                    errors['gender'].set("Gender is required.")
                    valid = False
                dob = dob_var.get().strip()
                if not dob:
                    errors['dob'].set("Date of birth is required.")
                    valid = False
                else:
                    import datetime
                    try:
                        datetime.datetime.strptime(dob, "%Y-%m-%d")
                    except Exception:
                        errors['dob'].set("Format: YYYY-MM-DD")
                        valid = False
            return valid

        def on_submit():
            if not validate_fields():
                return
            # Prepare user data
            password_hash = hashlib.sha256(password_var.get().encode('utf-8')).hexdigest()
            user_data = {
                "username": username_var.get().strip(),
                "password_hash": password_hash,
                "role": role_var.get(),
                "full_name": full_name_var.get().strip(),
                "email": email_var.get().strip(),
                "phone": phone_var.get().strip() or None,
                "created_at": datetime.now().isoformat(timespec="seconds")
            }
            if role_var.get() == "Teacher":
                user_data["subject"] = subject_var.get().strip()
                user_data["available_days"] = [day for day, var in available_days_vars.items() if var.get()]
                user_data["max_periods_per_day"] = int(max_periods_var.get())
            if role_var.get() == "Student":
                user_data["class_code"] = class_code_var.get().strip()
                user_data["roll_number"] = roll_var.get().strip()
                user_data["gender"] = gender_var.get().strip()
                if dob_var.get().strip():
                    user_data["date_of_birth"] = dob_var.get().strip()
            # Save to users.json
            try:
                with open(os.path.join(os.path.dirname(__file__), '../data/users.json'), 'r', encoding='utf-8') as f:
                    users = json.load(f)
            except Exception:
                users = []
            users.append(user_data)
            try:
                with open(os.path.join(os.path.dirname(__file__), '../data/users.json'), 'w', encoding='utf-8') as f:
                    json.dump(users, f, indent=4)
            except Exception as e:
                mb.showerror("Error", f"Failed to save: {e}")
                return
            mb.showinfo("Success", "Account created! You can now sign in.")
            self.show_signin()
        submit_btn = ctk.CTkButton(button_frame, text="Sign Up", height=48, corner_radius=14, fg_color="#1976d2", hover_color="#1565c0", font=("Arial Rounded MT Bold", 16), command=on_submit)
        submit_btn.pack(side="left", expand=True, fill="x", padx=(0, 12))
        cancel_btn = ctk.CTkButton(button_frame, text="Back to Login", height=48, corner_radius=14, fg_color="#e0e0e0", text_color="#1976d2", hover_color="#bdbdbd", font=("Arial Rounded MT Bold", 16), command=self.show_signin)
        cancel_btn.pack(side="right", expand=True, fill="x", padx=(12, 0))

    def handle_login(self, username, password, role):
        """Handle login attempt"""
        username = username.strip()
        password = password.strip()
        role = role.strip()
        
        # Load users from users.json
        try:
            users_file = os.path.join(os.path.dirname(__file__), '../data/users.json')
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            users = []
        
        # Hash the password
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        # Check against users
        for user in users:
            # Check if user has password_hash (new format) or password (old format)
            stored_password = user.get('password_hash', user.get('password', ''))
            
            if (
                user.get('username', '').strip().lower() == username.lower() and
                user.get('role', '').strip().lower() == role.lower() and
                stored_password == password_hash
            ):
                try:
                    self.error_label.configure(text="")
                except Exception:
                    pass
                self.open_dashboard(role, user)  # Pass the user data
                try:
                    self.destroy()
                except Exception:
                    pass
                return
        
        # If we get here, login failed
        try:
            self.error_label.configure(text="Invalid username, password, or role.")
        except Exception:
            pass
        print(f"Login failed for user: {username}, role: {role}")  # Debug print

    def open_dashboard(self, role, user_data):
        """Open the appropriate dashboard based on role"""
        self.destroy()  # Destroy login window before opening dashboard
        if role == "Admin":
            from gui.admin_dashboard import AdminDashboard
            AdminDashboard(user_data).mainloop()
        elif role == "Teacher":
            from gui.teacher_dashboard import TeacherDashboard
            TeacherDashboard(user_data).mainloop()
        elif role == "Student":
            from gui.student_dashboard import StudentDashboard
            StudentDashboard(user_data).mainloop()
        else:
            mb.showinfo("Login Success", f"Welcome, {role}!")

    def load_users(self):
        # This method should return a list of users loaded from a file or database
        users_file = os.path.join(os.path.dirname(__file__), '../data/users.json')
        try:
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    return json.load(f)
            else:
                # Create default users if file doesn't exist
                default_users = [
                    {"username": "admin", "password": "admin123", "role": "Admin"},
                    {"username": "teacher1", "password": "teacher123", "role": "Teacher"},
                    {"username": "student1", "password": "student123", "role": "Student"},
                ]
                os.makedirs(os.path.dirname(users_file), exist_ok=True)
                with open(users_file, 'w') as f:
                    json.dump(default_users, f, indent=4)
                return default_users
        except Exception as e:
            print(f"Error loading users: {e}")
            return []

    def draw_user_management(self):
        # This method should draw the user management interface
        pass

    def open_add_user_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add User")
        popup.geometry("350x320")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(corner_radius=16, fg_color="#f7fafd")
        # Entries
        username_entry = ctk.CTkEntry(popup, placeholder_text="Username", width=220)
        username_entry.pack(pady=(30, 10), padx=30)
        password_entry = ctk.CTkEntry(popup, placeholder_text="Password", show="*", width=220)
        password_entry.pack(pady=10, padx=30)
        confirm_entry = ctk.CTkEntry(popup, placeholder_text="Confirm Password", show="*", width=220)
        confirm_entry.pack(pady=10, padx=30)
        role_menu = ctk.CTkOptionMenu(popup, values=["Admin", "Teacher", "Student"], width=220)
        role_menu.set("Admin")
        role_menu.pack(pady=10, padx=30)
        error_label = ctk.CTkLabel(popup, text="", text_color="#d32f2f", font=("Arial", 12))
        error_label.pack(pady=(5, 0))
        def save_user():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            confirm = confirm_entry.get().strip()
            role = role_menu.get().strip()
            if not username or not password or not confirm:
                error_label.configure(text="All fields are required.")
                return
            if password != confirm:
                error_label.configure(text="Passwords do not match.")
                return
            if any(u["username"] == username for u in self.users):
                error_label.configure(text="Username already exists.")
                return
            self.users.append({"username": username, "password": password, "role": role})
            self.save_users()
            self.refresh_user_list()
            popup.destroy()
        save_btn = ctk.CTkButton(popup, text="Save", width=120, height=36, corner_radius=16, fg_color="#1976d2", command=save_user)
        save_btn.pack(pady=(20, 10))
        popup.bind("<Return>", lambda e: save_user())

    def select_user(self, idx):
        self.selected_user_index = idx
        self.refresh_users_list()

    def open_edit_user_modal(self, idx=None):
        if idx is not None:
            self.selected_user_index = idx
        users_list = self.filtered_users if hasattr(self, 'filtered_users') and self.filtered_users is not None else self.users
        if self.selected_user_index is None or self.selected_user_index >= len(users_list):
            self.show_error_popup("No user selected. Please select a user to edit.")
            return
        user = users_list[self.selected_user_index]
        # ... rest of modal logic ...

    def open_delete_user_modal(self, idx=None):
        if idx is not None:
            self.selected_user_index = idx
        users_list = self.filtered_users if hasattr(self, 'filtered_users') and self.filtered_users is not None else self.users
        if self.selected_user_index is None or self.selected_user_index >= len(users_list):
            mb.showerror("Error", "No user selected.")
            return
        u = users_list[self.selected_user_index]
        if mb.askyesno("Delete User", f"Delete user '{u['username']}'?"):
            # Remove from the main users list as well
            self.users.remove(u)
            save_json(USERS_PATH, self.users)
            ToastPopup(self, f"User '{u['username']}' deleted.")
            self.selected_user_index = None
            self.refresh_users_list()

    def refresh_users_list(self):
        self.users = load_json(USERS_PATH)
        filter_text = self.search_bar.var.get().lower().strip()
        for widget in self.users_list_frame.winfo_children():
            try:
                widget.destroy()
            except Exception as e:
                print(f"[DEBUG] Error destroying widget: {e}")
        # Filter users
        filtered_users = []
        for user in self.users:
            email = user.get('email', '')
            full_name = user.get('full_name', '')
            if (not filter_text or
                filter_text in user['username'].lower() or
                filter_text in user['role'].lower() or
                filter_text in email.lower() or
                filter_text in full_name.lower()):
                filtered_users.append(user)
        if not filtered_users:
            ctk.CTkLabel(self.users_list_frame, text="No results found.", text_color="#d32f2f").pack(pady=20)
        else:
            for idx, user in enumerate(filtered_users):
                row = ctk.CTkFrame(self.users_list_frame, fg_color=("#fff" if idx % 2 == 0 else "#f0f4fa"), corner_radius=12)
                row.grid(row=idx, column=0, sticky="ew", padx=10, pady=4)
                ctk.CTkLabel(row, text=user['username'], font=("Segoe UI", 18), anchor="w").grid(row=0, column=0, sticky="w", padx=10)
                ctk.CTkLabel(row, text=user['role'], font=("Segoe UI", 18), anchor="w").grid(row=0, column=1, sticky="w", padx=10)
                edit_btn = ctk.CTkButton(row, text="✎ Edit", font=("Segoe UI", 16), corner_radius=10, command=lambda i=idx: self.open_edit_user_modal(i))
                edit_btn.grid(row=0, column=2, padx=10)
                del_btn = ctk.CTkButton(row, text="🗑 Delete", font=("Segoe UI", 16), corner_radius=10, fg_color="#e57373", command=lambda i=idx: self.open_delete_user_modal(i))
                del_btn.grid(row=0, column=3, padx=10)

    def clear(self):
        self.var.set("")
        if self.on_search:
            self.on_search("")

    def on_user_search(self, event=None):
        q = self.user_search_entry.get().lower()
        if not q:
            self.filtered_users = self.all_users.copy()
        else:
            self.filtered_users = [
                u for u in self.all_users
                if q in u["username"].lower() or q in u["role"].lower()
            ]
        self.render_user_table()

    def clear_user_search(self):
        self.user_search_entry.delete(0, "end")
        self.on_user_search()

    def render_user_table(self):
        for w in self.user_list_frame.winfo_children():
            w.destroy()
        if not self.filtered_users:
            CTkLabel(self.user_list_frame, text="No users found", font=("Segoe UI", 16)).pack(pady=20)
            return
        for u in self.filtered_users:
            row = CTkFrame(self.user_list_frame, corner_radius=10)
            row.pack(fill="x", padx=10, pady=4)
            CTkLabel(row, text=u["username"], width=20, font=("Segoe UI", 16)).pack(side="left")
            CTkLabel(row, text=u["role"], width=10, font=("Segoe UI", 16)).pack(side="left")

    def on_class_search(self, event=None):
        q = self.class_search_entry.get().lower()
        if not q:
            self.filtered_classes = self.all_classes.copy()
        else:
            self.filtered_classes = [
                c for c in self.all_classes
                if q in c["code"].lower() or q in c["name"].lower()
            ]
        self.render_class_table()

    def on_subject_search(self, event=None):
        q = self.subject_search_entry.get().lower()
        if not q:
            self.filtered_subjects = self.all_subjects.copy()
        else:
            self.filtered_subjects = [
                s for s in self.all_subjects
                if q in s["code"].lower() or q in s["name"].lower() or q in s.get("teacher", "").lower()
            ]
        self.render_subject_table()

class AdminDashboard(ctk.CTk):
    USERS_FILE = os.path.join(os.path.dirname(__file__), '../data/users.json')
    DEFAULT_USERS = [
        {"username": "admin", "password": "admin123", "role": "Admin"},
        {"username": "teacher1", "password": "teacher123", "role": "Teacher"},
        {"username": "student1", "password": "student123", "role": "Student"},
    ]

    def __init__(self, user_data):
        super().__init__()
        self.title("Admin Dashboard")
        self.geometry("700x500")
        self.minsize(500, 400)
        self.selected_user_index = None
        self.users = self.load_users()
        # --- Top Welcome Label ---
        welcome_label = ctk.CTkLabel(
            self,
            text="Welcome, Admin!",
            font=("Arial Rounded MT Bold", 28, "bold"),
            text_color="#3a3a3a"
        )
        welcome_label.pack(pady=(30, 10))
        # --- Main Frame for User Management ---
        self.main_frame = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=20)
        self.main_frame.pack(padx=30, pady=10, fill="both", expand=True)
        # --- User List Panel (Left) ---
        self.user_panel = ctk.CTkFrame(self.main_frame, fg_color="#f0f4fa", corner_radius=16)
        self.user_panel.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)
        user_label = ctk.CTkLabel(
            self.user_panel,
            text="User Management",
            font=("Arial Rounded MT Bold", 18, "bold"),
            text_color="#1976d2"
        )
        user_label.pack(pady=(16, 8))
        # Search Entry
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.user_panel, placeholder_text="Search by username or role...", textvariable=self.search_var, width=220)
        self.search_entry.pack(pady=(0, 8), padx=10)
        self.search_var.trace_add("write", lambda *args: self.refresh_user_list(self.search_var.get()))
        # Scrollable user list using CTkScrollableFrame
        self.scroll_frame = ctk.CTkScrollableFrame(self.user_panel, fg_color="#f0f4fa", corner_radius=12)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        # Table header
        header_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#e3eaf6", corner_radius=8)
        header_frame.pack(fill="x", padx=2, pady=(2, 6))
        ctk.CTkLabel(header_frame, text="Username", width=120, anchor="w", font=("Arial", 14, "bold")).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(header_frame, text="Role", width=80, anchor="w", font=("Arial", 14, "bold")).pack(side="left", padx=(20, 0))
        # User list frame inside scrollable frame
        self.user_list_frame = ctk.CTkScrollableFrame(self.scroll_frame, fg_color="#f0f4fa", corner_radius=10)
        self.user_list_frame.pack(fill="both", expand=True)
        # --- Button Panel (Right) ---
        self.button_panel = ctk.CTkFrame(self.main_frame, fg_color="#f6f8fc", corner_radius=16)
        self.button_panel.pack(side="right", fill="y", padx=(10, 20), pady=20)
        # Add User Button
        self.add_btn = ctk.CTkButton(
            self.button_panel,
            text="Add User",
            width=120,
            height=40,
            corner_radius=20,
            fg_color="#1976d2",
            hover_color="#1565c0",
            font=("Arial Rounded MT Bold", 14),
            command=self.open_add_user_popup
        )
        self.add_btn.pack(pady=(40, 16), padx=20)
        # Edit User Button
        self.edit_btn = ctk.CTkButton(
            self.button_panel,
            text="Edit User",
            width=120,
            height=40,
            corner_radius=20,
            fg_color="#43a047",
            hover_color="#388e3c",
            font=("Arial Rounded MT Bold", 14),
            command=self.open_edit_user_popup,
            state="disabled"
        )
        self.edit_btn.pack(pady=16, padx=20)
        # Delete User Button
        self.del_btn = ctk.CTkButton(
            self.button_panel,
            text="Delete User",
            width=120,
            height=40,
            corner_radius=20,
            fg_color="#e53935",
            hover_color="#b71c1c",
            font=("Arial Rounded MT Bold", 14),
            command=self.delete_user,
            state="disabled"
        )
        self.del_btn.pack(pady=16, padx=20)
        # Responsive layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.main_frame.pack_propagate(False)
        self.user_panel.pack_propagate(False)
        self.button_panel.pack_propagate(False)
        # Draw user list immediately
        self.refresh_user_list()

    def load_users(self):
        try:
            with open(self.USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return self.DEFAULT_USERS.copy()

    def save_users(self):
        with open(self.USERS_FILE, 'w') as f:
            json.dump(self.users, f, indent=4)

    def refresh_user_list(self, filter_text=""):
        self.users = self.load_users()
        filter_text = filter_text.lower().strip()
        # Always clear selection when filtering
        self.selected_user_index = None
        # Remove all widgets from the list frame
        for widget in self.user_list_frame.winfo_children():
            try:
                widget.destroy()
            except Exception as e:
                print(f"[DEBUG] Error destroying widget: {e}")
        # Build filtered list
        def is_match(user):
            email = user.get('email', '-')
            full_name = user.get('full_name', '')
            return (
                not filter_text or
                filter_text in user['username'].lower() or
                filter_text in user['role'].lower() or
                filter_text in email.lower() or
                filter_text in full_name.lower()
            )
        self.filtered_users = [user for user in self.users if is_match(user)]
        if not self.filtered_users:
            ctk.CTkLabel(self.user_list_frame, text="No results found.", text_color="#d32f2f").pack(pady=20)
        else:
            for idx, user in enumerate(self.filtered_users):
                row = ctk.CTkFrame(self.user_list_frame, fg_color=("#fff" if idx % 2 == 0 else "#f0f4fa"), corner_radius=12)
                row.grid(row=idx, column=0, sticky="ew", padx=10, pady=4)
                ctk.CTkLabel(row, text=user['username'], font=("Segoe UI", 18), anchor="w").grid(row=0, column=0, sticky="w", padx=10)
                ctk.CTkLabel(row, text=user['role'], font=("Segoe UI", 18), anchor="w").grid(row=0, column=1, sticky="w", padx=10)
                edit_btn = ctk.CTkButton(row, text="✎ Edit", font=("Segoe UI", 16), corner_radius=10, command=lambda i=idx: self.open_edit_user_popup(i))
                edit_btn.grid(row=0, column=2, padx=10)
                del_btn = ctk.CTkButton(row, text="🗑 Delete", font=("Segoe UI", 16), corner_radius=10, fg_color="#e57373", command=lambda i=idx: self.open_delete_user_modal(i))
                del_btn.grid(row=0, column=3, padx=10)
        import datetime
        self.users_last_updated.configure(text=f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def select_user(self, idx):
        self.selected_user_index = idx
        self.refresh_user_list()

    def open_add_user_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add User")
        popup.geometry("350x320")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(corner_radius=16, fg_color="#f7fafd")
        # Entries
        username_entry = ctk.CTkEntry(popup, placeholder_text="Username", width=220)
        username_entry.pack(pady=(30, 10), padx=30)
        password_entry = ctk.CTkEntry(popup, placeholder_text="Password", show="*", width=220)
        password_entry.pack(pady=10, padx=30)
        confirm_entry = ctk.CTkEntry(popup, placeholder_text="Confirm Password", show="*", width=220)
        confirm_entry.pack(pady=10, padx=30)
        role_menu = ctk.CTkOptionMenu(popup, values=["Admin", "Teacher", "Student"], width=220)
        role_menu.set("Admin")
        role_menu.pack(pady=10, padx=30)
        error_label = ctk.CTkLabel(popup, text="", text_color="#d32f2f", font=("Arial", 12))
        error_label.pack(pady=(5, 0))
        def save_user():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            confirm = confirm_entry.get().strip()
            role = role_menu.get().strip()
            if not username or not password or not confirm:
                error_label.configure(text="All fields are required.")
                return
            if password != confirm:
                error_label.configure(text="Passwords do not match.")
                return
            if any(u["username"] == username for u in self.users):
                error_label.configure(text="Username already exists.")
                return
            self.users.append({"username": username, "password": password, "role": role})
            self.save_users()
            self.refresh_user_list()
            popup.destroy()
        save_btn = ctk.CTkButton(popup, text="Save", width=120, height=36, corner_radius=16, fg_color="#1976d2", command=save_user)
        save_btn.pack(pady=(20, 10))
        popup.bind("<Return>", lambda e: save_user())

    def open_edit_user_popup(self, idx):
        # ... (implement edit logic, call self.refresh_user_list() after saving)
        pass

    def delete_user(self):
        # ... (implement delete logic, call self.refresh_user_list() after deleting)
        pass

    def user_search_entry(self):
        self.user_search_entry = ctk.CTkEntry(self.user_panel, placeholder_text="🔍 Search users…", font=("Segoe UI", 18), corner_radius=10)
        self.user_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=10)
        self.user_search_entry.bind("<KeyRelease>", self.on_user_search)

    def user_clear_btn(self):
        self.user_clear_btn = ctk.CTkButton(self.user_panel, text="✖", width=40, command=self.clear_user_search, corner_radius=10)
        self.user_clear_btn.pack(side="left", padx=(0, 10), pady=10)

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()