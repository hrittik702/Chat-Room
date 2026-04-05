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




