import datetime
import os
import socket
import sqlite3
import logging

#initializing the logging, DEBUG level gives full info, you can set different levels as well
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

#checking if inbox folder exists or not
if not os.path.exists("emails.db"):
    logging.error(f"file not found: inbox")

#builing the socket
#use AF_INET6 for ipv6 and SOCK_DGRAM for udp
#SO_REUSEADDR reuses the address.
server_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
server_socket.bind(("localhost",2525))
server_socket.listen(1)
logging.debug("Socket bound on localhost: 2525")

conn, addr=server_socket.accept()
logging.info(f"Server connected to {addr}")
conn.sendall(b"220 SMTP Server Ready!\r\n")

#these are state variables.
#in_data_mode for if mail content is being received or not. 
#false=waiting for HELO and stuff true= receiving data
in_data_mode=False
helo_received=False
mail_from_received=False
rcpt_to_received=False
sender=""
recipient=""
message_lines=[]

while True:
    data=conn.recv(1024).decode()
    if not data:
        break
    
    for line in data.split("\r\n"):
        logging.debug(f"received: {line}")
        
        if in_data_mode:
            if line == ".":
                header = f"From: {sender}\nTo: {recipient}\n\n"
                full_message = header + "\n".join(message_lines)
                

                subject = ""
                for msg_line in message_lines:
                    if msg_line.lower().startswith("subject:"):
                        subject = msg_line[8:].strip()
                        break
                
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.datetime.now().strftime("%H-%M-%S")
                
                try:
                    db_conn = sqlite3.connect('emails.db')
                    cursor = db_conn.cursor()
                    cursor.execute('''
                        INSERT INTO emails (sender, recipient, subject, message, received_date, received_time, size)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        sender,
                        recipient,
                        subject,
                        full_message,
                        date_str,
                        time_str,
                        len(full_message)
                    ))
                    db_conn.commit()
                    db_conn.close()
                    logging.info(f"Message saved! From: {sender}, To: {recipient}, Size: {len(full_message)} bytes")
                except Exception as e:
                    logging.error(f"Failed to save message to database: {e}")
                
                # Optional: Also save as .eml file
                filename = f"inbox/mail_{date_str}_{time_str}.eml"
                try:
                    with open(filename, 'w') as f:
                        f.write(full_message)
                    logging.info(f"Message also saved to {filename}")
                except Exception as e:
                    logging.error(f"Failed to save file: {e}")
                
                in_data_mode = False
                helo_received = False
                mail_from_received = False
                rcpt_to_received = False
                sender = ""
                recipient = ""
                message_lines = []
                
                conn.sendall(b"250 OK: Message accepted for delivery\r\n")
                
            else:
                message_lines.append(line)
                
        else:
            
            if line.upper().startswith("HELO"):
                helo_received=True
                conn.sendall(b"250 Hello\r\n")
                logging.info("HELO command received")
                
            elif line.upper().startswith("MAIL FROM:"):
                if not helo_received:
                        conn.sendall(b"503 Bad sequence of commands\r\n")
                        logging.warning("MAIL FROM received before HELO")
                else:
                        sender = line[10:].strip()
                        mail_from_received = True
                        conn.sendall(b"250 OK\r\n")
                        logging.info(f"MAIL FROM accepted: {sender}")
            elif line.upper().startswith("RCPT TO:"):
                if not mail_from_received:
                    conn.sendall(b"503 Bad sequence of commands\r\n")
                    logging.warning("RCPT TO received before MAIL FROM")
                else:
                    recipient = line[8:].strip()
                    rcpt_to_received = True
                    conn.sendall(b"250 OK\r\n")
                    logging.info(f"RCPT TO accepted: {recipient}")

            elif line.upper() == "DATA":
                if not rcpt_to_received:
                    conn.sendall(b"503 Bad sequence of commands\r\n")
                    logging.warning("DATA received before RCPT TO")
                else:
                    in_data_mode = True
                    message_lines = []
                    conn.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                    logging.info("DATA mode started")
                    
            elif line.upper() == "QUIT":
                conn.sendall(b"221 Bye\r\n")
                logging.info("Client disconnected with QUIT")
                break

            else:
                conn.sendall(b"500 Syntax error: command unrecognized\r\n")
                logging.warning(f"Unrecognized command: {line}")
            
    
conn.close()
logging.info("Connection Closed!")

server_socket.close()
logging.info("Server Closed!")



