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

class HomeGUI(tk.Frame):
    """Ventana principal (home) para elegir nombre, idioma y modo."""
    def __init__(self, master, on_start_chat):
        super().__init__(master)
        self.master = master
        self.on_start_chat = on_start_chat
        self.pack(padx=20, pady=20)
        tk.Label(self, text="Nombre de usuario (solo letras y números):").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=(0,10))
        tk.Label(self, text="Tu idioma (ej: EN, ES, FR):").pack()
        self.lang_send_entry = tk.Entry(self)
        self.lang_send_entry.pack(pady=(0,10))
        tk.Label(self, text="Idioma del otro usuario (ej: EN, ES, FR):").pack()
        self.lang_receive_entry = tk.Entry(self)
        self.lang_receive_entry.pack(pady=(0,10))
        tk.Label(self, text="Modo:").pack()
        self.mode_var = tk.StringVar(value="1")
        tk.Radiobutton(self, text="Servidor", variable=self.mode_var, value="1").pack(anchor="w")
        tk.Radiobutton(self, text="Cliente", variable=self.mode_var, value="2").pack(anchor="w")
        tk.Button(self, text="Iniciar Chat", command=self.validate_and_start).pack(pady=(10,0))

    def validate_and_start(self):
        username = self.username_entry.get()
        if not username.isalnum():
            messagebox.showerror("Error", "El nombre solo puede contener letras y números.")
            return
        lang_send = self.lang_send_entry.get().strip()
        lang_receive = self.lang_receive_entry.get().strip()
        if not lang_send or not lang_receive:
            messagebox.showerror("Error", "Debes ingresar ambos idiomas.")
            return
        mode = self.mode_var.get()
        self.on_start_chat(username, lang_send, lang_receive, mode)

