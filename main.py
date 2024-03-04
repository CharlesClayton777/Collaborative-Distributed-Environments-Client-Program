# Start the Server program first, then start the Client Program
# Import required modules and advise user to retry if fails
try:
    import socket
    import json
    import threading
    import tkinter as tk
    from tkinter import scrolledtext
    from datetime import datetime
except ImportError:
    raise ImportError('Failed to start, close and retry')


# Connect to the chat server
def connect_to_server(host='127.0.0.1',
                      port=8888):  # Accept custom IP and Port or default to IP 127.0.0.1 and port 8888
    global client_socket
    client_socket = socket.socket(socket.AF_INET,
                                  socket.SOCK_STREAM)  # Create a dictionary set of socket data using the socket library
    client_socket.connect((host, port))  # Connect to the server using the library functionality and set server / port
    return client_socket


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

        # Update the message screen
        message_display.insert("end", f"[{message['timestamp']}] {message['name']}: {message['text']}\n")
        message_display.see("end")
        window.update()


# Function to send message to server
def send_message():
    message_text = message_entry.get()  # Get message on click
    if message_text:  # Checks if a message text exists
        message = {"text": message_text}
        # Send the message encoded in JSON format
        client_socket.send(json.dumps(message).encode())
        # Create a timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")  # Format timestamp to hour:min:sec
        # Update the message screen
        message_display.insert("end", f"[{timestamp}] You: {message['text']}\n", "sender")
        message_display.see("end")
        message_entry.delete(0, "end")
        window.update()



