import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import time

HOST = '192.168.226.102'
PORT = 12345


class ChatClient:
    def __init__(self):
        self.sock = None
        self.username = None
        self.room_code = None
        self.connected = False

        # ── main window ──────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("Chat Room")
        self.root.geometry("520x620")
        self.root.minsize(420, 500)
        self.root.configure(bg="#1e1e2e")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # ── colours & fonts ──────────────────────────────────────────
        self.BG       = "#1e1e2e"
        self.FG       = "#cdd6f4"
        self.ACCENT   = "#89b4fa"
        self.INPUT_BG = "#313244"
        self.BTN_BG   = "#89b4fa"
        self.BTN_FG   = "#1e1e2e"
        self.ERR      = "#f38ba8"
        self.SYS_CLR  = "#a6e3a1"
        self.FONT     = ("Segoe UI", 11)
        self.FONT_B   = ("Segoe UI", 11, "bold")
        self.FONT_H   = ("Segoe UI", 18, "bold")
        self.FONT_SM  = ("Segoe UI", 9)

        # start with login view
        self.login_frame = None
        self.chat_frame = None
        self.build_login_screen()

        self.root.mainloop()

    # ══════════════════════════════════════════════════════════════════
    #  LOGIN SCREEN
    # ══════════════════════════════════════════════════════════════════
    def build_login_screen(self):
        if self.chat_frame:
            self.chat_frame.destroy()

        self.login_frame = tk.Frame(self.root, bg=self.BG)
        self.login_frame.pack(expand=True)

        tk.Label(
            self.login_frame, text="💬  Chat Room", font=self.FONT_H,
            bg=self.BG, fg=self.ACCENT
        ).pack(pady=(0, 24))

        # room code
        tk.Label(
            self.login_frame, text="Room Code (4 digits)", font=self.FONT,
            bg=self.BG, fg=self.FG
        ).pack(anchor="w", padx=40)

        self.room_entry = tk.Entry(
            self.login_frame, font=self.FONT, bg=self.INPUT_BG, fg=self.FG,
            insertbackground=self.FG, relief="flat", width=28, justify="center"
        )
        self.room_entry.pack(pady=(2, 14), ipady=6, padx=40)
        self.room_entry.focus_set()

        # username
        tk.Label(
            self.login_frame, text="Username", font=self.FONT,
            bg=self.BG, fg=self.FG
        ).pack(anchor="w", padx=40)

        self.user_entry = tk.Entry(
            self.login_frame, font=self.FONT, bg=self.INPUT_BG, fg=self.FG,
            insertbackground=self.FG, relief="flat", width=28, justify="center"
        )
        self.user_entry.pack(pady=(2, 20), ipady=6, padx=40)
        self.user_entry.bind("<Return>", lambda e: self.join_room())

        # join button
        self.join_btn = tk.Button(
            self.login_frame, text="Join Room", font=self.FONT_B,
            bg=self.BTN_BG, fg=self.BTN_FG, activebackground="#74c7ec",
            relief="flat", cursor="hand2", width=20, command=self.join_room
        )
        self.join_btn.pack(ipady=6)

        # error label (hidden until needed)
        self.err_label = tk.Label(
            self.login_frame, text="", font=self.FONT_SM,
            bg=self.BG, fg=self.ERR
        )
        self.err_label.pack(pady=(10, 0))

    # ══════════════════════════════════════════════════════════════════
    #  CHAT SCREEN
    # ══════════════════════════════════════════════════════════════════
    def build_chat_screen(self):
        if self.login_frame:
            self.login_frame.destroy()

        self.chat_frame = tk.Frame(self.root, bg=self.BG)
        self.chat_frame.pack(fill="both", expand=True)

        # header
        header = tk.Frame(self.chat_frame, bg="#181825", height=44)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text=f"Room {self.room_code}", font=self.FONT_B,
            bg="#181825", fg=self.ACCENT
        ).pack(side="left", padx=14, pady=6)

        tk.Label(
            header, text=f"@{self.username}", font=self.FONT_SM,
            bg="#181825", fg="#6c7086"
        ).pack(side="right", padx=14)

        leave_btn = tk.Button(
            header, text="Leave", font=self.FONT_SM,
            bg=self.ERR, fg=self.BTN_FG, relief="flat", cursor="hand2",
            command=self.leave_room
        )
        leave_btn.pack(side="right", padx=(0, 6), pady=6)

        # message display
        self.msg_area = scrolledtext.ScrolledText(
            self.chat_frame, wrap="word", state="disabled",
            font=self.FONT, bg=self.BG, fg=self.FG,
            relief="flat", padx=12, pady=10,
            insertbackground=self.FG,
            selectbackground="#45475a"
        )
        self.msg_area.pack(fill="both", expand=True, padx=6, pady=(4, 0))

        # tag styles for coloured messages
        self.msg_area.tag_config("system", foreground=self.SYS_CLR)
        self.msg_area.tag_config("self", foreground=self.ACCENT)
        self.msg_area.tag_config("error", foreground=self.ERR)

        # bottom bar: entry + send
        bottom = tk.Frame(self.chat_frame, bg="#181825")
        bottom.pack(fill="x", padx=6, pady=6)

        self.msg_entry = tk.Entry(
            bottom, font=self.FONT, bg=self.INPUT_BG, fg=self.FG,
            insertbackground=self.FG, relief="flat"
        )
        self.msg_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 6))
        self.msg_entry.bind("<Return>", lambda e: self.send_message())
        self.msg_entry.focus_set()

        send_btn = tk.Button(
            bottom, text="Send", font=self.FONT_B,
            bg=self.BTN_BG, fg=self.BTN_FG, activebackground="#74c7ec",
            relief="flat", cursor="hand2", width=8, command=self.send_message
        )
        send_btn.pack(side="right", ipady=6)

    # ══════════════════════════════════════════════════════════════════
    #  NETWORKING
    # ══════════════════════════════════════════════════════════════════
    def join_room(self):
        room = self.room_entry.get().strip()
        user = self.user_entry.get().strip()

        if len(room) != 4 or not room.isdigit():
            self.err_label.config(text="Room code must be exactly 4 digits.")
            return
        if not user:
            self.err_label.config(text="Username cannot be empty.")
            return

        self.room_code = room
        self.username = user

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))

            # wait for ROOM prompt
            prompt = self.sock.recv(1024).decode('utf-8')
            if prompt != 'ROOM':
                raise ConnectionError("Unexpected server handshake.")
            self.sock.send(room.encode('utf-8'))

            # wait for NICK prompt
            prompt = self.sock.recv(1024).decode('utf-8')
            if prompt != 'NICK':
                # could be an error message
                if prompt.startswith('ERROR:'):
                    raise ConnectionError(prompt[6:])
                raise ConnectionError("Unexpected server handshake.")
            self.sock.send(user.encode('utf-8'))

            self.connected = True
            self.build_chat_screen()

            # start receive thread
            recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
            recv_thread.start()

        except Exception as e:
            self.err_label.config(text=f"Connection failed: {e}")

    def receive_loop(self):
        """Background thread that reads messages from the server."""
        while self.connected:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                message = data.decode('utf-8')

                # choose tag based on content
                if message.startswith("SERVER:"):
                    tag = "system"
                else:
                    tag = None

                self.display_message(message, tag=tag)

            except (ConnectionResetError, ConnectionAbortedError, OSError):
                break

        if self.connected:
            self.connected = False
            self.display_message("** Disconnected from server **", tag="error")

    def send_message(self):
        msg = self.msg_entry.get().strip()
        if not msg or not self.connected:
            return
        self.msg_entry.delete(0, tk.END)
        full = f"{self.username}: {msg}"
        try:
            self.sock.send(full.encode('utf-8'))
            self.display_message(full, tag="self")
        except Exception:
            self.display_message("** Failed to send message **", tag="error")

    def display_message(self, text, tag=None):
        """Thread-safe insertion into the ScrolledText widget."""
        def _insert():
            self.msg_area.config(state="normal")
            self.msg_area.insert(tk.END, text + "\n", tag)
            self.msg_area.config(state="disabled")
            self.msg_area.see(tk.END)
        self.root.after(0, _insert)

    def leave_room(self):
        self.disconnect()
        self.build_login_screen()

    def disconnect(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def on_close(self):
        self.disconnect()
        self.root.destroy()


if __name__ == '__main__':
    ChatClient()