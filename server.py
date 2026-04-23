import socket
import threading
import os 

#host and port declaration
HOST='127.0.0.1'
PORT=12345

#dictionary = {key : room_code, value : list of client sockets and username}
rooms={}
rooms_lock = threading.Lock()

def broadcast(message, room_code, exclude=None):
    file_path=f"room_{room_code}.txt"
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception as e:
        print(f"Error writing to history file: {e}")
    #automatic close 
    with rooms_lock :
        members = list(rooms.get(room_code, [])) #snapshot of list of users 
    for client_sock, _ in members :  
        if client_sock is exclude :
            continue
        try :
            client_sock.send(message.encode('utf-8'))
        except Exception:
            pass

def remove_client(client_sock,room_code):
    with rooms_lock :
        members = rooms.get(room_code, [])
        username = None 
    for i, (sock,name) in enumerate(members) :
        if sock is client_sock :
            username = name
            members.pop(i)
            break
        if room_code in rooms and len(rooms[room_code]) == 0 :
            del rooms[room_code]
    return username

def handle_client(client_sock, addr):
    room_code = None
    username = None
    try:
        #handshake
        client_sock.send('ROOM'.encode('utf-8'))
        room_code = client_sock.recv(1024).decode('utf-8').strip()

        # room code must be 4 digit and numeric only
        if not room_code or len(room_code) != 4 or not room_code.isdigit():
            client_sock.send('ERROR : Invalid room code. Must be 4 digits.'.encode('utf-8'))
            client_sock.close()
            return 

        #get username
        client_sock.send('NICK'.encode('utf-8'))
        username = client_sock.recv(1024).decode('utf-8').strip()
        if not username:
            client_sock.send('ERROR : Username cannot be empty'.encode('utf-8'))
            client_sock.close()
            return

        #connecting to chat room
        with rooms_lock:
            if room_code not in rooms:
                rooms[room_code] = []
                
                # NEW: Create a blank history file when a new room is made
                file_path = f"room_{room_code}.txt"
                if not os.path.exists(file_path):
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"--- Chat History for Room {room_code} ---\n")

            rooms[room_code].append((client_sock, username))
            
        print(f"[Room {room_code}] {username} joined ({addr})")

        #history feature
        file_path = f"room_{room_code}.txt"
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    history_data = f.read()
                client_sock.send(history_data.encode('utf-8'))
            except Exception as e:
                print(f"Error reading history: {e}")

        # new user
        broadcast(f"SERVER : {username} has entered the chat!", room_code)

        # send current member count to the joiner
        with rooms_lock:
            count = len(rooms.get(room_code, []))
        client_sock.send(f"\nSERVER : Welcome! There are {count} user(s) in room {room_code}.\n".encode('utf-8'))

        # main message loop
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            message = data.decode('utf-8')
            # Add the username so everyone knows who sent it
            formatted_message = f"{username}: {message}"
            broadcast(formatted_message, room_code, exclude=client_sock) 
    
    except (ConnectionResetError, ConnectionAbortedError, OSError):
        pass
    
    finally:
        # user leaving chat room
        if room_code and username:
            removed_name = remove_client(client_sock, room_code)
            if removed_name:
                print(f"[Room {room_code}] {removed_name} left ({addr})")
                broadcast(f"SERVER : {removed_name} has left the chat!", room_code)
        try:
            client_sock.close()
        except Exception:
            pass  


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"Server listening on {HOST}:{PORT} ...")

    try:
        while True:
            client_sock, addr = server.accept()
            print(f"New connection from {addr}")
            thread = threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server.close()


if __name__ == '__main__':
    main()
 




