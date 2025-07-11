import os
import customtkinter as ctk
from tkinter import messagebox as mb
import json
import bcrypt
import random
import sys
import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))
from utils.auto_scheduler import auto_generate_timetable as advanced_auto_generate
from gui.components.custom_widgets import CardFrame, SearchBar, TableRow, ToastPopup, LoadingSpinner, PASTEL_BG, PASTEL_CARD, PASTEL_ACCENT, PASTEL_HOVER, PASTEL_SELECTED, PASTEL_SHADOW, FONT, HEADER_FONT
import file_handler
from utils import timetable_utils
import traceback
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from announcements import load_announcements, add_announcement, edit_announcement, delete_announcement, filter_announcements, PRIORITIES
try:
    from tkcalendar import DateEntry
    HAS_TKCALENDAR = True
except ImportError:
    HAS_TKCALENDAR = False

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
USERS_PATH = os.path.join(DATA_DIR, 'users.json')
CLASSES_PATH = os.path.join(DATA_DIR, 'classes.json')
SUBJECTS_PATH = os.path.join(DATA_DIR, 'subjects.json')

def load_json(filepath):
    try:
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"[DEBUG] Loaded {filepath}: {data}")
            return data
    except Exception as e:
        print(f"[ERROR] Failed to load {filepath}: {e}")
        mb.showerror("Error", f"Failed to load {os.path.basename(filepath)}: {e}", parent=self)
        return []

