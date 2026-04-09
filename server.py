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



