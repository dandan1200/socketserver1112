import signal
import os
import sys
import socket
import hashlib
import select

IP = "127.0.0.1"
PORT = int(sys.argv[1])

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP,PORT))
server_socket.listen(1)

sockets_list = [server_socket]
clients = {}
channels = {}

def recieve_message(client_socket):
    try:
        initial_message = client_socket.recv(1024)
        if len(initial_message) > 0:
            return initial_message.decode("utf-8").strip()
        else:
            return False
    except:
        return False

#Use this variable for your loop
daemon_quit = False

#Do not modify or remove this handler
def quit_gracefully(signum, frame):
    global daemon_quit
    daemon_quit = True

def login(msg):
    # Validate msg format
    msg_arr = msg.split(" ")
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
    msg_arr = msg.split(" ")
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

def create_channel(message):
    if message.split(" ")[1] in channels:
        return False
    
    channels[message.split(" ")[1]] = []
    return True

def join_channel(message,user):
    if message.split(" ")[1] in channels:
        if user not in channels[message.split(" ")[1]]:
            channels[message.split(" ")[1]].append(user)
            return True
        else:
            return False
    else:
        return False


def run():
    if os.path.isfile("login_database.csv") == False:
        db = open("login_database.csv","x")
        db.close()
    while True:
        #Do not modify or remove this function call
        signal.signal(signal.SIGINT, quit_gracefully)

        read_sockets, _, exception_sockets = select.select(sockets_list,[],sockets_list)

        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()

                returnkey = ''
                user = recieve_message(client_socket)
                if user is False:
                    continue
                valid = False
                if user.split(" ")[0] == "LOGIN":
                    valid,username = login(user)
                    returnkey = "LOGIN"
                    if valid == True:
                        sockets_list.append(client_socket)
                        clients[client_socket] = username
                        #print("Accepted new connection from {}:{} username: {}".format(client_address[0],client_address[1],username))
                        client_socket.send(("RESULT " + returnkey + " 1\n").encode("utf-8"))
                    else:
                        sockets_list.append(client_socket)
                        clients[client_socket] = "Null"
                        client_socket.send(("RESULT " + returnkey + " 0\n").encode("utf-8"))

                elif user.split(" ")[0] == "REGISTER":
                    valid,username = register(user)
                    returnkey = "REGISTER"
                    if valid == True:
                        sockets_list.append(client_socket)
                        clients[client_socket] = username
                        #("Accepted new connection from {}:{} username: {}".format(client_address[0],client_address[1],username))
                        client_socket.send(("RESULT " + returnkey + " 1\n").encode("utf-8"))
                    else:
                        sockets_list.append(client_socket)
                        clients[client_socket] = "Null"
                        # client_socket.send(user.encode('utf-8'))
                        client_socket.send(("RESULT " + returnkey + " 1\n").encode("utf-8"))
 
            else:
                message = recieve_message(notified_socket)
                if message is False:
                    # print("Closed connection from {}:{} username: {}".format(client_address[0],client_address[1],clients[notified_socket]))
                    sockets_list.remove(notified_socket)
                    try:
                        clients.pop(client_socket)
                    except:
                        continue
                    continue

                username = clients[notified_socket]
                #print("Recieved message from {}:{} ".format(username,message))

                if message.split(" ")[0] == "LOGIN":
                    valid,username = login(message)
                    returnkey = "LOGIN"
                    if valid == True:
                        sockets_list.append(client_socket)
                        clients[client_socket] = username
                        #print("Accepted new connection from {}:{} username: {}".format(client_address[0],client_address[1],username))
                        notified_socket.send(("RESULT " + returnkey + " 1\n").encode("utf-8"))
                    else:
                        notified_socket.send(("RESULT " + returnkey + " 0\n").encode("utf-8"))

                elif message.split(" ")[0] == "REGISTER":
                    valid,username = register(message)
                    returnkey = "REGISTER"
                    if valid == True:
                        sockets_list.append(client_socket)
                        clients[client_socket] = username
                        #print("Accepted new connection from {}:{} username: {}".format(client_address[0],client_address[1],username))
                        notified_socket.send(("RESULT " + returnkey + " 1\n").encode("utf-8"))
                    else:
                        #client_socket.send(message.encode('utf-8'))

                        notified_socket.send(("RESULT " + returnkey + " 0\n").encode("utf-8"))

                elif message.split(" ")[0] == "JOIN":
                    valid = join_channel(message,username)
                    returnkey = "JOIN"
                    if valid == True:
                        notified_socket.send(("RESULT " + returnkey +  " " + message.split(" ")[1] + " 1\n").encode("utf-8"))
                    else:
                        notified_socket.send(("RESULT " + returnkey + " " + message.split(" ")[1] + " 0\n").encode("utf-8"))
                    
                elif message.split(" ")[0] == "CREATE":
                    valid = create_channel(message)
                    returnkey = "CREATE"
                    if valid == True:
                        notified_socket.send(("RESULT " + returnkey + " " + message.split(" ")[1] + " 1\n").encode("utf-8"))
                    else:
                        notified_socket.send(("RESULT " + returnkey + " " + message.split(" ")[1] + " 0\n").encode("utf-8"))

                elif message.split(" ")[0] == "SAY":
                    try:
                        if username in channels[message.split(" ")[1]]:
                            for cs in clients:
                                if cs != notified_socket and clients[cs] in channels[message.split(" ")[1]]:
                                    cs.send(("RECV " + username + " " + message.split(" ")[1] + " " + " ".join(message.split(" ")[2:])).encode('utf-8'))
                        else:
                            notified_socket.send("RESULT SAY 0".encode("utf-8"))
                    except:
                        notified_socket.send("RESULT SAY 0".encode("utf-8"))

                elif message == "CHANNELS":
                    sorted_channels = list(channels.keys())
                    sorted_channels.sort()
                    notified_socket.send("RESULT CHANNELS {}\n".format(", ".join(sorted_channels)).encode("utf-8"))





                # for client_socket in clients:
                #     if client_socket != notified_socket:
                #         client_socket.send((username + message).encode('utf-8'))
        
        


if __name__ == '__main__':
    run()


