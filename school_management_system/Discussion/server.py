import socket
import threading
import queue
import customtkinter as ctk
from functions import send_data, receive_data
import os
import time

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
        # Get all network interfaces
        hostname = socket.gethostname()
        # Get local IP
        local_ip = socket.gethostbyname(hostname)
        ips.append(local_ip)
        
        # Get all IPs
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip != "127.0.0.1" and ip not in ips:
                ips.append(ip)
    except:
        pass
    return ips

class Server:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.socket = None
        self.clients = []
        self.message_queue = queue.Queue()
        self.running = False
        self.announcements = []  # Store announcements
    
    def start(self):
        """Start the server"""
        try:
            # Check if port is available
            if not is_port_available(self.port):
                return f"Error: Port {self.port} is already in use. Please choose a different port."

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Add socket options to prevent "Address already in use" error
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            # Get and display available IPs
            available_ips = get_local_ips()
            ip_info = f"Server started on port {self.port}\nAvailable IPs: {', '.join(available_ips)}"
            
            # Start accepting clients in a separate thread
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            
            return ip_info
        except PermissionError:
            return f"Error: Permission denied. Try running with administrator privileges."
        except OSError as e:
            if "Address already in use" in str(e):
                return f"Error: Port {self.port} is already in use. Please choose a different port."
            return f"Error starting server: {str(e)}"
        except Exception as e:
            return f"Error starting server: {str(e)}"
    
    def stop(self):
        """Stop the server"""
        self.running = False
        if self.socket:
            self.socket.close()
        
        # Close all client connections
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
                client_socket, address = self.socket.accept()
                self.clients.append(client_socket)
                
                # Start client handler thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            except:
                break
    
    def handle_client(self, client_socket, address):
        """Handle client connection"""
        # Send existing announcements to new client
        for announcement in self.announcements:
            try:
                send_data(client_socket, {
                    "type": "announcement",
                    "data": announcement
                })
            except:
                pass

        while self.running:
            try:
                data = receive_data(client_socket)
                if not data:
                    break
                
                if data["type"] == "message":
                    # Broadcast message to all clients
                    for client in self.clients:
                        if client != client_socket:
                            try:
                                send_data(client, data)
                            except:
                                continue
                
                # Put message in queue
                self.message_queue.put(data)
            except:
                break
        
        # Remove client
        if client_socket in self.clients:
            self.clients.remove(client_socket)
        try:
            client_socket.close()
        except:
            pass

    def broadcast_announcement(self, content):
        """Broadcast an announcement to all clients"""
        announcement = {
            "content": content,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.announcements.append(announcement)
        
        # Broadcast to all clients
        for client in self.clients:
            try:
                send_data(client, {
                    "type": "announcement",
                    "data": announcement
                })
            except:
                continue
        
        return announcement

class ServerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("LAN Messenger - Server")
        self.geometry("800x600")
        
        # Initialize server
        self.server = Server()
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(self.main_frame)
        self.tabview.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Create tabs
        self.chat_tab = self.tabview.add("Chat")
        
        # Server controls
        self.control_frame = ctk.CTkFrame(self.chat_tab)
        self.control_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(
            self.control_frame,
            text="Server Status: Stopped",
            font=("Helvetica", 14)
        )
        self.status_label.pack(side="left", padx=10)
        
        self.start_button = ctk.CTkButton(
            self.control_frame,
            text="Start Server",
            command=self.toggle_server
        )
        self.start_button.pack(side="right", padx=10)
        
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
    
    def toggle_server(self):
        """Toggle server on/off"""
        if not self.server.running:
            status = self.server.start()
            self.status_label.configure(text=f"Server Status: Running ({status})")
            self.start_button.configure(text="Stop Server")
        else:
            self.server.stop()
            self.status_label.configure(text="Server Status: Stopped")
            self.start_button.configure(text="Start Server")
            self.add_system_message("Server stopped")
    
    def send_message(self):
        """Send a message to all clients"""
        if not self.server.running:
            self.add_system_message("Server is not running")
            return
        
        message = self.message_entry.get()
        if not message:
            return
        
        self.message_entry.delete(0, "end")
        self.add_message("You", message)
        
        # Create message data
        data = {
            "type": "message",
            "data": {
                "sender": "Server",
                "content": message
            }
        }
        
        # Broadcast to clients
        for client in self.server.clients:
            try:
                send_data(client, data)
            except:
                continue
    
    def send_announcement(self):
        """Send an announcement to all clients"""
        if not self.server.running:
            self.add_system_message("Server is not running")
            return
        
        announcement = self.announcement_entry.get()
        if not announcement:
            return
        
        self.announcement_entry.delete(0, "end")
        
        # Broadcast announcement
        announcement_data = self.server.broadcast_announcement(announcement)
        self.add_announcement(announcement_data)
    
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
                data = self.server.message_queue.get()
                
                if data["type"] == "message":
                    self.add_message(data["data"]["sender"], data["data"]["content"])
                elif data["type"] == "system":
                    self.add_system_message(data["data"]["content"])
            except:
                continue

if __name__ == "__main__":
    app = ServerGUI()
    app.mainloop()
