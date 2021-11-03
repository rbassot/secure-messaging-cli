#!/usr/bin/env python3

from socket import *
from sqlite3 import * #For future database implementation

from ClientThread import ClientThread


#----- Server Parameters -----
HOST = '0.0.0.0'    #bind to public IP
PORT = 50007
connections = []    #list of all ongoing connections
users = {}          #dictionary of all connected users
client_keys = {}    #dictionary of client keys needed for user authorization


def start_server():

    #create socket connection
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  #allows socket address reuse in a TIME_WAIT state
    sock.bind((HOST, PORT))

    #accept connections to the running server
    sock.listen(10)
    print('Server listening over port: ' + str(PORT))

    while True:
        client_sock, client_addr = sock.accept()

        #handle a connection on a new thread
        print('Connection established to client at address: ', client_addr)
        ClientThread(client_sock, client_addr)
        connections.append(client_sock)
        client_sock.send(b"You are connected from: " + str(client_addr).encode())

        '''while True:
            data = client_sock.recv(1024)
            if not data:
                break

            #temporary - echo back data to the client
            client_sock.sendall(data)'''

    sock.close()
    sys.exit()



if __name__ == "__main__":
    start_server()
