# Chat client with DeepL translation (multi-language configurable)

import socket
import threading
import os

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

DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
if not DEEPL_API_KEY:
    raise ValueError("DEEPL_API_KEY environment variable not set")
translator = deepl.Translator(DEEPL_API_KEY)


class HomeGUI(tk.Frame): 
    """Ventana principal (home) para elegir nombre, idioma y modo."""
    def __init__(self, master, on_start_chat):
        super().__init__(master)
        self.master = master
        self.on_start_chat = on_start_chat
        self.pack(padx=20, pady=20)

        LANGUAGES = ["EN", "ES", "FR", "DE", "IT", "PT", "EN-US", "PT-BR"]  # Lista de idiomas válidos

        tk.Label(self, text="Nombre de usuario (solo letras y números):").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack(pady=(0,10))

        # Nuevo: Menú desplegable para idioma de origen
        tk.Label(self, text="Tu idioma (origen):").pack()
        self.lang_send_var = tk.StringVar(value=LANGUAGES[0])
        self.lang_send_menu = tk.OptionMenu(self, self.lang_send_var, *LANGUAGES)
        self.lang_send_menu.pack(pady=(0,10))

        # Nuevo: Menú desplegable para idioma destino
        tk.Label(self, text="Idioma del otro usuario (destino):").pack()
        self.lang_receive_var = tk.StringVar(value=LANGUAGES[1])
        self.lang_receive_menu = tk.OptionMenu(self, self.lang_receive_var, *LANGUAGES)
        self.lang_receive_menu.pack(pady=(0,10))

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
        lang_send = self.lang_send_var.get()  # Nuevo: obtener idioma de origen del OptionMenu
        lang_receive = self.lang_receive_var.get()  # Nuevo: obtener idioma destino del OptionMenu
        if not lang_send or not lang_receive:
            messagebox.showerror("Error", "Debes seleccionar ambos idiomas.")
            return
        mode = self.mode_var.get()
        self.on_start_chat(username, lang_send, lang_receive, mode)

class ChatGUI(tk.Frame):
    """Ventana de chat con DeepL y botones extra."""
    def __init__(self, master, username, lang_send, lang_receive, mode, on_home):
        super().__init__(master)
        self.master = master
        self.username = username
        self.lang_send = self.validate_language(lang_send)
        self.lang_receive = self.validate_language(lang_receive)
        self.mode = mode
        self.on_home = on_home
        self.sock = None
        self.conn = None
        self.running = False
        self.is_server = (mode == "1")
        self.pack(padx=10, pady=10, fill="both", expand=True)

        # Nuevo: Mostrar rol, nombre de usuario y idioma seleccionado en la parte superior
        rol = "Servidor" if self.is_server else "Cliente"
        info_text = (
            f"Modo: {rol} | Usuario: {self.username} | "
            f"Tu idioma: {self.lang_send.upper()} | Idioma del otro usuario: {self.lang_receive.upper()}"
        )
        self.info_label = tk.Label(self, text=info_text, font=("Arial", 12, "bold"), fg="blue")
        self.info_label.pack(pady=(0, 5))
        # Fin de bloque nuevo

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
    # Refactorizar la lógica de traducción cliente-servidor para que sea más clara y escalable:
    # 1. Separar los conceptos de idioma de escritura (lo que yo envío) e idioma de recepción (lo que yo quiero entender).
    #    - Usar variables como my_lang_out (yo escribo) y my_lang_in (yo recibo).
    #    - Para el otro usuario, usar peer_lang_out y peer_lang_in.
    # 2. Toda traducción debe ir de peer_lang_out → my_lang_in cuando recibo, y de my_lang_out → peer_lang_in cuando envío.
    # 3. Validar que los idiomas ingresados estén dentro de una lista de idiomas válidos para DeepL.
    # 4. Manejar errores de traducción o clave API inválida con mensajes claros al usuario.
    # 5. Mantener el texto original visible junto al traducido para trazabilidad.
    # Implementar estas mejoras en la función send_message() y receive_messages().
    def validate_language(self, lang):
        """Valida que el idioma esté en la lista de idiomas soportados por DeepL."""
        valid_languages = [
            "EN",
            "EN-US",
            "ES",
            "FR",
            "DE",
            "IT",
            "NL",
            "PL",
            "PT",
            "PT-BR",
            "RU",
            "ZH",
        ]
        if lang.upper() not in valid_languages:
            raise ValueError(f"Idioma no soportado: {lang}. Debe ser uno de {valid_languages}.")
        return lang.upper()

    def send_message(self):
        if not self.conn or not self.running:
            self.append_text("🔴 No conectado.")
            return
        msg = self.entry.get()
        if not msg:
            return
        translated, _ = translate_message(msg, self.lang_receive)
        try:
            self.conn.send(translated.encode("utf-8"))
            self.append_text(f"{self.username}: {msg}")
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
                translated, _ = translate_message(message_decoded, self.lang_send)
                self.append_text(f"\n💬 Original: {message_decoded}")
                if translated != message_decoded:
                    self.append_text(f"🌍 Traducido: {translated}")
            except Exception as e:
                self.append_text(f"🔴 Error recibiendo: {e}")
                self.running = False
                self.send_button.config(state=tk.DISABLED)
                break

    def append_text(self, text):
        # Siempre actualizar la interfaz desde el hilo principal
        if self.text_area.winfo_exists():
            self.text_area.after(0, self._append_text_safe, text)

    def _append_text_safe(self, text):
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
            self.chat_frame.pack_forget()  # Oculta el chat, pero no lo destruye
        self.home_frame = HomeGUI(self, self.start_chat)

    def start_chat(self, username, lang_send, lang_receive, mode):
        self.home_frame.pack_forget()
        self.chat_frame = ChatGUI(self, username, lang_send, lang_receive, mode, self.show_home)

def translate_message(text, target_lang):
    """
    Traduce el mensaje al idioma objetivo y devuelve una tupla con el
    texto traducido y el idioma detectado. Si no se requiere traducción o
    ocurre un error, se devuelve el texto original y el idioma detectado o
    ``None``.
    """
    target = target_lang.upper()
    if target == "EN":
        target = "EN-US"
    try:
        result = translator.translate_text(text, target_lang=target)
        detected = result.detected_source_lang.upper()
        if detected == "EN":
            detected = "EN-US"
        if detected == target:
            return text, detected
        return result.text, detected
    except Exception:
        return text, None

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