class ChatGUI(tk.Frame):
    """Ventana de chat con DeepL y botones extra."""
    def __init__(self, master, username, lang_send, lang_receive, mode, on_home):
        super().__init__(master)
        self.master = master
        self.username = username
        self.lang_send = lang_send
        self.lang_receive = lang_receive
        self.mode = mode
        self.on_home = on_home
        self.sock = None
        self.conn = None
        self.running = False
        self.is_server = (mode == "1")
        self.pack(padx=10, pady=10, fill="both", expand=True)

        self.text_area = scrolledtext.ScrolledText(self, state='disabled', width=60, height=20)
        self.text_area.pack(padx=10, pady=10, fill="both", expand=True)
        entry_frame = tk.Frame(self)
        entry_frame.pack(fill="x", padx=10, pady=(0,10))
        self.entry = tk.Entry(entry_frame, width=50)
        self.entry.pack(side=tk.LEFT, fill="x", expand=True)
        self.send_button = tk.Button(entry_frame, text="Enviar", command=self.send_message, state=tk.DISABLED)
        self.send_button.pack(side=tk.LEFT, padx=(5,0))
        self.clear_button = tk.Button(entry_frame, text="Limpiar chat", command=self.clear_chat)  # Nuevo botón limpiar
        self.clear_button.pack(side=tk.LEFT, padx=(5,0))
        self.home_button = tk.Button(entry_frame, text="Volver a Home", command=self.go_home, fg="blue")  # Nuevo botón home
        self.home_button.pack(side=tk.LEFT, padx=(5,0))
        self.exit_button = tk.Button(entry_frame, text="Salir", command=self.close_app, fg="red")
        self.exit_button.pack(side=tk.LEFT, padx=(5,0))
        self.entry.bind("<Return>", lambda event: self.send_message())

        self.master.protocol("WM_DELETE_WINDOW", self.close_app)

        if self.is_server:
            self.start_server()
        else:
            self.start_client()

    def start_server(self):
        ip_local = get_local_ip()
        messagebox.showinfo("Server Info", f"Server IP: {ip_local}\nPort: 12345\nComparte esta IP con tu amigo.")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('0.0.0.0', 12345))
        self.sock.listen()
        self.running = True
        threading.Thread(target=self.accept_client, daemon=True).start()

    def accept_client(self):
        try:
            client_socket, client_address = self.sock.accept()
            self.conn = client_socket
            self.append_text(f"🟢 Conectado a {client_address}")
            self.send_button.config(state=tk.NORMAL)
            threading.Thread(target=self.receive_messages, args=(self.conn,), daemon=True).start()
        except Exception as e:
            self.append_text(f"🔴 Error aceptando conexión: {e}")

    def start_client(self):
        host = simpledialog.askstring("Conectar", "Ingresa la IP del servidor:", parent=self.master)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, 12345))
            self.append_text("🚀 Conectado al servidor.")
            self.conn = self.sock
            self.running = True
            self.send_button.config(state=tk.NORMAL)
            threading.Thread(target=self.receive_messages, args=(self.conn,), daemon=True).start()
        except Exception as e:
            self.append_text(f"🔴 Error de conexión: {e}")

    def send_message(self):
        if not self.conn or not self.running:
            self.append_text("🔴 No conectado.")
            return
        msg = self.entry.get()
        if not msg:
            return
        try:
            self.conn.send(msg.encode('utf-8'))
            self.append_text(f"{self.username}: {msg}")  # Mostrar nombre de usuario
            self.entry.delete(0, tk.END)
        except Exception as e:
            self.append_text(f"🔴 Error enviando: {e}")

    def receive_messages(self, conn):
        while self.running:
            try:
                message = conn.recv(1024)
                if not message:
                    self.append_text("🔴 Conexión cerrada.")
                    self.running = False
                    self.send_button.config(state=tk.DISABLED)
                    break
                message_decoded = message.decode('utf-8')
                # Corregido: usar EN-US si el usuario puso EN para evitar deprecation warning
                target_lang = self.lang_send.upper()
                if target_lang == "EN":
                    target_lang = "EN-US"
                source_lang = self.lang_receive.upper()
                if source_lang == "EN":
                    source_lang = "EN-US"
                # Nuevo: detectar idioma del mensaje recibido
                try:
                    detected = translator.detect_language(message_decoded).language
                except Exception:
                    detected = source_lang
                # Si el idioma detectado no coincide con el esperado, mostrar sin traducir
                if detected != source_lang:
                    self.append_text(f"\n💬 (Idioma detectado: {detected}) Mensaje recibido sin traducir: {message_decoded}")
                else:
                    translated = translator.translate_text(
                        message_decoded,
                        source_lang=source_lang,
                        target_lang=target_lang
                    )
                    self.append_text(f"\n💬 Original: {message_decoded}")
                    self.append_text(f"🌍 Traducido: {translated.text}")
            except Exception as e:
                self.append_text(f"🔴 Error recibiendo: {e}")
                self.running = False
                self.send_button.config(state=tk.DISABLED)
                break

    def append_text(self, text):
        self.text_area.config(state='normal')
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)
        self.text_area.config(state='disabled')

    def clear_chat(self):
        # Nuevo método: limpiar el área de chat
        self.text_area.config(state='normal')
        self.text_area.delete(1.0, tk.END)
        self.text_area.config(state='disabled')

    def go_home(self):
        # Nuevo método: volver a la ventana principal (home)
        self.running = False
        try:
            if self.conn:
                self.conn.shutdown(socket.SHUT_RDWR)
                self.conn.close()
        except Exception:
            pass
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.pack_forget()
        self.on_home()  # Llama a la función para mostrar la ventana principal

    def close_app(self):
        self.running = False
        try:
            if self.conn:
                self.conn.shutdown(socket.SHUT_RDWR)
                self.conn.close()
        except Exception:
            pass
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass
        self.master.destroy()

class MainApp(tk.Tk):
    """Controla la navegación entre Home y Chat."""
    def __init__(self):
        super().__init__()
        self.title("Chat Translator")
        self.geometry("700x500")
        self.chat_frame = None
        self.show_home()

    def show_home(self):
        if self.chat_frame:
            self.chat_frame.pack_forget()
        self.home_frame = HomeGUI(self, self.start_chat)

    def start_chat(self, username, lang_send, lang_receive, mode):
        self.home_frame.pack_forget()
        self.chat_frame = ChatGUI(self, username, lang_send, lang_receive, mode, self.show_home)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
