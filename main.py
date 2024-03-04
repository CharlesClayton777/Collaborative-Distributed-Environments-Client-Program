# Import required modules and advise user to retry if fails
#This is the client program run this second.

try:
    import socket
    import json
    import threading
    import tkinter as tk
    from tkinter import scrolledtext, filedialog
    from datetime import datetime
except ImportError:
    raise ImportError('Failed to start, close and retry')


# Connect to the chat server
def connect_to_server(host='127.0.0.1', port=8888,
                      name=""):  # Accept custom IP and Port or default to IP 127.0.0.1 and port 8888
    global client_socket
    client_socket = socket.socket(socket.AF_INET,
                                  socket.SOCK_STREAM)  # Create a dictionary set of socket data using the socket library
    client_socket.connect((host, port))  # Connect to the server using the library functionality and set server / port
    client_socket.send(name.encode())
    return client_socket


def send_file(file_path):
    with open(file_path, "rb") as file:
        file_data = file.read()
    header = {"type": "file",
              "filename": file_path.split("/")[-1],
              "length": len(file_data)
              }
    client_socket.send(json.dumps(header).encode())
    client_socket.sendall(file_data)


def choose_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        send_file(file_path)


def receive_file(client_socket, data_length):
    message_display.insert("end", f"[{message['timestamp']}] {message['name']}: sending file: {message['text']}\n")
    message_display.see("end")
    window.update()
    data = b''
    while len(data) < data_length:
        packet = client_socket.recv(1024)
        if not packet:
            break
        data += packet
    return data


# Function to save received file data
def save_file(client_name, file_data):
    file_path = f'received_files/{client_name}_{datetime.now().strftime("%Y%m%d%H%M%S")}'
    with open(file_path, 'wb') as file:
        file.write(file_data)
    print(f"File received and saved to {file_path}")


# Function to set the user's name
def set_name():
    # Create a global app variable and get it from the input
    name = name_entry.get()
    # Disable the name input and remove submit button
    name_entry.config(state="disabled")
    name_button.pack_forget()
    # Format the name data and send it
    client_socket.send(name.encode())
    timestamp = datetime.now().strftime("%H:%M:%S")  # Format timestamp to hour:min:sec
    # Update the message screen
    message_display.delete("end")
    message_display.insert("end", f"[{timestamp}] Welcome to the chat {name}\n", "system")
    message_display.see("end")
    window.update()


# Function to receive and display messages from the server
def receive_messages():
    # Continuous loop
    while True:
        # Assign data dictionary based on received data
        data = client_socket.recv(1024)
        # if no data received, break out of function
        if not data:
            break
        # Decode the JSON message
        message = json.loads(data.decode())
        message_type = message["type"]
        message_length = message["length"]

        if message_type == "text":
            # Update the message screen
            message_display.insert("end", f"[{message['timestamp']}] {message['name']}: {message['text']}\n")
            message_display.see("end")
            window.update()

        elif message_type == "file":
            file_data = receive_file(client_socket, message_length)
            save_file(client_name, file_data)


# Function to send message to server
def send_message():
    message_text = message_entry.get()  # Get message on click
    if message_text:  # Checks if a message text exists
        message = {"text": message_text, "type": "text"}
        # Send the message encoded in JSON format
        client_socket.send(json.dumps(message).encode())
        # Create a timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")  # Format timestamp to hour:min:sec
        # Update the message screen
        message_display.insert("end", f"[{timestamp}] You: {message['text']}\n", "sender")
        message_display.see("end")
        message_entry.delete(0, "end")
        window.update()


def create_windows():
    # Create a tkinter window
    global window
    global name_entry, name_button, message_display, message_entry
    window = tk.Tk()
    window.title("Chat Client")

    # Create a frame for name input
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

    # Create a scrolled text widget to display messages
    message_display = scrolledtext.ScrolledText(window, wrap=tk.WORD)
    message_display.tag_config('sender', foreground="#228B22")
    message_display.tag_config('system', foreground="#FF5733")
    message_display.pack(fill="both", expand=True)

    # Create an entry widget for typing messages
    message_entry = tk.Entry(window)
    message_entry.pack(fill="x")

    # Create a send button to send messages
    send_button = tk.Button(window, text="Send", command=send_message)
    send_button.pack()

    # Set the initial state of name entry and button
    name = ""
    name_entry.config(state="normal")
    name_button.config(state="normal")


def start_daemon_thread():
    global message_thread
    message_thread = threading.Thread(target=receive_messages)
    message_thread.daemon = True
    message_thread.start()
    return message_thread


def handle_cleanup():
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()


def main():
    try:
        connect_to_server()
        create_windows()
        start_daemon_thread()
        # Loop the program until exit
        while True:
            window.mainloop()
    finally:
        handle_cleanup()


if __name__ == '__main__':
    main()

