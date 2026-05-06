import socket
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading

# Server Settings
HOST = "0.0.0.0"  # Listen on all network interfaces
PORT = 5000  

# GUI Application
class MotionAlertApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Motion Alert Server")
        self.root.geometry("400x300")

        # Status Label
        self.status_label = tk.Label(root, text="Server Stopped", fg="red", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=5)

        # Alert Log (Scrolled Text Box)
        self.alert_log = scrolledtext.ScrolledText(root, width=50, height=10, state="disabled")
        self.alert_log.pack(pady=5)

        # Buttons
        self.start_button = tk.Button(root, text="Start Server", command=self.start_server, bg="green", fg="white")
        self.start_button.pack(side="left", padx=20, pady=10)

        self.stop_button = tk.Button(root, text="Stop Server", command=self.stop_server, bg="red", fg="white", state="disabled")
        self.stop_button.pack(side="right", padx=20, pady=10)

        # Server Variables
        self.server_thread = None
        self.server_running = False
        self.server_socket = None

    def start_server(self):
        """Start the server in a new thread"""
        if not self.server_running:
            self.server_running = True
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()

            # Update UI
            self.status_label.config(text="Server Running...", fg="green")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

    def stop_server(self):
        """Stop the server"""
        self.server_running = False
        if self.server_socket:
            self.server_socket.close()

        # Update UI
        self.status_label.config(text="Server Stopped", fg="red")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")

    def run_server(self):
        """Server to receive motion alerts"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((HOST, PORT))
            self.server_socket.listen(5)
            self.log_message("Server is listening for alerts...")

            while self.server_running:
                try:
                    client, addr = self.server_socket.accept()
                    data = client.recv(1024).decode('utf-8')

                    if data:
                        message = f"Alert from {addr}: {data}"
                        self.log_message(message)
                        self.show_alert(data)

                    client.close()
                except:
                    break  # Exit if server is stopped

        except Exception as e:
            self.log_message(f"Error: {e}")

    def log_message(self, message):
        """Log messages to the text area"""
        self.alert_log.config(state="normal")
        self.alert_log.insert(tk.END, message + "\n")
        self.alert_log.config(state="disabled")
        self.alert_log.yview(tk.END)

    def show_alert(self, message):
        """Show popup notification for motion detection"""
        self.root.after(0, lambda: messagebox.showwarning("Motion Alert", message))

# Run the Application
if __name__ == "__main__":
    root = tk.Tk()
    app = MotionAlertApp(root)
    root.mainloop()
