import customtkinter as ctk
import pyotp
import json
import time
import threading
import socket
import pickle

class TeacherView(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Teacher Attendance System")
        self.geometry("400x300")
        
        # Initialize TOTP
        self.load_config()
        
        # Setup server
        self.setup_server()
        
        # Setup UI
        self.setup_ui()
        
        # Start TOTP update thread
        self.start_totp_thread()

    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.totp_secret = config.get('totp_secret', pyotp.random_base32())
        except FileNotFoundError:
            self.totp_secret = pyotp.random_base32()
            config = {}
        
        self.totp = pyotp.TOTP(self.totp_secret, interval=20)
        
        # Save the secret while preserving other data
        config['totp_secret'] = self.totp_secret
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

    def setup_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', 5000))  # Listen on all interfaces
        self.server_socket.listen(5)
        
        # Start server thread
        self.server_thread = threading.Thread(target=self.handle_clients, daemon=True)
        self.server_thread.start()

    def handle_clients(self):
        while True:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Connection from {address}")
                
                # Send current TOTP code
                current_code = self.totp.now()
                client_socket.send(pickle.dumps(current_code))
                client_socket.close()
            except Exception as e:
                print(f"Error handling client: {e}")

    def setup_ui(self):
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Teacher Attendance System",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=20)

        # TOTP display
        self.totp_frame = ctk.CTkFrame(self.main_frame)
        self.totp_frame.pack(pady=20)
        
        self.totp_label = ctk.CTkLabel(self.totp_frame, text="Current TOTP:")
        self.totp_label.pack()
        
        self.totp_display = ctk.CTkLabel(self.totp_frame, text=self.totp.now(), font=("Arial", 24))
        self.totp_display.pack()
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.totp_frame)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(1.0)

        # IP Address display
        self.ip_label = ctk.CTkLabel(
            self.main_frame,
            text=f"Server IP: {socket.gethostbyname(socket.gethostname())}",
            font=("Arial", 12)
        )
        self.ip_label.pack(pady=10)

        # New TOTP button
        self.new_totp_button = ctk.CTkButton(
            self.main_frame,
            text="Generate New TOTP Secret",
            command=self.generate_new_totp
        )
        self.new_totp_button.pack(pady=10)

    def start_totp_thread(self):
        def update_totp():
            while True:
                current_time = time.time()
                time_left = 20 - (current_time % 20)
                progress = time_left / 20
                
                self.progress_bar.set(progress)
                self.totp_display.configure(text=self.totp.now())
                
                time.sleep(1)
        
        thread = threading.Thread(target=update_totp, daemon=True)
        thread.start()

    def generate_new_totp(self):
        self.totp_secret = pyotp.random_base32()
        self.totp = pyotp.TOTP(self.totp_secret, interval=20)
        
        # Save the new secret
        with open('config.json', 'w') as f:
            json.dump({'totp_secret': self.totp_secret}, f, indent=4)

if __name__ == "__main__":
    app = TeacherView()
    app.mainloop() 