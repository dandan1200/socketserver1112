import socket
import select
import errno

PORT = 8080
SERVER = ""

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER,PORT))
client_socket.setblocking(False)

message = ''

while True:
    message = input("Input: ")
    message = message.encode("utf-8")
    client_socket.send(message)
    try: 
        while True:
            rmsg = client_socket.recv(1024)
            print(rmsg.decode("utf-8"))
    
    except:
        pass


