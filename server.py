import socket
import threading

HOST = '0.0.0.0'
PORT = 1234
LISTENER_LIMIT = 5

active_clients = {}
groups = {}

def broadcast_group_update():
    """Send updated group list to all connected clients."""
    groups_list = "~".join(groups.keys())
    message = f"SERVER~GROUPS~{groups_list}"
    for client, _ in active_clients.values():
        send_message_to_client(client, message)

def handle_client(client, username):
    try:
        while True:
            message = client.recv(2048).decode()
            if not message:
                break
            try:
                command, *args = message.split("~")

                if command == "CREATE_GROUP":
                    group_name = args[0]
                    if group_name not in groups:
                        groups[group_name] = []
                        send_message_to_client(client, f"SERVER~Group {group_name} created.")
                        broadcast_group_update()
                    else:
                        send_message_to_client(client, f"SERVER~Group {group_name} already exists.")

                elif command == "FETCH_GROUPS":
                    send_message_to_client(client, f"SERVER~GROUPS~{'~'.join(groups.keys())}")

                elif command == "JOIN_GROUP":
                    group_name = args[0]
                    if group_name in groups:
                        if username not in groups[group_name]:
                            groups[group_name].append(username)
                            active_clients[username] = (client, group_name)
                            send_message_to_client(client, f"SERVER~Joined group {group_name}.")
                            broadcast_message(group_name, "SERVER", f"{username} has joined the group.")
                    else:
                        send_message_to_client(client, f"SERVER~Group {group_name} does not exist.")

                elif command == "LEAVE_GROUP":
                    group_name = active_clients[username][1]
                    if group_name and username in groups[group_name]:
                        groups[group_name].remove(username)
                        send_message_to_client(client, f"SERVER~Left group {group_name}.")
                        broadcast_message(group_name, "SERVER", f"{username} has left the group.")
                        active_clients[username] = (client, None)

                elif command == "SEND_MESSAGE":
                    group_name = active_clients[username][1]
                    if group_name:
                        message_content = args[0]
                        broadcast_message(group_name, username, message_content)

            except Exception as e:
                print(f"Failed to process client message: {e}")
                send_message_to_client(client, "SERVER~Failed to process your message.")
    finally:
        if username in active_clients:
            group_name = active_clients[username][1]
            if group_name and username in groups[group_name]:
                groups[group_name].remove(username)
            del active_clients[username]
        client.close()

def broadcast_message(group_name, sender_username, message_content):
    """Send message to all clients in the specified group."""
    if group_name in groups:
        for username in groups[group_name]:
            client, _ = active_clients.get(username, (None, None))
            if client:
                try:
                    client.sendall(f"{sender_username}~{message_content}".encode())
                except Exception as e:
                    print(f"Failed to send message to {username}: {e}")

def send_message_to_client(client, message):
    try:
        client.sendall(message.encode())
    except Exception as e:
        print(f"Failed to send message: {e}")

def client_handler(client):
    try:
        username = client.recv(2048).decode('utf-8', errors='replace').strip()
        if username and username not in active_clients:
            active_clients[username] = (client, None)
            send_message_to_client(client, f"SERVER~Welcome {username}!")
            threading.Thread(target=handle_client, args=(client, username)).start()
        else:
            send_message_to_client(client, "SERVER~Username already taken or invalid.")
            client.close()
    except Exception as e:
        print(f"Client handler error: {e}")
        client.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((HOST, PORT))
        print(f"Server running on {HOST}:{PORT}")
    except Exception as e:
        print(f"Error: {e}")
        return

    server.listen(LISTENER_LIMIT)
    while True:
        try:
            client, _ = server.accept()
            threading.Thread(target=client_handler, args=(client,)).start()
        except Exception as e:
            print(f"Error accepting client: {e}")

if __name__ == '__main__':
    main()

