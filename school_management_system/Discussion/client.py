import socket
import threading
import queue
import customtkinter as ctk
from functions import send_data, receive_data

class Client:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.message_queue = queue.Queue()
        self.connected = False
        self.username = None
        self.announcements = []  # Store announcements
    
    def connect(self, username):
        """Connect to the server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.username = username
            self.connected = True
            
            # Start receiving thread
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except:
            return False
    
    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            self.socket.close()
    
    def receive_messages(self):
        """Receive messages from the server"""
        while self.connected:
            try:
                data = receive_data(self.socket)
                if not data:
                    break
                
                if data["type"] == "announcement":
                    self.announcements.append(data["data"])
                
                self.message_queue.put(data)
            except:
                break
        
        self.connected = False
        self.message_queue.put({
            "type": "system",
            "data": {
                "content": "Disconnected from server"
            }
        })
    
    def send_message(self, content):
        """Send a message to the server"""
        if not self.connected:
            return False
        
        try:
            send_data(self.socket, {
                "type": "message",
                "data": {
                    "sender": self.username,
                    "content": content
                }
            })
            return True
        except:
            return False

class ClientGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("LAN Messenger - Client")
        self.geometry("800x600")
        
        # Initialize client
        self.client = Client()
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Create tabs
        self.chat_tab = self.tabview.add("Chat")
        
        # Connection frame
        self.connection_frame = ctk.CTkFrame(self.chat_tab)
        self.connection_frame.pack(pady=10, padx=20, fill="x")
        
        self.host_entry = ctk.CTkEntry(
            self.connection_frame,
            placeholder_text="Host",
            width=150
        )
        self.host_entry.pack(side="left", padx=5)
        self.host_entry.insert(0, "localhost")
        
        self.port_entry = ctk.CTkEntry(
            self.connection_frame,
            placeholder_text="Port",
            width=100
        )
        self.port_entry.pack(side="left", padx=5)
        self.port_entry.insert(0, "5000")
        
        self.username_entry = ctk.CTkEntry(
            self.connection_frame,
            placeholder_text="Username",
            width=150
        )
        self.username_entry.pack(side="left", padx=5)
        
        self.connect_button = ctk.CTkButton(
            self.connection_frame,
            text="Connect",
            command=self.toggle_connection
        )
        self.connect_button.pack(side="right", padx=5)
        
        # Chat area
        self.chat_frame = ctk.CTkFrame(self.chat_tab)
        self.chat_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.chat_text = ctk.CTkTextbox(
            self.chat_frame,
            wrap="word",
            font=("Helvetica", 12)
        )
        self.chat_text.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Message input
        self.input_frame = ctk.CTkFrame(self.chat_tab)
        self.input_frame.pack(pady=10, padx=20, fill="x")
        
        self.message_entry = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Type a message...",
            font=("Helvetica", 12)
        )
        self.message_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        self.send_button = ctk.CTkButton(
            self.input_frame,
            text="Send",
            command=self.send_message
        )
        self.send_button.pack(side="right", padx=10)
        

        
        # Bind Enter key to send message
        self.message_entry.bind("<Return>", lambda e: self.send_message())
        
        # Start message processing thread
        self.message_thread = threading.Thread(target=self.process_messages)
        self.message_thread.daemon = True
        self.message_thread.start()
    
    def toggle_connection(self):
        """Toggle connection to server"""
        if not self.client.connected:
            host = self.host_entry.get()
            try:
                port = int(self.port_entry.get())
            except:
                self.add_system_message("Invalid port number")
                return
            
            username = self.username_entry.get()
            if not username:
                self.add_system_message("Please enter a username")
                return
            
            if self.client.connect(username):
                self.client.host = host
                self.client.port = port
                self.connect_button.configure(text="Disconnect")
                self.add_system_message(f"Connected to {host}:{port}")
            else:
                self.add_system_message("Failed to connect to server")
        else:
            self.client.disconnect()
            self.connect_button.configure(text="Connect")
            self.add_system_message("Disconnected from server")
    
    def send_message(self):
        """Send a message to the server"""
        if not self.client.connected:
            self.add_system_message("Not connected to server")
            return
        
        message = self.message_entry.get()
        if not message:
            return
        
        self.message_entry.delete(0, "end")
        if self.client.send_message(message):
            self.add_message("You", message)
        else:
            self.add_system_message("Failed to send message")
    
    def add_message(self, sender, content):
        """Add a message to the chat area"""
        self.chat_text.insert("end", f"{sender}: {content}\n")
        self.chat_text.see("end")
    
    def add_system_message(self, content):
        """Add a system message to the chat area"""
        self.chat_text.insert("end", f"System: {content}\n", "system")
        self.chat_text.see("end")
    
    def add_announcement(self, announcement):
        """Add an announcement to the announcements area"""
        self.announcements_text.insert("end", f"[{announcement['timestamp']}] {announcement['content']}\n")
        self.announcements_text.see("end")
    
    def process_messages(self):
        """Process messages from the queue"""
        while True:
            try:
                data = self.client.message_queue.get()
                
                if data["type"] == "message":
                    self.add_message(data["data"]["sender"], data["data"]["content"])
                elif data["type"] == "system":
                    self.add_system_message(data["data"]["content"])
                elif data["type"] == "announcement":
                    self.add_announcement(data["data"])
            except:
                continue

if __name__ == "__main__":
    app = ClientGUI()
    app.mainloop()
