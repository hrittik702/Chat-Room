import socket
import threading

HOST = '192.168.226.102'
PORT = 12345

# {room_code: [(client_socket, username), ...]}
rooms = {}
rooms_lock = threading.Lock()


def broadcast(message, room_code, exclude=None):
    """Send a message to every client in a room, optionally excluding one."""
    with rooms_lock:
        members = list(rooms.get(room_code, []))
    for client_sock, _ in members:
        if client_sock is exclude:
            continue
        try:
            client_sock.send(message.encode('utf-8'))
        except Exception:
            pass


def remove_client(client_sock, room_code):
    """Remove a client from its room and return the username."""
    with rooms_lock:
        members = rooms.get(room_code, [])
        username = None
        for i, (sock, name) in enumerate(members):
            if sock is client_sock:
                username = name
                members.pop(i)
                break
        # clean up empty rooms
        if room_code in rooms and len(rooms[room_code]) == 0:
            del rooms[room_code]
    return username


def handle_client(client_sock, addr):
    """Handle the full lifecycle of one client connection."""
    room_code = None
    username = None
    try:
        # --- handshake: get room code ---
        client_sock.send('ROOM'.encode('utf-8'))
        room_code = client_sock.recv(1024).decode('utf-8').strip()

        if not room_code or len(room_code) != 4 or not room_code.isdigit():
            client_sock.send('ERROR:Invalid room code. Must be 4 digits.'.encode('utf-8'))
            client_sock.close()
            return

        # --- handshake: get username ---
        client_sock.send('NICK'.encode('utf-8'))
        username = client_sock.recv(1024).decode('utf-8').strip()

        if not username:
            client_sock.send('ERROR:Username cannot be empty.'.encode('utf-8'))
            client_sock.close()
            return

        # --- register client in the room ---
        with rooms_lock:
            if room_code not in rooms:
                rooms[room_code] = []
            rooms[room_code].append((client_sock, username))

        print(f"[Room {room_code}] {username} joined  ({addr})")

        # notify everyone in the room (including the new user)
        broadcast(f"SERVER: {username} has entered the chat!", room_code)

        # send current member count to the joiner
        with rooms_lock:
            count = len(rooms.get(room_code, []))
        client_sock.send(f"SERVER: Welcome! There are {count} user(s) in room {room_code}.".encode('utf-8'))

        # --- main message loop ---
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            message = data.decode('utf-8')
            broadcast(message, room_code, exclude=client_sock)

    except (ConnectionResetError, ConnectionAbortedError, OSError):
        pass
    finally:
        # --- cleanup ---
        if room_code and username:
            removed_name = remove_client(client_sock, room_code)
            if removed_name:
                print(f"[Room {room_code}] {removed_name} left  ({addr})")
                broadcast(f"SERVER: {removed_name} has left the chat!", room_code)
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