def save_json(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"[DEBUG] Saved {filepath}: {data}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save {filepath}: {e}")
        mb.showerror("Error", f"Failed to save {os.path.basename(filepath)}: {e}", parent=self)
        return False

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class AdminDashboard(ctk.CTk):
    def __init__(self, admin_username="Admin"):
        super().__init__()
        self.title("Admin Dashboard")
        try:
            self.state('zoomed')
        except Exception:
            width = self.winfo_screenwidth()
            height = self.winfo_screenheight()
            self.geometry(f"{width}x{height}")
        self.minsize(800, 600)
        self.configure(fg_color="#f6f8fc")
        self.admin_username = admin_username
        self.current_tab = "Users"  # Set default tab
        # Load data
        self.all_users = load_json(USERS_PATH)
        self.all_classes = load_json(CLASSES_PATH)
        self.all_subjects = load_json(SUBJECTS_PATH)
        self.filtered_users = list(self.all_users)
        self.filtered_classes = list(self.all_classes)
        self.filtered_subjects = list(self.all_subjects)
        self.selected_user_index = None
        self.selected_class_index = None
        self.selected_subject_index = None
        # Search vars
        self.user_search_var = ctk.StringVar(master=self)
        self.class_search_var = ctk.StringVar(master=self)
        self.subject_search_var = ctk.StringVar(master=self)
        # Timetable state
        self.selected_timetable_class = ctk.StringVar(master=self)
        self.timetable_class_var = ctk.StringVar(master=self)
        # For after_cancel safety
        self._after_ids = set()
        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        self.users_tab = self.tabview.add("Users")
        self.classes_tab = self.tabview.add("Classes")
        self.subjects_tab = self.tabview.add("Subjects")
        self.timetable_tab = self.tabview.add("Timetable")
        self.announcements_tab = self.tabview.add("Announcements")
        # Setup tabs
        self.setup_users_tab()
        self.setup_classes_tab()
        self.setup_subjects_tab()
        self.setup_timetable_tab()
        self.setup_announcements_tab()
        # Global error handler for Tkinter
        self.report_callback_exception = self.global_tk_error_handler
        self._manual_grid_rendering = False
        # --- Persistent search bar widgets for Users tab ---
        # REMOVE the following lines:
        # self.user_search_bar_frame = ctk.CTkFrame(self.users_tab, fg_color="#F8F9FA", corner_radius=16)
        # self.user_search_bar_frame.pack(fill="x", padx=20, pady=(20, 10))
        # self.user_search_var = ctk.StringVar(master=self)
        # self.user_search_entry = ctk.CTkEntry(self.user_search_bar_frame, textvariable=self.user_search_var, placeholder_text="Search users…", font=("Segoe UI", 15), height=40, corner_radius=16)
        # self.user_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
        # self.user_search_entry.bind("<KeyRelease>", self.on_user_search)
        # self.user_search_btn = ctk.CTkButton(self.user_search_bar_frame, text="🔍", width=40, height=40, corner_radius=16, command=self.trigger_user_search)
        # self.user_search_btn.pack(side="left", padx=(0, 10), pady=10)
        # self.user_clear_btn = ctk.CTkButton(self.user_search_bar_frame, text="✖", width=40, height=40, corner_radius=16, command=self.clear_user_search)
        # self.user_clear_btn.pack(side="left", padx=(0, 10), pady=10)
        # self.user_add_btn = ctk.CTkButton(self.user_search_bar_frame, text="Add User", font=("Segoe UI", 15, "bold"), height=40, corner_radius=16, command=self.open_add_user_modal)
        # self.user_add_btn.pack(side="left", padx=(0, 10), pady=10)
        # self.users_table_frame = None

    def global_tk_error_handler(self, exc, val, tb):
        print("[TK ERROR]", exc, val)
        traceback.print_exception(exc, val, tb)
        mb.showerror("Tkinter Error", f"{exc}: {val}")

    # --- USERS TAB ---
    def setup_users_tab(self):
        # Only create search bar and table frame if not already created
        if not hasattr(self, 'user_search_bar_frame') or not self.user_search_bar_frame.winfo_exists():
            self.user_search_bar_frame = ctk.CTkFrame(self.users_tab, fg_color="#F8F9FA", corner_radius=16)
            self.user_search_bar_frame.pack(fill="x", padx=20, pady=(20, 10))
            self.user_search_var = ctk.StringVar(master=self)
            self.user_search_entry = ctk.CTkEntry(self.user_search_bar_frame, textvariable=self.user_search_var, placeholder_text="Search users…", font=("Segoe UI", 15), height=40, corner_radius=16)
            self.user_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
            self.user_search_entry.bind("<KeyRelease>", self.on_user_search)
            self.user_search_btn = ctk.CTkButton(self.user_search_bar_frame, text="🔍", width=40, height=40, corner_radius=16, command=self.trigger_user_search)
            self.user_search_btn.pack(side="left", padx=(0, 10), pady=10)
            self.user_clear_btn = ctk.CTkButton(self.user_search_bar_frame, text="✖", width=40, height=40, corner_radius=16, command=self.clear_user_search)
            self.user_clear_btn.pack(side="left", padx=(0, 10), pady=10)
            self.user_add_btn = ctk.CTkButton(self.user_search_bar_frame, text="Add User", font=("Segoe UI", 15, "bold"), height=40, corner_radius=16, command=self.open_add_user_modal)
            self.user_add_btn.pack(side="left", padx=(0, 10), pady=10)
        if not hasattr(self, 'users_table_frame') or not self.users_table_frame.winfo_exists():
            self.users_table_frame = ctk.CTkFrame(self.users_tab, fg_color="#F8F9FA", corner_radius=16)
            self.users_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.update_users_table()

    def trigger_user_search(self):
        # Called by search button, triggers the same as typing
        self.on_user_search()

    def update_users_table(self):
        try:
            if not hasattr(self, 'users_table_frame') or self.users_table_frame is None or not self.users_table_frame.winfo_exists():
                self.users_table_frame = ctk.CTkFrame(self.users_tab, fg_color="#F8F9FA", corner_radius=16)
                self.users_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            for widget in self.users_table_frame.winfo_children():
                widget.destroy()
            scroll = ctk.CTkScrollableFrame(self.users_table_frame, fg_color="#F8F9FA", corner_radius=16)
            scroll.pack(fill="both", expand=True)
            header = ctk.CTkFrame(scroll, fg_color="#4FC3F7", corner_radius=12)
            header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
            ctk.CTkLabel(header, text="Username", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=0, padx=20, pady=12)
            ctk.CTkLabel(header, text="Role", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=1, padx=20, pady=12)
            ctk.CTkLabel(header, text="Actions", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=2, padx=20, pady=12)
            for idx, user in enumerate(self.filtered_users):
                row_bg = "#fff" if idx % 2 == 0 else "#f0f4fa"
                row = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=12)
                row.grid(row=idx+1, column=0, sticky="ew", padx=0, pady=4)
                ctk.CTkLabel(row, text=user['username'], font=("Segoe UI", 15), anchor="w").grid(row=0, column=0, padx=20, pady=10)
                ctk.CTkLabel(row, text=user['role'], font=("Segoe UI", 15), anchor="w").grid(row=0, column=1, padx=20, pady=10)
                edit_btn = ctk.CTkButton(row, text="✎ Edit", font=("Segoe UI", 15), corner_radius=12, fg_color="#4FC3F7", width=80, height=36, command=lambda i=idx: self.open_edit_user_modal(i))
                edit_btn.grid(row=0, column=2, padx=10)
                del_btn = ctk.CTkButton(row, text="🗑 Delete", font=("Segoe UI", 15), corner_radius=12, fg_color="#e57373", width=80, height=36, command=lambda i=idx: self.confirm_delete_user(self.filtered_users[i]))
                del_btn.grid(row=0, column=3, padx=10)
            # After updating, set focus back to entry
            if hasattr(self, 'user_search_entry') and self.user_search_entry.winfo_exists():
                self.user_search_entry.focus_set()
        except Exception as e:
            print(f"[ERROR] update_users_table: {e}")

    def on_user_search(self, *args):
        query = self.user_search_var.get().strip().lower()
        if not query:
            self.filtered_users = list(self.all_users)
        else:
            def relevance(user):
                uname = user.get('username', '').lower()
                role = user.get('role', '').lower()
                if query == uname or query == role:
                    return 0
                if uname.startswith(query) or role.startswith(query):
                    return 1
                if query in uname or query in role:
                    return 2
                return 3
            filtered = [u for u in self.all_users if query in u.get('username', '').lower() or query in u.get('role', '').lower()]
            self.filtered_users = sorted(filtered, key=relevance)
        self.update_users_table()

    def clear_user_search(self):
        self.user_search_var.set("")
        self.filtered_users = list(self.all_users)
        self.update_users_table()

    # --- MODAL CREATION/DESTRUCTION SAFETY PATCH FOR ADD USER ---
    def open_add_user_modal(self):
        self.close_any_modal()
        if hasattr(self, '_user_modal') and self._user_modal.winfo_exists():
            self._user_modal.lift()
            return
        modal = ctk.CTkToplevel(self)
        self._user_modal = modal
        modal.title("Add User")
        modal.geometry("400x350")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 175
        modal.geometry(f"+{x}+{y}")
        username_entry = ctk.CTkEntry(modal, placeholder_text="Username", height=36, corner_radius=10)
        username_entry.pack(pady=(30, 10), padx=30)
        password_entry = ctk.CTkEntry(modal, placeholder_text="Password", height=36, corner_radius=10, show="*")
        password_entry.pack(pady=10, padx=30)
        role_menu = ctk.CTkOptionMenu(modal, values=["Admin", "Teacher", "Student"], width=220)
        role_menu.set("Teacher")
        role_menu.pack(pady=10, padx=30)
        error_label = ctk.CTkLabel(modal, text="", text_color="#d32f2f", font=("Segoe UI", 12))
        error_label.pack(pady=(5, 0))
        dashboard = self
        def save_and_close():
            print("[DEBUG] Save button pressed in Add User modal")
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            role = role_menu.get().strip()
            if not username or not password or not role:
                error_label.configure(text="All fields are required.")
                print("[DEBUG] Validation failed: missing fields")
                return
            if any(u["username"] == username for u in dashboard.all_users):
                error_label.configure(text="Username already exists.")
                print("[DEBUG] Validation failed: username exists")
                return
            hashed_pw = hash_password(password)
            new_user = {
                "username": username,
                "password": hashed_pw,
                "role": role
            }
            dashboard.all_users.append(new_user)
            dashboard.filtered_users = list(dashboard.all_users)
            dashboard.save_users()
            dashboard.refresh_users_table()
            print("[DEBUG] User added and saved successfully")
            if modal.winfo_exists():
                modal.destroy()
        def cancel():
            if modal.winfo_exists():
                modal.destroy()
        btn_frame = ctk.CTkFrame(modal, fg_color=PASTEL_BG)
        btn_frame.pack(pady=20)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=save_and_close, height=36, corner_radius=10, width=100)
        save_btn.pack(side="left", padx=10)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cancel, height=36, corner_radius=10, width=100, fg_color="#e3f2fd", text_color="#1976d2")
        cancel_btn.pack(side="left", padx=10)
        modal.protocol("WM_DELETE_WINDOW", cancel)

    # --- MODAL CREATION/DESTRUCTION SAFETY PATCH FOR USERS ---
    def open_edit_user_modal(self, idx):
        self.close_any_modal()
        if hasattr(self, '_user_modal') and self._user_modal.winfo_exists():
            self._user_modal.lift()
            return
        modal = ctk.CTkToplevel(self)
        self._user_modal = modal
        modal.title("Edit User")
        modal.geometry("400x350")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 175
        modal.geometry(f"+{x}+{y}")
        user = self.filtered_users[idx]
        username_entry = ctk.CTkEntry(modal, placeholder_text="Username", height=36, corner_radius=10)
        username_entry.insert(0, user.get("username", ""))
        username_entry.pack(pady=(30, 10), padx=30)
        password_entry = ctk.CTkEntry(modal, placeholder_text="Password (leave blank to keep)", height=36, corner_radius=10, show="*")
        password_entry.pack(pady=10, padx=30)
        role_menu = ctk.CTkOptionMenu(modal, values=["Admin", "Teacher", "Student"], width=220)
        role_menu.set(user.get("role", "Teacher"))
        role_menu.pack(pady=10, padx=30)
        error_label = ctk.CTkLabel(modal, text="", text_color="#d32f2f", font=("Segoe UI", 12))
        error_label.pack(pady=(5, 0))
        dashboard = self
        def save_and_close():
            print("[DEBUG] Save button pressed in Edit User modal")
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            role = role_menu.get().strip()
            if not username or not role:
                error_label.configure(text="Username and role are required.")
                print("[DEBUG] Validation failed: missing username or role")
                return
            for u in dashboard.all_users:
                if u["username"] == username and u != user:
                    error_label.configure(text="Username already exists.")
                    print("[DEBUG] Validation failed: username exists")
                    return
            user["username"] = username
            if password:
                user["password"] = hash_password(password)
            user["role"] = role
            dashboard.filtered_users = list(dashboard.all_users)
            dashboard.save_users()
            dashboard.refresh_users_table()
            print("[DEBUG] User edited and saved successfully")
            if modal.winfo_exists():
                modal.destroy()
        def cancel():
            if modal.winfo_exists():
                modal.destroy()
        btn_frame = ctk.CTkFrame(modal, fg_color=PASTEL_BG)
        btn_frame.pack(pady=20)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=save_and_close, height=36, corner_radius=10, width=100)
        save_btn.pack(side="left", padx=10)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cancel, height=36, corner_radius=10, width=100, fg_color="#e3f2fd", text_color="#1976d2")
        cancel_btn.pack(side="left", padx=10)
        modal.protocol("WM_DELETE_WINDOW", cancel)

    # --- DELETE MODAL SAFETY PATCH FOR USERS ---
    def confirm_delete_user(self, user):
        self.close_any_modal()
        modal = ctk.CTkToplevel(self)
        self._user_modal = modal
        modal.title("Confirm Delete")
        modal.geometry("400x200")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 100
        modal.geometry(f"+{x}+{y}")
        def focus_trap(event):
            widgets = [yes_btn, no_btn]
            idx = widgets.index(modal.focus_get()) if modal.focus_get() in widgets else 0
            if event.keysym == "Tab":
                if event.state & 0x1:
                    idx = (idx - 1) % len(widgets)
                else:
                    idx = (idx + 1) % len(widgets)
                widgets[idx].focus_set()
                return "break"
        modal.bind_all("<KeyPress-Tab>", focus_trap)
        ctk.CTkLabel(
            modal,
            text=f"Are you sure you want to delete user '{user['username']}'?",
            font=("Segoe UI", 18, "bold"),
            text_color="#0d47a1",
            wraplength=360,
            anchor="center",
            justify="center"
        ).pack(pady=(36, 18), padx=24)
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(pady=8)
        yes_btn = ctk.CTkButton(btn_frame, text="Yes", width=100, height=44, fg_color="#d32f2f", hover_color="#b71c1c", text_color="#fff", font=("Segoe UI", 16, "bold"), command=lambda: self._delete_user_confirmed(user, modal))
        yes_btn.grid(row=0, column=0, padx=18)
        no_btn = ctk.CTkButton(btn_frame, text="No", width=100, height=44, fg_color="#90caf9", hover_color="#b3e5fc", text_color="#0d47a1", font=("Segoe UI", 16, "bold"), command=modal.destroy)
        no_btn.grid(row=0, column=1, padx=18)
        yes_btn.focus_set()

    def _delete_user_confirmed(self, user, modal):
        if user in self.all_users:
            self.all_users.remove(user)
        if user in self.filtered_users:
            self.filtered_users.remove(user)
            self.save_users()
            self.refresh_users_table()
        modal.destroy()

    # --- CLASSES TAB ---
    def setup_classes_tab(self):
        # Only create search bar and table frame if not already created
        if not hasattr(self, 'class_search_bar_frame') or not self.class_search_bar_frame.winfo_exists():
            self.class_search_bar_frame = ctk.CTkFrame(self.classes_tab, fg_color="#F8F9FA", corner_radius=16)
            self.class_search_bar_frame.pack(fill="x", padx=20, pady=(20, 10))
            self.class_search_var = ctk.StringVar(master=self)
            self.class_search_entry = ctk.CTkEntry(self.class_search_bar_frame, textvariable=self.class_search_var, placeholder_text="Search classes…", font=("Segoe UI", 15), height=40, corner_radius=16)
            self.class_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
            self.class_search_entry.bind("<KeyRelease>", self.on_class_search)
            self.class_search_btn = ctk.CTkButton(self.class_search_bar_frame, text="🔍", width=40, height=40, corner_radius=16, command=self.trigger_class_search)
            self.class_search_btn.pack(side="left", padx=(0, 10), pady=10)
            self.class_clear_btn = ctk.CTkButton(self.class_search_bar_frame, text="✖", width=40, height=40, corner_radius=16, command=self.clear_class_search)
            self.class_clear_btn.pack(side="left", padx=(0, 10), pady=10)
            self.class_add_btn = ctk.CTkButton(self.class_search_bar_frame, text="Add Class", font=("Segoe UI", 15, "bold"), height=40, corner_radius=16, command=self.open_add_class_modal)
            self.class_add_btn.pack(side="left", padx=(0, 10), pady=10)
        if not hasattr(self, 'classes_table_frame') or not self.classes_table_frame.winfo_exists():
            self.classes_table_frame = ctk.CTkFrame(self.classes_tab, fg_color="#F8F9FA", corner_radius=16)
            self.classes_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.update_classes_table()

    def trigger_class_search(self):
        self.on_class_search()

    def update_classes_table(self):
        try:
            if not hasattr(self, 'classes_table_frame') or self.classes_table_frame is None or not self.classes_table_frame.winfo_exists():
                self.classes_table_frame = ctk.CTkFrame(self.classes_tab, fg_color="#F8F9FA", corner_radius=16)
                self.classes_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            for widget in self.classes_table_frame.winfo_children():
                widget.destroy()
            scroll = ctk.CTkScrollableFrame(self.classes_table_frame, fg_color="#F8F9FA", corner_radius=16)
            scroll.pack(fill="both", expand=True)
            header = ctk.CTkFrame(scroll, fg_color="#4FC3F7", corner_radius=12)
            header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
            ctk.CTkLabel(header, text="Class Code", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=0, padx=20, pady=12)
            ctk.CTkLabel(header, text="Class Name", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=1, padx=20, pady=12)
            ctk.CTkLabel(header, text="Actions", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=2, padx=20, pady=12)
            for idx, cls in enumerate(self.filtered_classes):
                row_bg = "#fff" if idx % 2 == 0 else "#f0f4fa"
                row = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=12)
                row.grid(row=idx+1, column=0, sticky="ew", padx=0, pady=4)
                ctk.CTkLabel(row, text=cls['code'], font=("Segoe UI", 15), anchor="w").grid(row=0, column=0, padx=20, pady=10)
                ctk.CTkLabel(row, text=cls['name'], font=("Segoe UI", 15), anchor="w").grid(row=0, column=1, padx=20, pady=10)
                edit_btn = ctk.CTkButton(row, text="✎ Edit", font=("Segoe UI", 15), corner_radius=12, fg_color="#4FC3F7", width=80, height=36, command=lambda i=idx: self.open_edit_class_modal(i))
                edit_btn.grid(row=0, column=2, padx=10)
                del_btn = ctk.CTkButton(row, text="🗑 Delete", font=("Segoe UI", 15), corner_radius=12, fg_color="#e57373", width=80, height=36, command=lambda i=idx: self.confirm_delete_class(self.filtered_classes[i]))
                del_btn.grid(row=0, column=3, padx=10)
            if hasattr(self, 'class_search_entry') and self.class_search_entry.winfo_exists():
                self.class_search_entry.focus_set()
        except Exception as e:
            print(f"[ERROR] update_classes_table: {e}")

    def on_class_search(self, *args):
        query = self.class_search_var.get().strip().lower()
        self.filtered_classes = [c for c in self.all_classes if query in c.get('name', '').lower() or query in c.get('code', '').lower()]
        self.update_classes_table()

    def clear_class_search(self):
        self.class_search_var.set("")
        self.filtered_classes = list(self.all_classes)
        self.update_classes_table()

    # --- MODAL SAFETY, LABELS, AND POLISH FOR CLASSES ---
    def open_add_class_modal(self):
        self.close_any_modal()
        if hasattr(self, '_class_modal') and self._class_modal.winfo_exists():
            self._class_modal.lift()
            return
        modal = ctk.CTkToplevel(self)
        self._class_modal = modal
        modal.title("Add Class")
        modal.geometry("400x300")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 150
        modal.geometry(f"+{x}+{y}")
        # Field labels
        ctk.CTkLabel(modal, text="Class Name", font=FONT, anchor="w").pack(pady=(24, 0), padx=30, anchor="w")
        name_entry = ctk.CTkEntry(modal, placeholder_text="Enter class name", height=36, corner_radius=10)
        name_entry.pack(pady=(2, 10), padx=30, fill="x")
        ctk.CTkLabel(modal, text="Class Code", font=FONT, anchor="w").pack(pady=(0, 0), padx=30, anchor="w")
        code_entry = ctk.CTkEntry(modal, placeholder_text="Enter class code", height=36, corner_radius=10)
        code_entry.pack(pady=(2, 10), padx=30, fill="x")
        error_label = ctk.CTkLabel(modal, text="", text_color="#d32f2f", font=("Segoe UI", 12))
        error_label.pack(pady=(5, 0))
        dashboard = self
        def save_and_close():
            name = name_entry.get().strip()
            code = code_entry.get().strip()
            if not name or not code:
                error_label.configure(text="All fields are required.")
                return
            if any(c["code"] == code for c in dashboard.all_classes):
                error_label.configure(text="Class code already exists.")
                return
            new_class = {"name": name, "code": code}
            dashboard.all_classes.append(new_class)
            dashboard.filtered_classes = list(dashboard.all_classes)
            dashboard.save_classes()
            dashboard.refresh_classes_table()
            if modal.winfo_exists():
                modal.destroy()
        def cancel():
            if modal.winfo_exists():
                modal.destroy()
        btn_frame = ctk.CTkFrame(modal, fg_color=PASTEL_BG)
        btn_frame.pack(pady=20)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=save_and_close, height=36, corner_radius=10, width=100)
        save_btn.pack(side="left", padx=10)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cancel, height=36, corner_radius=10, width=100, fg_color="#e3f2fd", text_color="#1976d2")
        cancel_btn.pack(side="left", padx=10)
        modal.protocol("WM_DELETE_WINDOW", cancel)

    def open_edit_class_modal(self, idx):
        self.close_any_modal()
        if hasattr(self, '_class_modal') and self._class_modal.winfo_exists():
            self._class_modal.lift()
            return
        modal = ctk.CTkToplevel(self)
        self._class_modal = modal
        modal.title("Edit Class")
        modal.geometry("400x300")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 150
        modal.geometry(f"+{x}+{y}")
        class_ = self.filtered_classes[idx]
        name_entry = ctk.CTkEntry(modal, placeholder_text="Class Name", height=36, corner_radius=10)
        name_entry.insert(0, class_.get("name", ""))
        name_entry.pack(pady=(30, 10), padx=30)
        code_entry = ctk.CTkEntry(modal, placeholder_text="Class Code", height=36, corner_radius=10)
        code_entry.insert(0, class_.get("code", ""))
        code_entry.pack(pady=10, padx=30)
        error_label = ctk.CTkLabel(modal, text="", text_color="#d32f2f", font=("Segoe UI", 12))
        error_label.pack(pady=(5, 0))
        dashboard = self
        def save_and_close():
            name = name_entry.get().strip()
            code = code_entry.get().strip()
            if not name or not code:
                error_label.configure(text="All fields are required.")
                return
            for c in dashboard.all_classes:
                if c["code"] == code and c != class_:
                    error_label.configure(text="Class code already exists.")
                    return
            class_["name"] = name
            class_["code"] = code
            dashboard.filtered_classes = list(dashboard.all_classes)
            dashboard.save_classes()
            dashboard.refresh_classes_table()
            if modal.winfo_exists():
                modal.destroy()
        def cancel():
            if modal.winfo_exists():
                modal.destroy()
        btn_frame = ctk.CTkFrame(modal, fg_color=PASTEL_BG)
        btn_frame.pack(pady=20)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=save_and_close, height=36, corner_radius=10, width=100)
        save_btn.pack(side="left", padx=10)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cancel, height=36, corner_radius=10, width=100, fg_color="#e3f2fd", text_color="#1976d2")
        cancel_btn.pack(side="left", padx=10)
        modal.protocol("WM_DELETE_WINDOW", cancel)

    def confirm_delete_class(self, class_obj):
        self.close_any_modal()
        modal = ctk.CTkToplevel(self)
        self._class_modal = modal
        modal.title("Confirm Delete")
        modal.geometry("400x200")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 100
        modal.geometry(f"+{x}+{y}")
        def focus_trap(event):
            widgets = [yes_btn, no_btn]
            idx = widgets.index(modal.focus_get()) if modal.focus_get() in widgets else 0
            if event.keysym == "Tab":
                if event.state & 0x1:
                    idx = (idx - 1) % len(widgets)
                else:
                    idx = (idx + 1) % len(widgets)
                widgets[idx].focus_set()
                return "break"
        modal.bind_all("<KeyPress-Tab>", focus_trap)
        ctk.CTkLabel(
            modal,
            text=f"Are you sure you want to delete class '{class_obj['name']}'?",
            font=("Segoe UI", 18, "bold"),
            text_color="#0d47a1",
            wraplength=360,
            anchor="center",
            justify="center"
        ).pack(pady=(36, 18), padx=24)
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(pady=8)
        yes_btn = ctk.CTkButton(btn_frame, text="Yes", width=100, height=44, fg_color="#d32f2f", hover_color="#b71c1c", text_color="#fff", font=("Segoe UI", 16, "bold"), command=lambda: self._delete_class_confirmed(class_obj, modal))
        yes_btn.grid(row=0, column=0, padx=18)
        no_btn = ctk.CTkButton(btn_frame, text="No", width=100, height=44, fg_color="#90caf9", hover_color="#b3e5fc", text_color="#0d47a1", font=("Segoe UI", 16, "bold"), command=modal.destroy)
        no_btn.grid(row=0, column=1, padx=18)
        yes_btn.focus_set()

    def _delete_class_confirmed(self, class_obj, modal):
        if class_obj in self.all_classes:
            self.all_classes.remove(class_obj)
        if class_obj in self.filtered_classes:
            self.filtered_classes.remove(class_obj)
            self.save_classes()
            self.refresh_classes_table()
        modal.destroy()

    # --- SUBJECTS TAB ---
    def setup_subjects_tab(self):
        # Only create search bar and table frame if not already created
        if not hasattr(self, 'subject_search_bar_frame') or not self.subject_search_bar_frame.winfo_exists():
            self.subject_search_bar_frame = ctk.CTkFrame(self.subjects_tab, fg_color="#F8F9FA", corner_radius=16)
            self.subject_search_bar_frame.pack(fill="x", padx=20, pady=(20, 10))
            self.subject_search_var = ctk.StringVar(master=self)
            self.subject_search_entry = ctk.CTkEntry(self.subject_search_bar_frame, textvariable=self.subject_search_var, placeholder_text="Search subjects…", font=("Segoe UI", 15), height=40, corner_radius=16)
            self.subject_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=10)
            self.subject_search_entry.bind("<KeyRelease>", self.on_subject_search)
            self.subject_search_btn = ctk.CTkButton(self.subject_search_bar_frame, text="🔍", width=40, height=40, corner_radius=16, command=self.trigger_subject_search)
            self.subject_search_btn.pack(side="left", padx=(0, 10), pady=10)
            self.subject_clear_btn = ctk.CTkButton(self.subject_search_bar_frame, text="✖", width=40, height=40, corner_radius=16, command=self.clear_subject_search)
            self.subject_clear_btn.pack(side="left", padx=(0, 10), pady=10)
            self.subject_add_btn = ctk.CTkButton(self.subject_search_bar_frame, text="Add Subject", font=("Segoe UI", 15, "bold"), height=40, corner_radius=16, command=self.open_add_subject_modal)
            self.subject_add_btn.pack(side="left", padx=(0, 10), pady=10)
        if not hasattr(self, 'subjects_table_frame') or not self.subjects_table_frame.winfo_exists():
            self.subjects_table_frame = ctk.CTkFrame(self.subjects_tab, fg_color="#F8F9FA", corner_radius=16)
            self.subjects_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.update_subjects_table()

    def trigger_subject_search(self):
        self.on_subject_search()

    def update_subjects_table(self):
        try:
            if not hasattr(self, 'subjects_table_frame') or self.subjects_table_frame is None or not self.subjects_table_frame.winfo_exists():
                self.subjects_table_frame = ctk.CTkFrame(self.subjects_tab, fg_color="#F8F9FA", corner_radius=16)
                self.subjects_table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
            for widget in self.subjects_table_frame.winfo_children():
                widget.destroy()
            scroll = ctk.CTkScrollableFrame(self.subjects_table_frame, fg_color="#F8F9FA", corner_radius=16)
            scroll.pack(fill="both", expand=True)
            header = ctk.CTkFrame(scroll, fg_color="#4FC3F7", corner_radius=12)
            header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 8))
            ctk.CTkLabel(header, text="Subject Code", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=0, padx=20, pady=12)
            ctk.CTkLabel(header, text="Subject Name", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=1, padx=20, pady=12)
            ctk.CTkLabel(header, text="Teacher", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=2, padx=20, pady=12)
            ctk.CTkLabel(header, text="Actions", font=("Segoe UI", 15, "bold"), text_color="#1976d2").grid(row=0, column=3, padx=20, pady=12)
            for idx, subj in enumerate(self.filtered_subjects):
                row_bg = "#fff" if idx % 2 == 0 else "#f0f4fa"
                row = ctk.CTkFrame(scroll, fg_color=row_bg, corner_radius=12)
                row.grid(row=idx+1, column=0, sticky="ew", padx=0, pady=4)
                ctk.CTkLabel(row, text=subj['code'], font=("Segoe UI", 15), anchor="w").grid(row=0, column=0, padx=20, pady=10)
                ctk.CTkLabel(row, text=subj['name'], font=("Segoe UI", 15), anchor="w").grid(row=0, column=1, padx=20, pady=10)
                ctk.CTkLabel(row, text=subj.get('teacher', '-'), font=("Segoe UI", 15), anchor="w").grid(row=0, column=2, padx=20, pady=10)
                edit_btn = ctk.CTkButton(row, text="✎ Edit", font=("Segoe UI", 15), corner_radius=12, fg_color="#4FC3F7", width=80, height=36, command=lambda i=idx: self.open_edit_subject_modal(i))
                edit_btn.grid(row=0, column=3, padx=10)
                del_btn = ctk.CTkButton(row, text="🗑 Delete", font=("Segoe UI", 15), corner_radius=12, fg_color="#e57373", width=80, height=36, command=lambda i=idx: self.confirm_delete_subject(self.filtered_subjects[i]))
                del_btn.grid(row=0, column=4, padx=10)
            if hasattr(self, 'subject_search_entry') and self.subject_search_entry.winfo_exists():
                self.subject_search_entry.focus_set()
        except Exception as e:
            print(f"[ERROR] update_subjects_table: {e}")

    def on_subject_search(self, *args):
        query = self.subject_search_var.get().strip().lower()
        self.filtered_subjects = [s for s in self.all_subjects if query in s.get('name', '').lower() or query in s.get('code', '').lower() or query in s.get('teacher', '').lower()]
        self.update_subjects_table()

    def clear_subject_search(self):
        self.subject_search_var.set("")
        self.filtered_subjects = list(self.all_subjects)
        self.update_subjects_table()

    # --- MODAL SAFETY & CENTERING FOR SUBJECTS ---
    def open_add_subject_modal(self):
        self.close_any_modal()
        if hasattr(self, '_subject_modal') and self._subject_modal.winfo_exists():
            self._subject_modal.lift()
            return
        modal = ctk.CTkToplevel(self)
        self._subject_modal = modal
        modal.title("Add Subject")
        modal.geometry("400x350")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 175
        modal.geometry(f"+{x}+{y}")
        name_entry = ctk.CTkEntry(modal, placeholder_text="Subject Name", height=36, corner_radius=10)
        name_entry.pack(pady=(30, 10), padx=30)
        code_entry = ctk.CTkEntry(modal, placeholder_text="Subject Code", height=36, corner_radius=10)
        code_entry.pack(pady=10, padx=30)
        # Dropdown for teacher selection
        teacher_names = [u.get("full_name", u["username"]) for u in self.all_users if u.get("role") == "Teacher"]
        teacher_menu = ctk.CTkOptionMenu(modal, values=teacher_names or ["-"], width=220)
        teacher_menu.set(teacher_names[0] if teacher_names else "-")
        teacher_menu.pack(pady=10, padx=30)
        error_label = ctk.CTkLabel(modal, text="", text_color="#d32f2f", font=("Segoe UI", 12))
        error_label.pack(pady=(5, 0))
        dashboard = self
        def save_and_close():
            name = name_entry.get().strip()
            code = code_entry.get().strip()
            teacher = teacher_menu.get().strip()
            if not name or not code or not teacher:
                error_label.configure(text="All fields are required.")
                return
            if any(s["code"] == code for s in self.all_subjects):
                error_label.configure(text="Subject code already exists.")
                return
            new_subject = {"name": name, "code": code, "teacher": teacher}
            self.all_subjects.append(new_subject)
            self.filtered_subjects = list(self.all_subjects)
            self.save_subjects()
            self.refresh_subjects_table()
            if modal.winfo_exists():
                modal.destroy()
        def cancel():
            if modal.winfo_exists():
                modal.destroy()
        btn_frame = ctk.CTkFrame(modal, fg_color=PASTEL_BG)
        btn_frame.pack(pady=20)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=save_and_close, height=36, corner_radius=10, width=100)
        save_btn.pack(side="left", padx=10)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cancel, height=36, corner_radius=10, width=100, fg_color="#e3f2fd", text_color="#1976d2")
        cancel_btn.pack(side="left", padx=10)
        modal.protocol("WM_DELETE_WINDOW", cancel)

    def open_edit_subject_modal(self, idx):
        self.close_any_modal()
        if hasattr(self, '_subject_modal') and self._subject_modal.winfo_exists():
            self._subject_modal.lift()
            return
        modal = ctk.CTkToplevel(self)
        self._subject_modal = modal
        modal.title("Edit Subject")
        modal.geometry("400x350")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 175
        modal.geometry(f"+{x}+{y}")
        subject = self.filtered_subjects[idx]
        name_entry = ctk.CTkEntry(modal, placeholder_text="Subject Name", height=36, corner_radius=10)
        name_entry.insert(0, subject.get("name", ""))
        name_entry.pack(pady=(30, 10), padx=30)
        code_entry = ctk.CTkEntry(modal, placeholder_text="Subject Code", height=36, corner_radius=10)
        code_entry.insert(0, subject.get("code", ""))
        code_entry.pack(pady=10, padx=30)
        teacher_names = [u.get("full_name", u["username"]) for u in self.all_users if u.get("role") == "Teacher"]
        teacher_menu = ctk.CTkOptionMenu(modal, values=teacher_names or ["-"], width=220)
        teacher_menu.set(subject.get("teacher", teacher_names[0] if teacher_names else "-"))
        teacher_menu.pack(pady=10, padx=30)
        error_label = ctk.CTkLabel(modal, text="", text_color="#d32f2f", font=("Segoe UI", 12))
        error_label.pack(pady=(5, 0))
        dashboard = self
        def save_and_close():
            name = name_entry.get().strip()
            code = code_entry.get().strip()
            teacher = teacher_menu.get().strip()
            if not name or not code or not teacher:
                error_label.configure(text="All fields are required.")
                return
            for s in self.all_subjects:
                if s["code"] == code and s != subject:
                    error_label.configure(text="Subject code already exists.")
                    return
            subject["name"] = name
            subject["code"] = code
            subject["teacher"] = teacher
            self.filtered_subjects = list(self.all_subjects)
            self.save_subjects()
            self.refresh_subjects_table()
            if modal.winfo_exists():
                modal.destroy()
        def cancel():
            if modal.winfo_exists():
                modal.destroy()
        btn_frame = ctk.CTkFrame(modal, fg_color=PASTEL_BG)
        btn_frame.pack(pady=20)
        save_btn = ctk.CTkButton(btn_frame, text="Save", command=save_and_close, height=36, corner_radius=10, width=100)
        save_btn.pack(side="left", padx=10)
        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", command=cancel, height=36, corner_radius=10, width=100, fg_color="#e3f2fd", text_color="#1976d2")
        cancel_btn.pack(side="left", padx=10)
        modal.protocol("WM_DELETE_WINDOW", cancel)

    def confirm_delete_subject(self, subject_obj):
        self.close_any_modal()
        modal = ctk.CTkToplevel(self)
        self._subject_modal = modal
        modal.title("Confirm Delete")
        modal.geometry("400x200")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        self.update_idletasks()
        x = self.winfo_rootx() + self.winfo_width() // 2 - 200
        y = self.winfo_rooty() + self.winfo_height() // 2 - 100
        modal.geometry(f"+{x}+{y}")
        def focus_trap(event):
            widgets = [yes_btn, no_btn]
            idx = widgets.index(modal.focus_get()) if modal.focus_get() in widgets else 0
            if event.keysym == "Tab":
                if event.state & 0x1:
                    idx = (idx - 1) % len(widgets)
                else:
                    idx = (idx + 1) % len(widgets)
                widgets[idx].focus_set()
                return "break"
        modal.bind_all("<KeyPress-Tab>", focus_trap)
        ctk.CTkLabel(
            modal,
            text=f"Are you sure you want to delete subject '{subject_obj['name']}'?",
            font=("Segoe UI", 18, "bold"),
            text_color="#0d47a1",
            wraplength=360,
            anchor="center",
            justify="center"
        ).pack(pady=(36, 18), padx=24)
        btn_frame = ctk.CTkFrame(modal, fg_color="transparent")
        btn_frame.pack(pady=8)
        yes_btn = ctk.CTkButton(btn_frame, text="Yes", width=100, height=44, fg_color="#d32f2f", hover_color="#b71c1c", text_color="#fff", font=("Segoe UI", 16, "bold"), command=lambda: self._delete_subject_confirmed(subject_obj, modal))
        yes_btn.grid(row=0, column=0, padx=18)
        no_btn = ctk.CTkButton(btn_frame, text="No", width=100, height=44, fg_color="#90caf9", hover_color="#b3e5fc", text_color="#0d47a1", font=("Segoe UI", 16, "bold"), command=modal.destroy)
        no_btn.grid(row=0, column=1, padx=18)
        yes_btn.focus_set()

    def _delete_subject_confirmed(self, subject_obj, modal):
        if subject_obj in self.all_subjects:
            self.all_subjects.remove(subject_obj)
        if subject_obj in self.filtered_subjects:
            self.filtered_subjects.remove(subject_obj)
            self.save_subjects()
            self.refresh_subjects_table()
        modal.destroy()

    # --- TIMETABLE MODAL/GRID SAFETY PATCH ---
    def setup_timetable_tab(self):
        print("[DEBUG] Entered setup_timetable_tab")
        import customtkinter as ctk
        from tkinter import messagebox as mb
        # --- Main Tabview ---
        for widget in self.timetable_tab.winfo_children():
            widget.destroy()
        tabview = ctk.CTkTabview(self.timetable_tab)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        manual_tab = tabview.add("Manual Timetable")
        auto_tab = tabview.add("Auto-Generated Timetable")
        # --- Helper: Get class codes ---
        def get_class_codes():
            return [c['code'] for c in self.all_classes] if self.all_classes else []
        # --- Helper: Get subjects for class ---
        def get_class_subjects(class_code):
            return [s for s in self.all_subjects]
        def get_subject_names(class_code):
            return [s['name'] for s in get_class_subjects(class_code)]
        def get_teachers_per_subject():
            return {s['name']: [s.get('teacher')] if s.get('teacher') else [] for s in self.all_subjects}
        # --- Days List ---
        ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        period_options = [str(i) for i in range(3, 9)]
        # --- Auto Tab Modern Layout ---
        auto_top_frame = ctk.CTkFrame(auto_tab, fg_color="#f7fafd", corner_radius=16)
        auto_top_frame.pack(fill="x", padx=10, pady=(10, 0))
        # Class selection
        ctk.CTkLabel(auto_top_frame, text="Class:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(10, 4))
        auto_class_var = ctk.StringVar(value=get_class_codes()[0] if get_class_codes() else "", master=self)
        auto_class_menu = ctk.CTkOptionMenu(auto_top_frame, values=get_class_codes(), variable=auto_class_var, width=140, height=36, corner_radius=10)
        auto_class_menu.pack(side="left", padx=(0, 10))
        # Periods per day
        ctk.CTkLabel(auto_top_frame, text="Periods/Day:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(10, 4))
        auto_periods_var = ctk.StringVar(value="6", master=self)
        auto_periods_dropdown = ctk.CTkOptionMenu(auto_top_frame, values=period_options, variable=auto_periods_var, width=80, height=36, corner_radius=10)
        auto_periods_dropdown.pack(side="left", padx=(0, 10))
        # Working days checkboxes
        ctk.CTkLabel(auto_top_frame, text="Working Days:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(10, 4))
        auto_days_vars = {day: ctk.BooleanVar(value=day in ALL_DAYS[:5], master=self) for day in ALL_DAYS}
        for day in ALL_DAYS:
            cb = ctk.CTkCheckBox(auto_top_frame, text=day[:3], variable=auto_days_vars[day], width=40, height=36)
            cb.pack(side="left", padx=(0, 2))
        # --- Subject Loads Horizontal Bar ---
        subject_loads_frame = ctk.CTkFrame(auto_tab, fg_color="#f7fafd", corner_radius=16)
        subject_loads_frame.pack(fill="x", padx=10, pady=(10, 0))
        subject_period_vars = {}
        last_auto_class = {'code': None}
        def render_subject_load_bar():
            for w in subject_loads_frame.winfo_children():
                try:
                    if w.winfo_exists():
                        w.destroy()
                except Exception:
                    pass
            class_code = auto_class_var.get()
            subjects = get_class_subjects(class_code)
            # Always re-initialize subject_period_vars for every config change
            ttdata = self.load_timetable_for_class(class_code)
            schedule = ttdata.get("schedule", {})
            subject_period_count = {s['name']: 0 for s in subjects}
            for day_periods in schedule.values():
                for subj in day_periods:
                    if subj in subject_period_count:
                        subject_period_count[subj] += 1
            subject_period_vars.clear()
            for subj in subjects:
                var = ctk.StringVar(value=str(subject_period_count.get(subj['name'], 0)), master=self)
                subject_period_vars[subj['name']] = var
            last_auto_class['code'] = class_code
            if not subjects:
                ctk.CTkLabel(subject_loads_frame, text="No subjects assigned to this class.", font=("Segoe UI", 13, "italic"), text_color="#d32f2f").pack(padx=10, pady=10)
                return
            bar = ctk.CTkFrame(subject_loads_frame, fg_color="#f7fafd")
            bar.pack(fill="x", padx=10, pady=4)
            for subj in subjects:
                subj_frame = ctk.CTkFrame(bar, fg_color="#e3eaf6", corner_radius=10)
                subj_frame.pack(side="left", padx=8, pady=2)
                ctk.CTkLabel(subj_frame, text=subj['name'], font=("Segoe UI", 13, "bold")).pack(padx=8, pady=(4, 0))
                var = subject_period_vars[subj['name']]
                ctk.CTkEntry(subj_frame, textvariable=var, width=50, height=32, font=("Segoe UI", 13)).pack(padx=8, pady=(2, 0))
                ctk.CTkLabel(subj_frame, text=f"{subj.get('teacher', '-')}", font=("Segoe UI", 10, "italic"), text_color="#1976d2").pack(padx=8, pady=(0, 4))
        # --- Auto tab button functions must be defined before the button bar ---
        def auto_generate_and_save():
            class_code = auto_class_var.get()
            if not class_code:
                mb.showerror("Input Error", "Please select a class.")
                return
            periods = int(auto_periods_var.get())
            days = get_selected_auto_days()
            if not days:
                mb.showerror("Input Error", "Please select at least one working day.")
                return
            # Gather subject period allocations
            subject_periods = {}
            for subj, var in subject_period_vars.items():
                val = var.get()
                if val.isdigit() and int(val) > 0:
                    subject_periods[subj] = int(val)
            if not subject_periods:
                mb.showerror("Input Error", "Please enter at least one subject with periods > 0.")
                return
            total_requested = sum(subject_periods.values())
            total_slots = len(days) * periods
            if total_requested > total_slots:
                mb.showerror("Auto Generation Failed", f"Total subject periods ({total_requested}) exceed available slots ({total_slots}). Reduce subject allocations or increase periods/days.")
                return
            teachers_per_subject = get_teachers_per_subject()
            teacher_map = {subj: teachers[0] if teachers else None for subj, teachers in teachers_per_subject.items()}
            all_class_schedules = {}
            for c in get_class_codes():
                path = self.get_timetable_path(c)
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_class_schedules[c] = data.get('schedule', {})
            try:
                schedule = advanced_auto_generate(
                    class_code,
                    periods,
                    days,
                    subject_periods,
                    teacher_map,
                    all_class_schedules
                )
            except Exception as e:
                mb.showerror("Auto Generation Failed", str(e))
                return
            data = {
                "mode": "auto",
                "working_days": days,
                "periods_per_day": periods,
                "schedule": schedule
            }
            self.save_timetable_for_class(class_code, data)
            render_auto_grid()
            render_subject_load_bar()
            render_manual_grid(preserve_current=True)
        def clear_auto_grid():
            class_code = auto_class_var.get()
            if not class_code:
                mb.showerror("Input Error", "Please select a class to clear.")
                return
            periods = int(auto_periods_var.get())
            days = get_selected_auto_days()
            schedule = {day: ["Free"] * periods for day in days}
            data = {
                "mode": "auto",
                "working_days": days,
                "periods_per_day": periods,
                "schedule": schedule
            }
            self.save_timetable_for_class(class_code, data)
            render_auto_grid()
            render_subject_load_bar()
            render_manual_grid(preserve_current=True)
        def save_auto_grid():
            class_code = auto_class_var.get()
            if not class_code:
                mb.showerror("Input Error", "Please select a class.")
                return
            periods = int(auto_periods_var.get())
            days = get_selected_auto_days()
            ttdata = self.load_timetable_for_class(class_code)
            schedule = ttdata.get("schedule", {})
            data = {
                "mode": "auto",
                "working_days": days,
                "periods_per_day": periods,
                "schedule": schedule
            }
            self.save_timetable_for_class(class_code, data)
            mb.showinfo("Saved", "Timetable saved successfully.")
            render_auto_grid()
            render_manual_grid(preserve_current=True)
        # --- Button Bar (horizontal) for auto tab ---
        auto_btn_frame = ctk.CTkFrame(auto_tab, fg_color="#f7fafd")
        auto_btn_frame.pack(fill="x", pady=(0, 16), padx=10)
        ctk.CTkButton(auto_btn_frame, text="⚡ Generate Automatically", height=40, width=180, corner_radius=12, command=auto_generate_and_save).pack(side="left", padx=12)
        ctk.CTkButton(auto_btn_frame, text="💾 Save Timetable", height=40, width=160, corner_radius=12, command=save_auto_grid).pack(side="left", padx=12)
        ctk.CTkButton(auto_btn_frame, text="🧹 Clear All", height=40, width=120, corner_radius=12, command=clear_auto_grid).pack(side="left", padx=12)
        # --- Copy Auto to Manual Button ---
        def copy_auto_to_manual():
            class_code = auto_class_var.get()
            if not class_code:
                mb.showerror("Input Error", "Please select a class.")
                return
            ttdata = self.load_timetable_for_class(class_code)
            if not ttdata or not ttdata.get("schedule"):
                mb.showerror("Copy Failed", "No auto-generated schedule found for this class.")
                return
            try:
                manual_data = {
                    "mode": "manual",
                    "working_days": ttdata.get("working_days", []),
                    "periods_per_day": ttdata.get("periods_per_day", 6),
                    "schedule": ttdata.get("schedule", {})
                }
                self.save_timetable_for_class(class_code, manual_data)
                print(f"[DEBUG] Copied auto schedule to manual for {class_code}")
                # --- Ensure manual tab switches to the copied class and refreshes grid ---
                manual_class_var.set(class_code)
                mb.showinfo("Copied", "Auto-generated schedule copied to manual timetable. You can now edit it manually.")
                render_manual_grid(preserve_current=False)
                render_auto_grid()
            except Exception as e:
                print(f"[ERROR] Failed to copy auto to manual: {e}")
                mb.showerror("Copy Failed", f"Failed to copy auto schedule to manual: {e}")
        ctk.CTkButton(auto_btn_frame, text="➡️ Copy to Manual", height=40, width=160, corner_radius=12, command=copy_auto_to_manual).pack(side="left", padx=12)
        # --- Auto grid (read-only) ---
        auto_grid_frame = ctk.CTkScrollableFrame(auto_tab, fg_color="#f7fafd", corner_radius=16)
        auto_grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        def get_selected_auto_days():
            return [day for day, var in auto_days_vars.items() if var.get()]
        def render_auto_grid():
            for w in auto_grid_frame.winfo_children():
                try:
                    if w.winfo_exists():
                        w.destroy()
                except Exception:
                    pass
            class_code = auto_class_var.get()
            # Always reload from disk for latest state
            ttdata = self.load_timetable_for_class(class_code)
            periods = int(auto_periods_var.get())
            days = get_selected_auto_days()
            schedule = ttdata.get("schedule", {})
            ctk.CTkLabel(auto_grid_frame, text="", width=100).grid(row=0, column=0, padx=5, pady=5)
            for col, period in enumerate([f"Period {i+1}" for i in range(periods)]):
                ctk.CTkLabel(auto_grid_frame, text=period, font=("Segoe UI", 13, "bold"), width=100, fg_color="#e3eaf6", corner_radius=8).grid(row=0, column=col+1, padx=2, pady=2)
            for row, day in enumerate(days):
                ctk.CTkLabel(auto_grid_frame, text=day, font=("Segoe UI", 13, "bold"), width=100, fg_color="#e3eaf6", corner_radius=8).grid(row=row+1, column=0, padx=2, pady=2)
                for col in range(periods):
                    val = schedule.get(day, [""]*periods)[col] if day in schedule and len(schedule[day]) > col else "Free"
                    cell_text = val if val else "Free"
                    fg = "#b3e5fc" if cell_text != "Free" else "#fff"
                    if cell_text == "CONFLICT":
                        fg = "#ffb3b3"
                    ctk.CTkLabel(auto_grid_frame, text=cell_text, font=("Segoe UI", 15), width=120, height=36, fg_color=fg, corner_radius=8).grid(row=row+1, column=col+1, padx=2, pady=2)
            ctk.CTkLabel(auto_grid_frame, text="Unused slots are set as 'Free'. Conflicts are marked in red.", font=("Segoe UI", 10, "italic"), text_color="#888").grid(row=len(days)+2, column=0, columnspan=periods+1, sticky="w", padx=10, pady=(4,0))
        # --- Traces for auto tab config changes ---
        def auto_tab_update(*_):
            print("[DEBUG] auto_tab_update called")
            class_code = auto_class_var.get()
            if not class_code:
                return
            periods = int(auto_periods_var.get())
            days = get_selected_auto_days()
            ttdata = self.load_timetable_for_class(class_code)
            if ttdata.get('working_days') != days or ttdata.get('periods_per_day') != periods:
                self.update_schedule_on_config_change(class_code, days, periods)
            render_subject_load_bar()
            render_auto_grid()
            render_manual_grid(preserve_current=False)
        auto_class_var.trace_add("write", auto_tab_update)
        auto_periods_var.trace_add("write", auto_tab_update)
        for var in auto_days_vars.values():
            var.trace_add("write", auto_tab_update)
        # --- Manual Tab Modern Layout ---
        manual_class_var = ctk.StringVar(value=get_class_codes()[0] if get_class_codes() else "", master=self)
        manual_periods_var = ctk.StringVar(value="6", master=self)
        manual_days_vars = {day: ctk.BooleanVar(value=day in ALL_DAYS[:5], master=self) for day in ALL_DAYS}
        manual_top_frame = ctk.CTkFrame(manual_tab, fg_color="#f7fafd", corner_radius=16)
        manual_top_frame.pack(fill="x", padx=10, pady=(10, 0))
        ctk.CTkLabel(manual_top_frame, text="Class:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(10, 4))
        manual_class_menu = ctk.CTkOptionMenu(manual_top_frame, values=get_class_codes(), variable=manual_class_var, width=140, height=36, corner_radius=10)
        manual_class_menu.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(manual_top_frame, text="Periods/Day:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(10, 4))
        manual_periods_dropdown = ctk.CTkOptionMenu(manual_top_frame, values=period_options, variable=manual_periods_var, width=80, height=36, corner_radius=10)
        manual_periods_dropdown.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(manual_top_frame, text="Working Days:", font=("Segoe UI", 13, "bold")).pack(side="left", padx=(10, 4))
        for day in ALL_DAYS:
            cb = ctk.CTkCheckBox(manual_top_frame, text=day[:3], variable=manual_days_vars[day], width=40, height=36)
            cb.pack(side="left", padx=(0, 2))
        manual_status_label = ctk.CTkLabel(manual_top_frame, text="", font=("Segoe UI", 12, "italic"), text_color="#888")
        manual_status_label.pack(side="left", padx=(10, 0))
        # --- Manual grid ---
        manual_grid_frame = ctk.CTkScrollableFrame(manual_tab, fg_color="#f7fafd", corner_radius=16)
        manual_grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.manual_entries = {}
        def get_selected_manual_days():
            return [day for day, var in manual_days_vars.items() if var.get()]
        def render_manual_grid(preserve_current=False):
            current_values = {}
            if preserve_current:
                for key, entry in self.manual_entries.items():
                    try:
                        current_values[key] = entry.get()
                    except Exception:
                        pass
            for w in manual_grid_frame.winfo_children():
                try:
                    if w.winfo_exists():
                        w.destroy()
                except Exception:
                    pass
            class_code = manual_class_var.get()
            periods = int(manual_periods_var.get())
            days = get_selected_manual_days()
            ttdata = self.load_timetable_for_class(class_code)
            manual_status_label.configure(text=f"Last updated: {ttdata.get('last_modified','auto')}")
            schedule = ttdata.get("schedule", {})
            ctk.CTkLabel(manual_grid_frame, text="", width=100).grid(row=0, column=0, padx=5, pady=5)
            for col, period in enumerate([f"Period {i+1}" for i in range(periods)]):
                ctk.CTkLabel(manual_grid_frame, text=period, font=("Segoe UI", 13, "bold"), width=100, fg_color="#e3eaf6", corner_radius=8).grid(row=0, column=col+1, padx=2, pady=2)
            self.manual_entries = {}
            subjects = get_subject_names(class_code)
            options = subjects + ["Free"]
            for row, day in enumerate(days):
                ctk.CTkLabel(manual_grid_frame, text=day, font=("Segoe UI", 13, "bold"), width=100, fg_color="#e3eaf6", corner_radius=8).grid(row=row+1, column=0, padx=2, pady=2)
                for col in range(periods):
                    val = schedule.get(day, [""]*periods)[col] if day in schedule and len(schedule[day]) > col else "Free"
                    entry = ctk.CTkOptionMenu(manual_grid_frame, values=options, width=120, height=36, corner_radius=8)
                    if preserve_current and (day, col) in current_values:
                        entry.set(current_values[(day, col)])
                    else:
                        entry.set(val if val else "Free")
                    entry.grid(row=row+1, column=col+1, padx=2, pady=2)
                    self.manual_entries[(day, col)] = entry
            ctk.CTkLabel(manual_grid_frame, text="Set a period to 'Free' for an empty slot. Conflicts are marked in red.", font=("Segoe UI", 10, "italic"), text_color="#888").grid(row=len(days)+2, column=0, columnspan=periods+1, sticky="w", padx=10, pady=(4,0))
        # --- Manual tab button functions must be defined before the button bar ---
        def save_manual_grid():
            class_code = manual_class_var.get()
            if not class_code:
                mb.showerror("Input Error", "Please select a class.")
                return
            periods = int(manual_periods_var.get())
            days = get_selected_manual_days()
            schedule = {day: [self.manual_entries[(day, col)].get() for col in range(periods)] for day in days}
            data = {
                "mode": "manual",
                "working_days": days,
                "periods_per_day": periods,
                "schedule": schedule
            }
            self.save_timetable_for_class(class_code, data)
            print(f"[DEBUG] Manual timetable saved for {class_code}: {data}")
            render_manual_grid(preserve_current=True)
            render_auto_grid()
        def clear_manual_grid():
            class_code = manual_class_var.get()
            if not class_code:
                mb.showerror("Input Error", "Please select a class to clear.")
                return
            periods = int(manual_periods_var.get())
            days = get_selected_manual_days()
            schedule = {day: ["Free"] * periods for day in days}
            data = {
                "mode": "manual",
                "working_days": days,
                "periods_per_day": periods,
                "schedule": schedule
            }
            self.save_timetable_for_class(class_code, data)
            print(f"[DEBUG] Manual timetable cleared for {class_code}")
            render_manual_grid(preserve_current=False)
            render_auto_grid()
        # --- Manual Button Bar (always visible) ---
        manual_btn_frame = ctk.CTkFrame(manual_tab, fg_color="#f7fafd")
        manual_btn_frame.pack(fill="x", pady=(0, 16), padx=10)
        ctk.CTkButton(manual_btn_frame, text="💾 Save Timetable", height=40, width=160, corner_radius=12, command=save_manual_grid).pack(side="left", padx=12)
        ctk.CTkButton(manual_btn_frame, text="🧹 Clear All", height=40, width=120, corner_radius=12, command=clear_manual_grid).pack(side="left", padx=12)
        # --- Manual grid update on config change ---
        def manual_tab_update(*_):
            print("[DEBUG] manual_tab_update called")
            render_manual_grid(preserve_current=True)
            render_subject_load_bar()
            render_auto_grid()
        manual_class_var.trace_add("write", manual_tab_update)
        manual_periods_var.trace_add("write", manual_tab_update)
        for var in manual_days_vars.values():
            var.trace_add("write", manual_tab_update)
        # Initial render
        render_manual_grid(preserve_current=False)

    def get_timetable_path(self, class_code=None):
        # Use per-class timetable files
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        tt_dir = os.path.join(data_dir, 'timetables')
        if not os.path.exists(tt_dir):
            os.makedirs(tt_dir, exist_ok=True)
        if class_code:
            return os.path.join(tt_dir, f"{class_code}.json")
        return tt_dir

    def load_timetable_for_class(self, class_code):
        path = self.get_timetable_path(class_code)
        if not os.path.exists(path):
            return {
                "mode": "auto",
                "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "periods_per_day": 6,
                "schedule": {day: ["Free"]*6 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]},
                "last_modified": None
            }
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load timetable for {class_code}: {e}")
            return {
                "mode": "auto",
                "working_days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "periods_per_day": 6,
                "schedule": {day: ["Free"]*6 for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]},
                "last_modified": None
            }

    def save_timetable_for_class(self, class_code, data):
        import datetime
        path = self.get_timetable_path(class_code)
        # Add last_modified timestamp
        data['last_modified'] = datetime.datetime.now().isoformat()
        try:
            # If file exists, merge with previous state for non-destructive update
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    prev = json.load(f)
                # Only update changed fields, preserve manual/auto distinction
                for k in ['mode', 'working_days', 'periods_per_day', 'schedule']:
                    prev[k] = data.get(k, prev.get(k))
                prev['last_modified'] = data['last_modified']
                data = prev
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save timetable for {class_code}: {e}")
            return False

    def save_current_timetable(self):
        class_code = self.selected_timetable_class.get() if hasattr(self, 'selected_timetable_class') else None
        if not class_code:
            mb.showerror("Error", "No class selected.")
            return
        timetable = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        for day in days:
            timetable[day] = [self.timetable_entries[(day, col)].get() for col in range(8)]
        if self.save_timetable_for_class(class_code, timetable):
            mb.showinfo("Success", f"Timetable for {class_code} saved.")

    def generate_timetable(self):
        mb.showinfo("Info", "Auto-generation not implemented yet.")

    def setup_announcements_tab(self):
        for widget in self.announcements_tab.winfo_children():
            widget.destroy()
        # --- Top Bar: Horizontal Controls ---
        top_frame = ctk.CTkFrame(self.announcements_tab, fg_color=PASTEL_BG, corner_radius=16)
        top_frame.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(top_frame, text="Title", font=FONT).pack(side="left", padx=(10, 4))
        title_var = ctk.StringVar()
        ctk.CTkEntry(top_frame, textvariable=title_var, placeholder_text="Title", font=FONT, width=140, height=36, corner_radius=10).pack(side="left", padx=4)
        ctk.CTkLabel(top_frame, text="Content", font=FONT).pack(side="left", padx=(10, 4))
        content_var = ctk.StringVar()
        ctk.CTkEntry(top_frame, textvariable=content_var, placeholder_text="Content", font=FONT, width=200, height=36, corner_radius=10).pack(side="left", padx=4)
        ctk.CTkLabel(top_frame, text="Target", font=FONT).pack(side="left", padx=(10, 4))
        target_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(top_frame, values=["All", "Teacher", "Student"] + [f"Class:{c['code']}" for c in self.all_classes], variable=target_var, width=110, height=36, corner_radius=10, font=FONT).pack(side="left", padx=4)
        ctk.CTkLabel(top_frame, text="Priority", font=FONT).pack(side="left", padx=(10, 4))
        priority_var = ctk.StringVar(value="Medium")
        ctk.CTkOptionMenu(top_frame, values=PRIORITIES, variable=priority_var, width=90, height=36, corner_radius=10, font=FONT).pack(side="left", padx=4)
        ctk.CTkLabel(top_frame, text="Expiry", font=FONT).pack(side="left", padx=(10, 4))
        expiry_var = ctk.StringVar()
        if HAS_TKCALENDAR:
            expiry_picker = DateEntry(top_frame, textvariable=expiry_var, width=12, date_pattern='y-mm-dd')
            expiry_picker.pack(side="left", padx=4)
        else:
            ctk.CTkEntry(top_frame, textvariable=expiry_var, placeholder_text="YYYY-MM-DD", font=FONT, width=110, height=36, corner_radius=10).pack(side="left", padx=4)
        def on_add():
            title = title_var.get().strip()
            content = content_var.get().strip()
            target = target_var.get().strip()
            priority = priority_var.get().strip()
            expiry = expiry_var.get().strip() or None
            if not title or not content:
                mb.showerror("Input Error", "Title and content are required.")
                return
            if expiry:
                try:
                    expiry_iso = expiry if 'T' in expiry else expiry + 'T23:59:59'
                    import datetime
                    datetime.datetime.fromisoformat(expiry_iso)
                except Exception:
                    mb.showerror("Input Error", "Expiry date must be YYYY-MM-DD or ISO format.")
                    return
            else:
                expiry_iso = None
            add_announcement(title, content, target, self.admin_username, priority, expiry_iso)
            self.setup_announcements_tab()
        ctk.CTkButton(top_frame, text="Add", command=on_add, width=70, height=36, corner_radius=10, font=FONT, fg_color=PASTEL_ACCENT, hover_color=PASTEL_HOVER).pack(side="left", padx=(10, 4))
        # --- Announcements List ---
        list_frame = ctk.CTkScrollableFrame(self.announcements_tab, fg_color=PASTEL_BG, corner_radius=16)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        anns = load_announcements()
        if not anns:
            ctk.CTkLabel(list_frame, text="No announcements yet.", font=("Segoe UI", 14, "italic"), text_color="#888").pack(pady=30)
            return
        import datetime
        now = datetime.datetime.now().isoformat()
        for ann in sorted(anns, key=lambda a: (PRIORITIES.index(a.get('priority', 'Medium')) if a.get('priority', 'Medium') in PRIORITIES else 1, a.get('created_at', '')), reverse=False):
            expired = ann.get('expiry_date') and ann['expiry_date'] < now
            fg = PASTEL_CARD if not expired else PASTEL_SHADOW
            card = ctk.CTkFrame(list_frame, fg_color=fg, corner_radius=12)
            card.pack(fill="x", padx=8, pady=8)
            ctk.CTkLabel(card, text=ann['title'], font=HEADER_FONT, anchor="w").pack(anchor="w", padx=10, pady=(6, 0))
            ctk.CTkLabel(card, text=ann['content'], font=FONT, anchor="w").pack(anchor="w", padx=10, pady=(0, 6))
            meta = f"Target: {ann['target']} | Priority: {ann['priority']} | By: {ann['created_by']} | Expires: {ann.get('expiry_date', '-')[:10]}"
            ctk.CTkLabel(card, text=meta, font=("Segoe UI", 10, "italic"), text_color="#1976d2").pack(anchor="w", padx=10, pady=(0, 6))
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(anchor="e", padx=10, pady=(0, 6))
            def make_edit(ann=ann):
                def edit():
                    self.open_edit_announcement_modal(ann)
                return edit
            def make_delete(ann=ann):
                def delete():
                    if mb.askyesno("Delete", f"Delete announcement '{ann['title']}'?"):
                        delete_announcement(ann['id'])
                        self.setup_announcements_tab()
                return delete
            ctk.CTkButton(btn_frame, text="✎ Edit", width=60, height=32, corner_radius=8, font=FONT, fg_color=PASTEL_ACCENT, hover_color=PASTEL_HOVER, command=make_edit(ann)).pack(side="left", padx=4)
            ctk.CTkButton(btn_frame, text="🗑 Delete", width=60, height=32, corner_radius=8, font=FONT, fg_color="#e57373", hover_color="#ef9a9a", command=make_delete(ann)).pack(side="left", padx=4)
    def open_edit_announcement_modal(self, ann):
        import datetime
        modal = ctk.CTkToplevel(self)
        modal.title("Edit Announcement")
        modal.geometry("420x340")
        modal.grab_set()
        modal.transient(self)
        modal.configure(fg_color=PASTEL_BG)
        title_var = ctk.StringVar(value=ann['title'])
        content_var = ctk.StringVar(value=ann['content'])
        target_var = ctk.StringVar(value=ann['target'])
        priority_var = ctk.StringVar(value=ann['priority'])
        expiry_var = ctk.StringVar(value=ann.get('expiry_date', '')[:10])
        frame = ctk.CTkFrame(modal, fg_color=PASTEL_BG)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="Title", font=FONT, anchor="w").pack(anchor="w")
        ctk.CTkEntry(frame, textvariable=title_var, font=FONT, width=220).pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text="Content", font=FONT, anchor="w").pack(anchor="w")
        ctk.CTkEntry(frame, textvariable=content_var, font=FONT, width=220).pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text="Target", font=FONT, anchor="w").pack(anchor="w")
        ctk.CTkOptionMenu(frame, values=["All", "Teacher", "Student"] + [f"Class:{c['code']}" for c in self.all_classes], variable=target_var, width=120, font=FONT).pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text="Priority", font=FONT, anchor="w").pack(anchor="w")
        ctk.CTkOptionMenu(frame, values=PRIORITIES, variable=priority_var, width=90, font=FONT).pack(fill="x", pady=4)
        ctk.CTkLabel(frame, text="Expiry Date", font=FONT, anchor="w").pack(anchor="w")
        if HAS_TKCALENDAR:
            expiry_picker = DateEntry(frame, textvariable=expiry_var, width=12, date_pattern='y-mm-dd')
            expiry_picker.pack(fill="x", pady=4)
        else:
            ctk.CTkEntry(frame, textvariable=expiry_var, placeholder_text="YYYY-MM-DD", font=FONT, width=120).pack(fill="x", pady=4)
        error_label = ctk.CTkLabel(frame, text="", text_color="#d32f2f", font=("Segoe UI", 12))
        error_label.pack(pady=(5, 0))
        def save_and_close():
            title = title_var.get().strip()
            content = content_var.get().strip()
            target = target_var.get().strip()
            priority = priority_var.get().strip()
            expiry = expiry_var.get().strip() or None
            if not title or not content:
                error_label.configure(text="Title and content are required.")
                return
            if expiry:
                try:
                    expiry_iso = expiry if 'T' in expiry else expiry + 'T23:59:59'
                    datetime.datetime.fromisoformat(expiry_iso)
                except Exception:
                    error_label.configure(text="Expiry date must be YYYY-MM-DD or ISO format.")
                    return
            else:
                expiry_iso = None
            edit_announcement(ann['id'], title=title, content=content, target=target, priority=priority, expiry_date=expiry_iso)
            self.setup_announcements_tab()
            if modal.winfo_exists():
                modal.destroy()
        btn_frame = ctk.CTkFrame(frame, fg_color=PASTEL_BG)
        btn_frame.pack(pady=16)
        ctk.CTkButton(btn_frame, text="Save", command=save_and_close, height=36, corner_radius=10, width=100, font=FONT, fg_color=PASTEL_ACCENT, hover_color=PASTEL_HOVER).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=modal.destroy, height=36, corner_radius=10, width=100, font=FONT, fg_color="#e3f2fd", text_color="#1976d2").pack(side="left", padx=10)
        modal.protocol("WM_DELETE_WINDOW", modal.destroy)

    # --- DATA SAVE/REFRESH PATCHES ---
    def save_users(self):
        save_json(USERS_PATH, self.all_users)

    def refresh_users_table(self):
        self.setup_users_tab()

    def save_classes(self):
        save_json(CLASSES_PATH, self.all_classes)

    def refresh_classes_table(self):
        self.setup_classes_tab()

    def save_subjects(self):
        save_json(SUBJECTS_PATH, self.all_subjects)

    def refresh_subjects_table(self):
        self.setup_subjects_tab()

    # --- GLOBAL MODAL MANAGER ---
    def close_any_modal(self):
        for modal_attr in ['_user_modal', '_class_modal', '_subject_modal']:
            modal = getattr(self, modal_attr, None)
            if modal and modal.winfo_exists():
                modal.destroy()
                setattr(self, modal_attr, None)

    def on_closing(self):
        # Cancel all after-calls and destroy safely
        if hasattr(self, '_after_ids'):
            for aid in list(self._after_ids):
                try:
                    self.after_cancel(aid)
                except Exception as e:
                    print(f"[DEBUG] after_cancel failed for {aid}: {e}")
                finally:
                    self._after_ids.discard(aid)
        self.destroy()

    def safe_update_widget(self, widget, method, *args, **kwargs):
        try:
            if widget.winfo_exists():
                getattr(widget, method)(*args, **kwargs)
        except Exception:
            pass

    def update_schedule_on_config_change(self, class_code, new_days, new_periods):
        # Load current timetable
        ttdata = self.load_timetable_for_class(class_code)
        old_days = ttdata.get('working_days', [])
        old_periods = ttdata.get('periods_per_day', 0)
        schedule = ttdata.get('schedule', {})
        # Build new schedule, preserving as much as possible
        new_schedule = {}
        for day in new_days:
            if day in schedule:
                # Copy existing periods, pad or trim as needed
                periods = schedule[day][:new_periods] + ["Free"] * max(0, new_periods - len(schedule[day]))
                new_schedule[day] = periods[:new_periods]
            else:
                new_schedule[day] = ["Free"] * new_periods
        # Save updated structure (do not change mode)
        data = dict(ttdata)
        data['working_days'] = new_days
        data['periods_per_day'] = new_periods
        data['schedule'] = new_schedule
        self.save_timetable_for_class(class_code, data)

# To launch after login:
# from gui.admin_dashboard import AdminDashboard
# AdminDashboard(admin_username).mainloop()

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PERIODS = [f"Period {i+1}" for i in range(6)]  # 6 periods per day

if __name__ == "__main__":
    AdminDashboard().mainloop()
