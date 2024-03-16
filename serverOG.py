#!/bin/python
import signal
import os
import sys
import socket
import hashlib


#Use this variable for your loop
daemon_quit = False

#Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True


def open_server():
    port = int(sys.argv[1])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('', port)
    sock.bind(server_address)
    sock.listen()
    return sock

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


def get_connections(sock):
    activeConnections = {}
    while True:
        
        connection, client_address = sock.accept()
        print(len(activeConnections))
        try:
            input_msg = connection.recv(1024).decode().strip("\n")
            if input_msg.split(":")[0] == "LOGIN":
                valid,username = login(input_msg)
                if valid:
                    activeConnections.update({username : (connection,client_address)}) 
                    activeConnections.get(username)[0].send('1\n'.encode())
                    print("Successful login: " + str(username) + " " + str(client_address))
                else:
                    connection.send('0\n'.encode())

            elif input_msg.split(":")[0] == "REGISTER":
                valid,username = register(input_msg)
                if valid:
                    activeConnections.update({username:(connection,client_address)}) 
                    activeConnections.get(username)[0].send('1\n'.encode())
                else:
                    connection.send('0\n'.encode())
                
            elif input_msg == "DC":
                activeConnections.pop(connection)
                connection.close()
        finally:
            pass





def run():
    #Do not modify or remove this function call
    signal.signal(signal.SIGINT, quit_gracefully)

    # Call your own functions from within 
    # the run() funcion


    #Check DB exists
    if os.path.isfile("login_database.csv") == False:
        db = open("login_database.csv","x")
        db.close()
        
    # Start server for listening
    sock = open_server()

    # Get connection and messages
    get_connections(sock)



    


if __name__ == '__main__':
    run()


