# Import required modules and advise user to retry if fails
# This is the client program run this second.
# Client

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    import socket
    import json
    import threading
    import tkinter as tk
    from tkinter import scrolledtext, filedialog
    from datetime import datetime
except ImportError:
    raise ImportError('Failed to start, close and retry')

# Generate a fixed key (for demonstration purposes)
encryption_key = b'ThisIsASecretKey'

# Connect to the chat server
def connect_to_server(host='127.0.0.1', port=8888, name=""):
    try:
        global client_socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        client_socket.send(name.encode())
        return client_socket
    except Exception as e:
        print(f"Error connecting to server: {e}")


def send_file(file_path):
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Broadcast "preparing to send file" message
        message = {"timestamp": timestamp, "name": name, "text": "Sending file...", "type": "text",
                   "length": 0}
        client_socket.send(json.dumps(message).encode())

        with open(file_path, "rb") as file:
            file_data = file.read()
        header = {"timestamp": timestamp,
                  "name": name,
                  "text": '',
                  "type": "file",
                  "filename": file_path.split("/")[-1],
                  "length": len(file_data)
                  }
        client_socket.send(json.dumps(header).encode())
        client_socket.sendall(file_data)
    except Exception as e:
        print(f"Error sending file: {e}")


def choose_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        send_file(file_path)


def receive_file(client_socket, message):
    filename = message['filename']
    message_display.insert("end", f"[{message['timestamp']}] {message['name']}: sending file: {filename}\n")
    message_display.see("end")
    window.update()
    data = b''
    while len(data) < message['length']:
        packet = client_socket.recv(1024)
        if not packet:
            break
        data += packet
    return data


# Function to save received file data
def save_file(message, file_data):
    name = message['name']
    filename = message['filename']
    file_path = f'received_files/{name}_{datetime.now().strftime("%Y%m%d%H%M%S")} {filename}'
    with open(file_path, 'wb') as file:
        file.write(file_data)
    print(f"File received and saved to {file_path}")


# Function to set the user's name
disallowed_names = ["Admin", "Server", "Moderator"]  # List of disallowed names


def set_name():
    global name
    name = name_entry.get()

    if name.strip() == "":
        # Handle empty name
        # You can display a message or take any other action here
        return

    if name in disallowed_names:
        # Handle disallowed names
        # You can display a message or take any other action here
        return

    # Disable the name input and remove submit button
    name_entry.config(state="disabled")
    name_button.pack_forget()

    # Format the name data and send it
    client_socket.send(name.encode())

    timestamp = datetime.now().strftime("%H:%M:%S")
    message_display.delete("end")
    message_display.insert("end", f"[{timestamp}] Welcome to the chat {name}\n", "system")
    message_display.see("end")
    window.update()


# Function to receive and display messages from the server
def receive_messages():
    while True:
        data = client_socket.recv(1024)
        if not data:
            break
        # Split the received data into IV and encrypted message
        iv = data[:AES.block_size]
        encrypted_message = data[AES.block_size:]
        cipher = AES.new(encryption_key, AES.MODE_CBC, iv)  # Create AES cipher with IV
        decrypted_message = unpad(cipher.decrypt(encrypted_message), AES.block_size)  # Decrypt and unpad the message
        message = json.loads(decrypted_message.decode())  # Decode JSON message
        # Handle the message as usual
        message_type = message["type"]
        message_length = message["length"]

        if message_type == "text":
            # Update the message screen
            message_display.insert("end", f"[{message['timestamp']}] {message['name']}: {message['text']}\n")
            message_display.see("end")
            window.update()

        elif message_type == "file":
            file_data = receive_file(client_socket, message)
            save_file(message, file_data)


# Function to send message to server
import time

# Add global variables for rate limiting
last_message_time = 0
message_limit_interval = 0  # Allow one message every 100 seconds
message_limit_count = 0  # Allow a maximum of 100 messages within the interval


# Function to send message to server
def send_message():
    global last_message_time

    # Check if rate limit is exceeded
    current_time = time.time()
    if current_time - last_message_time < message_limit_interval:
        print("Message rate limit exceeded. Please wait before sending another message.")
        return

    message_text = message_entry.get()  # Get message on click

    # Check if message length exceeds limit
    if len(message_text) > 200:  # Adjust the message length limit as needed
        print("Message length limit exceeded. Please keep your message within 200 characters.")
        return

    if message_text:  # Checks if a message text exists
        # Update last message time
        last_message_time = current_time

        # Create a timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")  # Format timestamp to hour:min:sec
        message = {"timestamp": timestamp, "name": name, "text": message_text, "type": "text",
                   "length": len(message_text)}
        # Send the message encoded in JSON format
        client_socket.send(json.dumps(message).encode())

        # Update the message screen
        message_display.insert("end", f"[{timestamp}] You: {message['text']}\n", "sender")
        message_display.see("end")
        message_entry.delete(0, "end")
        window.update()


def create_windows():
    global window
    global name_entry, name_button, message_display, message_entry
    window = tk.Tk()
    window.title("Chat Client")

    name_frame = tk.Frame(window)
    name_frame.pack(fill="x")

    name_label = tk.Label(name_frame, text="Enter your name:")
    name_label.pack(side="left")

    name_entry = tk.Entry(name_frame)
    name_entry.pack(side="left")

    name_button = tk.Button(name_frame, text="Set Name", command=set_name)
    name_button.pack(side="left")

    send_file_button = tk.Button(window, text="Send File", command=choose_file)
    send_file_button.pack()


    message_display = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    message_display.tag_config('sender', foreground="#228B22")
    message_display.tag_config('system', foreground="#FF5733")
    message_display.pack(fill="both", expand=True)

    message_entry = tk.Entry(window)
    message_entry.pack(fill="x")

    send_button = tk.Button(window, text="Send", command=send_message)
    send_button.pack()

    theme_button = tk.Button(window, text="Toggle Theme", command=toggle_theme)
    theme_button.pack()


def start_daemon_thread():
    global message_thread
    message_thread = threading.Thread(target=receive_messages)
    message_thread.daemon = True
    message_thread.start()
    return message_thread


def handle_cleanup():
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()


def toggle_theme():
    current_bg = window.cget("bg")
    if current_bg == "white":
        # Switch to dark theme
        window.configure(bg="grey")
        message_display.configure(bg="grey", fg="white")
        message_entry.configure(bg="grey", fg="white")
    else:
        # Switch to light theme
        window.configure(bg="white")
        message_display.configure(bg="white", fg="black")
        message_entry.configure(bg="white", fg="black")


def main():
    try:
        connect_to_server()
        create_windows()
        start_daemon_thread()
        while True:
            window.mainloop()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        handle_cleanup()


if __name__ == '__main__':
    main()

