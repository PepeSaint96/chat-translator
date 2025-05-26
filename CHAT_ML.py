# Chat client with DeepL translation (multi-language configurable)

import socket
import threading
import deepl

# Ask user for language preferences in English
print("Example language codes: EN-US (English US), EN-GB (English UK), ES (Spanish), FR (French), DE (German), etc.")
LANG_SEND = input("What is your language? (messages you WRITE and want to READ in): ").strip().upper()
LANG_RECEIVE = input("What language does the other user write in? (messages you RECEIVE): ").strip().upper()

DEEPL_API_KEY = "f9b2a1b9-34b1-40dc-997e-a22089c17457:fx"
translator = deepl.Translator(DEEPL_API_KEY)

# Connect to server
print("Both computers must be connected to the same network (WiFi or LAN).")
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
