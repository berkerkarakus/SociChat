import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog

HOST = '127.0.0.1'
PORT = 1234
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

DARK_GREY = '#121212'
MEDIUM_GREY = '#1F1B24'
OCEAN_BLUE = '#464EB8'
WHITE = "white"
FONT = ("Helvetica", 17)
BUTTON_FONT = ("Helvetica", 15)
SMALL_FONT = ("Helvetica", 13)

username = None
current_group = None
groups = []

def connect_to_server():
    try:
        client.connect((HOST, PORT))
        print("Successfully connected to the server")
        return True
    except:
        messagebox.showerror("Connection Error", f"Cannot connect to server {HOST}:{PORT}")
        return False

def listen_for_messages():
    while True:
        try:
            message = client.recv(2048).decode()
            if message:
                handle_server_message(message)
        except Exception as e:
            print(f"Error listening for messages: {e}")
            break

def handle_server_message(message):
    global groups

    if message.startswith("SERVER~GROUPS~"):
        groups_list = message.split("~")[2:]
        groups = groups_list if groups_list[0] != "" else []
        update_groups_frame()
    elif message.startswith("SERVER~"):
        server_message = message.replace("SERVER~", "").strip()
        add_message(f"Server: {server_message}")
    else:
        try:
            sender, content = message.split("~", 1)
            add_message(f"{sender}: {content}")
        except ValueError:
            print(f"Invalid message format: {message}")

def send_message_to_server(message):
    try:
        if message:
            client.sendall(message.encode())
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send message: {e}")

def fetch_groups():
    send_message_to_server("FETCH_GROUPS")

def create_group():
    group_name = simpledialog.askstring("Create Group", "Enter a name for the group:")
    if group_name:
        send_message_to_server(f"CREATE_GROUP~{group_name}")

def join_group(group_name):
    global current_group
    if group_name:
        send_message_to_server(f"JOIN_GROUP~{group_name}")
        current_group = group_name
        chat_label.config(text=f"Chat: {group_name}")
        chat_window.config(state=tk.NORMAL)
        chat_window.delete(1.0, tk.END)
        chat_window.config(state=tk.DISABLED)

def leave_group():
    global current_group
    if current_group:
        send_message_to_server("LEAVE_GROUP")
        current_group = None

def send_message():
    message = message_entry.get()
    if message:
        send_message_to_server(f"SEND_MESSAGE~{message}")

        message_entry.delete(0, tk.END)
def update_groups_frame():
    for widget in groups_frame.winfo_children():
        widget.destroy()

    if not groups:
        empty_label = tk.Label(groups_frame, text="No groups available.", font=FONT, bg=MEDIUM_GREY, fg=WHITE)
        empty_label.pack(pady=20)
    else:
        for group in groups:
            group_frame = tk.Frame(groups_frame, bg=MEDIUM_GREY)
            group_frame.pack(fill=tk.X, pady=5)

            group_label = tk.Label(group_frame, text=group, font=FONT, bg=MEDIUM_GREY, fg=WHITE)
            group_label.pack(side=tk.LEFT, padx=10)

            join_button = tk.Button(group_frame, text="Join", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE,
                                    command=lambda g=group: on_join_group(g))
            join_button.pack(side=tk.RIGHT, padx=10)

def on_join_group(group_name):
    join_group(group_name)
    main_frame.pack_forget()
    chat_frame.pack(expand=True, fill=tk.BOTH)

def add_message(message):
    chat_window.config(state=tk.NORMAL)
    chat_window.insert(tk.END, message + "\n")
    chat_window.config(state=tk.DISABLED)

def return_to_main_menu():
    leave_group()  # Kullanıcı gruptan çıkıyor
    chat_frame.pack_forget()
    main_frame.pack(expand=True, fill=tk.BOTH)
    fetch_groups()

def login():
    global username
    username = simpledialog.askstring("Login", "Enter your username:")
    if username:
        if connect_to_server():
            send_message_to_server(username)
            threading.Thread(target=listen_for_messages, daemon=True).start()
            root.deiconify()
            main_frame.pack(expand=True, fill=tk.BOTH)
            fetch_groups()
        else:
            root.quit()
    else:
        messagebox.showerror("Error", "Username is required!")
        root.quit()

root = tk.Tk()
root.geometry("800x600")
root.title("Chat Application")
root.withdraw()

main_frame = tk.Frame(root, bg=MEDIUM_GREY)

groups_label = tk.Label(main_frame, text="Groups", font=FONT, bg=MEDIUM_GREY, fg=WHITE)
groups_label.pack(side=tk.TOP, pady=5)

groups_frame = tk.Frame(main_frame, bg=MEDIUM_GREY)
groups_frame.pack(fill=tk.BOTH, expand=True)

create_group_button = tk.Button(main_frame, text="Create New Group", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE,
                                command=create_group)
create_group_button.pack(side=tk.BOTTOM, pady=10)

chat_frame = tk.Frame(root, bg=DARK_GREY)
chat_label = tk.Label(chat_frame, text="Chat", font=FONT, bg=DARK_GREY, fg=WHITE)
chat_label.pack(side=tk.TOP, pady=10)

chat_window = scrolledtext.ScrolledText(chat_frame, font=SMALL_FONT, bg=MEDIUM_GREY, fg=WHITE)
chat_window.pack(expand=True, fill=tk.BOTH)

message_entry = tk.Entry(chat_frame, font=FONT, bg=MEDIUM_GREY, fg=WHITE, width=40)
message_entry.pack(side=tk.LEFT, padx=10)

send_button = tk.Button(chat_frame, text="Send", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE, command=send_message)
send_button.pack(side=tk.LEFT, padx=10)

main_menu_button = tk.Button(chat_frame, text="Main Menu", font=BUTTON_FONT, bg=OCEAN_BLUE, fg=WHITE,
                              command=return_to_main_menu)
main_menu_button.pack(side=tk.LEFT, padx=10)

if __name__ == "__main__":
    login()
    root.mainloop()

