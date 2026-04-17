import socket
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(("0.0.0.0", 1110))
server_socket.listen(5)
logging.info("POP3 Server listening on port 1110")

while True:
    conn, addr = server_socket.accept()
    logging.info(f"Connection from {addr}")
    conn.sendall(b"+OK POP3 server ready\r\n")
    
    authenticated = False
    username = ""
    user_messages = []
    deleted_messages = set()
    
    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break
            
            logging.debug(f"Received: {data}")
            
            parts = data.split()
            command = parts[0].upper()
            argument = parts[1] if len(parts) > 1 else ""
            
            if not authenticated:
                # USER command
                if command == "USER":
                    username = argument
                    conn.sendall(b"+OK User accepted\r\n")
                
                # PASS command
                elif command == "PASS":
                    if not username:
                        conn.sendall(b"-ERR USER first\r\n")
                        continue
                    
                    db_conn = sqlite3.connect('emails.db')
                    cursor = db_conn.cursor()
                    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                    user = cursor.fetchone()
                    
                    if user:
                        authenticated = True
                        # Load messages - FIXED: Match with brackets
                        cursor.execute(
                            "SELECT id, size, recipient FROM emails WHERE recipient = ?",
                            (f"<{username}>",)
                        )
                        user_messages = cursor.fetchall()
                        conn.sendall(f"+OK Maildrop ready, {len(user_messages)} messages\r\n".encode())
                        logging.info(f"User {username} authenticated, {len(user_messages)} messages")
                    else:
                        conn.sendall(b"-ERR Invalid username\r\n")
                    
                    db_conn.close()
                
                elif command == "QUIT":
                    conn.sendall(b"+OK Bye\r\n")
                    break
                
                else:
                    conn.sendall(b"-ERR Authentication required\r\n")
            
            else:
                # STAT command
                if command == "STAT":
                    total = len([m for i, m in enumerate(user_messages) if i+1 not in deleted_messages])
                    total_size = sum(m[1] for i, m in enumerate(user_messages) if i+1 not in deleted_messages)
                    conn.sendall(f"+OK {total} {total_size}\r\n".encode())
                
                # LIST command
                elif command == "LIST":
                    print("debug list block")
                    if argument:
                        msg_num = int(argument)
                        if 1 <= msg_num <= len(user_messages) and msg_num not in deleted_messages:
                            msg_id, size, recipient = user_messages[msg_num-1]
                            conn.sendall(f"+OK {msg_num} {size}\r\n".encode())
                        else:
                            conn.sendall(b"-ERR No such message\r\n")
                    else:
                        conn.sendall(f"+OK {len(user_messages)} messages\r\n".encode())
                        for idx, (msg_id, size, recipient) in enumerate(user_messages, 1):
                            if idx not in deleted_messages:
                                conn.sendall(f"{idx} {size}\r\n".encode())
                        conn.sendall(b".\r\n")
                
                # RETR command - FIXED
                elif command == "RETR":
                    print("debug retr block")
                    if not argument:
                        conn.sendall(b"-ERR Message number required\r\n")
                        continue
                    
                    msg_num = int(argument)
                    if 1 <= msg_num <= len(user_messages) and msg_num not in deleted_messages:
                        msg_id, size, recipient = user_messages[msg_num-1]
                        
                        db_conn = sqlite3.connect('emails.db')
                        cursor = db_conn.cursor()
                        cursor.execute("SELECT message FROM emails WHERE id = ?", (msg_id,))
                        result = cursor.fetchone()
                        db_conn.close()
                        
                        if result:
                            message = result[0]
                            conn.sendall(f"+OK {len(message)} octets\r\n".encode())
                            conn.sendall(message.encode())
                            conn.sendall(b"\r\n.\r\n")
                            logging.info(f"RETR {msg_num} sent")
                        else:
                            conn.sendall(b"-ERR Message not found\r\n")
                    else:
                        conn.sendall(b"-ERR No such message\r\n")
                
                # DELE command
                elif command == "DELE":
                    if argument:
                        msg_num = int(argument)
                        if 1 <= msg_num <= len(user_messages) and msg_num not in deleted_messages:
                            deleted_messages.add(msg_num)
                            conn.sendall(f"+OK Message {msg_num} deleted\r\n".encode())
                        else:
                            conn.sendall(b"-ERR No such message\r\n")
                    else:
                        conn.sendall(b"-ERR Message number required\r\n")
                
                # RSET command
                elif command == "RSET":
                    deleted_messages.clear()
                    conn.sendall(b"+OK\r\n")
                
                # QUIT command
                elif command == "QUIT":
                    if deleted_messages:
                        db_conn = sqlite3.connect('emails.db')
                        cursor = db_conn.cursor()
                        for msg_num in deleted_messages:
                            if msg_num <= len(user_messages):
                                msg_id, _, _ = user_messages[msg_num-1]
                                cursor.execute("DELETE FROM emails WHERE id = ?", (msg_id,))
                        db_conn.commit()
                        db_conn.close()
                        logging.info(f"Deleted {len(deleted_messages)} messages")
                    
                    conn.sendall(b"+OK Bye\r\n")
                    break
                
                else:
                    conn.sendall(b"-ERR Unknown command\r\n")
                    
        except Exception as e:
            logging.error(f"Error: {e}")
            break
    
    conn.close()

server_socket.close()