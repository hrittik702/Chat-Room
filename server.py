import socket
import threading

#host and port declaration
host='127.0.0.1'
port=12345

#dictionary = {key : room_code, value : list of client sockets and username}
rooms={}
rooms_lock = threading.Lock()

def broadcast(message, room_code, exclude=None):
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
        members = rooms.get(client_sock, [])
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
    #get roomcode for joining server
    try :
        client_sock.send('ROOM'.encode('utf-8'))
        room_code = client_sock.recv(1024).decode('utf-8').strip()

        #room code must be 4 digit and numeric only
        if not room_code or len(room_code)!=4 or not room_code.isdigit():
            client_sock.send('ERROR : Invalid room code. Must be 4 digits.'.encode('utf-8'))
            client_sock.close()

        #get username & strip is used for string cleanup /n
        client_sock.send('NICK'.encode('utf-8'))
        username = client_sock.recv(1024).decode('utf-8').strip()
        if not username :
            client_sock.send('ERROR : Username cannot be empty'.encode('utf-8')).strip()
            client_sock.close()
            return

        #getting user into chat room
        with rooms_lock :
            if room_code not in rooms :
                rooms[room_code] = []
            rooms[room_code].append((client_sock, username))
        print(f"[Room {room_code}] {username} joined ({addr})")

        #server broadcast that a user has entered the chat
        broadcast(f"Server : {username} has entered the chat!", room_code)

        # send current member count to the joiner
        with rooms_lock:
            count = len(rooms.get(room_code, []))
        client_sock.send(f"SERVER: Welcome! There are {count} user(s) in room {room_code}.".encode('utf-8'))

        #sending messages
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            message = data.decode('utf-8')
            broadcast(message, room_code, exclude=client_sock) 
    
    except (ConnectionResetError, ConnectionAbortedError, OSError):
        pass
    
    finally:
        #user leaving chat roomo
        if room_code and username:
            removed_name = remove_client(client_sock, room_code)
            if removed_name:
                print(f"[Room {room_code}] {removed_name} left  ({addr})")
                broadcast(f"SERVER: {removed_name} has left the chat!", room_code)
        try:
            client_sock.close()
        except Exception:
            pass   




