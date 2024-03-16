#!/bin/python
import signal
import os
import sys
import socket
import hashlib
import select

# Start server
port = int(sys.argv[1])
server_address = ('', port)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR, 1)
server_socket.bind(server_address)
server_socket.listen()

sockets_list = [server_socket]

clients = {}

def recieve_message(client_socket):
    try:
        input_msg = client_socket.recv(1024).decode()
        if input_msg.split(":")[0] == "LOGIN":
            valid,username = login(input_msg)
            if valid:
                print("Successful login: " + str(username))
                return username
                
            else:
                return 'invalid'
                

        elif input_msg.split(":")[0] == "REGISTER":
            valid,username = register(input_msg)
            if valid:
                print("Successful register: " + str(username))
            else:
                return 'invalid'
        else:
            return input_msg
    except:
        return False

def login(msg):
    # Validate msg format
    msg_arr = msg.split(":")
    if len(msg_arr) != 3:
        return False,""
    else:
        username = msg_arr[1]
        password = msg_arr[2]
        with open("login_database.csv", 'r') as db:
            for login in db.readlines():
                if login.split(",")[0] == username:
                    print(str(login.split(",")[1]).strip("\n") + '\n' + str(hashlib.sha256(password.encode('utf-8')).digest()))
                    if str(hashlib.sha256(password.encode('utf-8')).digest()) == str(login.split(",")[1]).strip("\n"):
                        return True,username
        return False,username

def register(msg):
    msg_arr = msg.split(":")
    if len(msg_arr) != 3:
        return False,""
    else:
        username = msg_arr[1]
        password = msg_arr[2]
        with open("login_database.csv", 'r') as db:
            for x in db.readlines():
                if x.split(",")[0] == username:
                    return False,""

        with open("login_database.csv", 'a') as db:
            db.write(username + ","+ str(hashlib.sha256(password.encode('utf-8')).digest()) + "\n")
        return True,username

#Use this variable for your loop
daemon_quit = False

#Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True



def run():
    #Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)

    if os.path.isfile("login_database.csv") == False:
        db = open("login_database.csv","x")
        db.close()

    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                
                user = recieve_message(server_socket)
                print(user)
                if user == 'invalid':
                    client_socket.send("0\n".encode())
                    continue
                elif user == False:
                    continue
                
                sockets_list.append(client_socket)

                clients[client_socket] = user
                
                print(f"Accepted new connection from {client_address[0]}:{client_address[1]} username: {user}")
            else:
                message = recieve_message(notified_socket)

                if message is False:
                    print(f"Closed connection from {clients[notified_socket]}")
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    continue
                
                user = clients[notified_socket]
                print(f"Recieved message from {user}: {message}")

                for client_socket in clients:
                    if client_socket != notified_socket:
                        client_socket.send((user + ": " + message).encode())
        
        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            del clients[notified_socket]
    


if __name__ == '__main__':
    run()