import socket
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import logging

class SimpleEmailClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Email Client")
        self.root.geometry("600x500")
        
        self.smtp_host = "localhost"
        self.smtp_port = 2525
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="From (Sender):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.from_entry = ttk.Entry(main_frame, width=50)
        self.from_entry.grid(row=0, column=1, pady=5, padx=5)
        self.from_entry.insert(0, "sender@example.com")
        
        ttk.Label(main_frame, text="To (Recipient):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.to_entry = ttk.Entry(main_frame, width=50)
        self.to_entry.grid(row=1, column=1, pady=5, padx=5)
        self.to_entry.insert(0, "recipient@example.com")
        
        ttk.Label(main_frame, text="Subject:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.subject_entry = ttk.Entry(main_frame, width=50)
        self.subject_entry.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(main_frame, text="Message:").grid(row=3, column=0, sticky=tk.NW, pady=5)
        self.message_text = scrolledtext.ScrolledText(main_frame, width=60, height=15)
        self.message_text.grid(row=3, column=1, pady=5, padx=5)
        
        self.send_btn = ttk.Button(main_frame, text="Send Email", command=self.send_email)
        self.send_btn.grid(row=4, column=1, pady=15, sticky=tk.E)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def send_email(self):
        sender = self.from_entry.get().strip()
        recipient = self.to_entry.get().strip()
        subject = self.subject_entry.get().strip()
        body = self.message_text.get("1.0", tk.END).strip()
        
        if not sender or not recipient:
            messagebox.showerror("Error", "Please enter both sender and recipient")
            return
        
        try:
            # Manual socket connection (bypasses smtplib)
            self.status_var.set("Connecting...")
            self.root.update()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.smtp_host, self.smtp_port))
            
            # Read greeting
            response = sock.recv(1024).decode()
            logging.debug(f"Server: {response}")
            
            # Send HELO
            sock.sendall(b"HELO client.local\r\n")
            response = sock.recv(1024).decode()
            logging.debug(f"Server: {response}")
            
            # Send MAIL FROM
            sock.sendall(f"MAIL FROM: <{sender}>\r\n".encode())
            response = sock.recv(1024).decode()
            logging.debug(f"Server: {response}")
            
            # Send RCPT TO
            sock.sendall(f"RCPT TO: <{recipient}>\r\n".encode())
            response = sock.recv(1024).decode()
            logging.debug(f"Server: {response}")
            
            # Send DATA
            sock.sendall(b"DATA\r\n")
            response = sock.recv(1024).decode()
            logging.debug(f"Server: {response}")
            
            # Send email content
            email_content = ""
            if subject:
                email_content += f"Subject: {subject}\r\n"
            email_content += f"\r\n{body}\r\n"
            email_content += ".\r\n"
            
            sock.sendall(email_content.encode())
            response = sock.recv(1024).decode()
            logging.debug(f"Server: {response}")
            
            # Send QUIT
            sock.sendall(b"QUIT\r\n")
            sock.close()
            
            self.status_var.set("Email sent successfully!")
            messagebox.showinfo("Success", "Email sent!")
            self.subject_entry.delete(0, tk.END)
            self.message_text.delete("1.0", tk.END)
            
        except ConnectionRefusedError:
            self.status_var.set("ERROR: Server not running!")
            messagebox.showerror("Error", "SMTP server is not running on localhost:2525")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", f"Failed to send: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleEmailClient(root)
    root.mainloop()