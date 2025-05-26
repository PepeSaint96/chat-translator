# Chat client with DeepL translation (multi-language configurable)

import socket
import threading
import deepl

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

# Ask user for language preferences in English
print("Example language codes: EN-US (English US), EN-GB (English UK), ES (Spanish), FR (French), DE (German), etc.")
LANG_SEND = input("What is your language? (messages you WRITE and want to READ in): ").strip().upper()
LANG_RECEIVE = input("What language does the other user write in? (messages you RECEIVE): ").strip().upper()

DEEPL_API_KEY = "f9b2a1b9-34b1-40dc-997e-a22089c17457:fx"
translator = deepl.Trancleaslator(DEEPL_API_KEY)

# Connect to server
print("Both computers must be connected to the same network (WiFi or LAN).")
mode = input("Enter 1 for Server or 2 for Client: ").strip()

if mode == "1":
    # --- SERVER MODE ---
    IP_LOCAL = get_local_ip()
    print(f"🟢 Server will listen on local IP: {IP_LOCAL}:12345")
    HOST = '0.0.0.0'
    PORT = 12345

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print("Server started. Waiting for connections...")

    while True:
        try:
            client_socket, client_address = server.accept()
            print(f"🟢 Accepted connection from {client_address}")

            def handle_client(client_socket):
                while True:
                    try:
                        message = client_socket.recv(1024)
                        if not message:
                            print("🔴 Connection closed by client.")
                            break
                        message_decoded = message.decode('utf-8')
                        translated = translator.translate_text(
                            message_decoded,
                            source_lang=LANG_RECEIVE,
                            target_lang=LANG_SEND
                        )
                        print(f"\n💬 Original: {message_decoded}")
                        print(f"🌍 Translated: {translated.text}")
                    except Exception as e:
                        print("🔴 Error receiving:", e)
                        break
                client_socket.close()
                print(f"🔴 Connection closed from {client_address}")

            client_handler = threading.Thread(target=handle_client, args=(client_socket,))
            client_handler.start()

        except Exception as e:
            print("🔴 Error accepting connection:", e)

else:
    # --- CLIENT MODE ---
    HOST = input("Enter the IP address of the other computer (server): ")
    PORT = 12345

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print("\n🚀 Connected to server.")

    # Listen and translate messages
    def receive():
        while True:
            try:
                message = client.recv(1024)
                if not message:
                    print("🔴 Connection closed by server.")
                    break
                message_decoded = message.decode('utf-8')
                translated = translator.translate_text(
                    message_decoded,
                    source_lang=LANG_RECEIVE,
                    target_lang=LANG_SEND
                )
                print(f"\n💬 Original: {message_decoded}")
                print(f"🌍 Translated: {translated.text}")
            except Exception as e:
                print("🔴 Error receiving:", e)
                break
        client.close()

    # Start thread to listen for messages
    thread = threading.Thread(target=receive)
    thread.start()

    # Send messages
    while True:
        try:
            msg = input("You: ")
            if msg.lower() in ["exit", "salir", "quit"]:
                try:
                    client.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                client.close()
                break
            client.send(msg.encode('utf-8'))
        except Exception as e:
            print("🔴 Error sending message:", e)
            break
