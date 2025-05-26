# Chat client with DeepL translation (multi-language configurable)

import socket
import threading
import deepl
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    s.close()
    return ip

DEEPL_API_KEY = "f9b2a1b9-34b1-40dc-997e-a22089c17457:fx"
translator = deepl.Translator(DEEPL_API_KEY)

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat Translator")
        self.text_area = scrolledtext.ScrolledText(root, state='disabled', width=60, height=20)
        self.text_area.pack(padx=10, pady=10)
        self.entry = tk.Entry(root, width=50)
        self.entry.pack(side=tk.LEFT, padx=(10,0), pady=(0,10))
        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.pack(side=tk.LEFT, padx=(5,10), pady=(0,10))
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.sock = None
        self.running = False
        self.is_server = False

        # Language setup dialogs
        self.lang_send = simpledialog.askstring("Language", "Your language (e.g. EN, ES, FR):", parent=root)
        self.lang_receive = simpledialog.askstring("Language", "Other user's language (e.g. EN, ES, FR):", parent=root)
        mode = simpledialog.askstring("Mode", "Enter 1 for Server or 2 for Client:", parent=root)
        if mode == "1":
            self.is_server = True
            self.start_server()
        else:
            self.is_server = False
            self.start_client()

    def start_server(self):
        ip_local = get_local_ip()
        messagebox.showinfo("Server Info", f"Server IP: {ip_local}\nPort: 12345\nShare this IP with your friend.")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', 12345))
        self.sock.listen()
        self.running = True
        threading.Thread(target=self.accept_client, daemon=True).start()

    def accept_client(self):
        try:
            client_socket, client_address = self.sock.accept()
            self.conn = client_socket
            self.append_text(f"🟢 Connected to {client_address}")
            threading.Thread(target=self.receive_messages, args=(self.conn,), daemon=True).start()
        except Exception as e:
            self.append_text(f"🔴 Error accepting connection: {e}")

    def start_client(self):
        host = simpledialog.askstring("Connect", "Enter server IP address:", parent=self.root)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, 12345))
            self.append_text("🚀 Connected to server.")
            self.conn = self.sock
            self.running = True
            threading.Thread(target=self.receive_messages, args=(self.conn,), daemon=True).start()
        except Exception as e:
            self.append_text(f"🔴 Connection error: {e}")

    def send_message(self):
        msg = self.entry.get()
        if not msg:
            return
        try:
            self.conn.send(msg.encode('utf-8'))
            self.append_text(f"You: {msg}")
            self.entry.delete(0, tk.END)
        except Exception as e:
            self.append_text(f"🔴 Error sending: {e}")

    def receive_messages(self, conn):
        while self.running:
            try:
                message = conn.recv(1024)
                if not message:
                    self.append_text("🔴 Connection closed.")
                    break
                message_decoded = message.decode('utf-8')
                translated = translator.translate_text(
                    message_decoded,
                    source_lang=self.lang_receive.upper(),
                    target_lang=self.lang_send.upper()
                )
                self.append_text(f"\n💬 Original: {message_decoded}")
                self.append_text(f"🌍 Translated: {translated.text}")
            except Exception as e:
                self.append_text(f"🔴 Error receiving: {e}")
                break

    def append_text(self, text):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)
        self.text_area.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()
