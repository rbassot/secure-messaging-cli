#!/usr/bin/env python3

from socket import *
from sqlite3 import * #For future database implementation

import config
from ServerThread import ServerThread


#----- Server Parameters -----
HOST = '0.0.0.0'    #bind to public IP
PORT = 50007
connections = []    #list of all ongoing connections
#users = {}          #dictionary of all connected users
client_keys = {}    #dictionary of client keys needed for user authorization


def start_server():
    '''
    Start the main server thread to accept client connections. This thread accepts
    TCP socket connections over Port 50007. This function spawns child threads
    (SendThread) that are dedicated to handling the requests of a single client.

    An initial connection message is also sent to the client-side.
    This main thread never terminates, and must be terminated from the console.

    Parameters
    ----------
    None

    Returns
    ----------
    None
    '''

    #create socket connection
    sock = socket(AF_INET, SOCK_STREAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  #allows socket address reuse in a TIME_WAIT state
    sock.bind((HOST, PORT))

    #accept connections to the running server
    sock.listen(10)
    print('Server listening over port: ' + str(PORT))

    while True:
        client_sock, client_addr = sock.accept()

        #handle a connection on a new ClientThread
        print('Connection established to client at address: ' + str(client_addr))

        #spawn a server thread obj dedicated to the client
        ServerThread(client_sock, client_addr)
        #config.connections.append(client_sock)
        client_sock.send(b"You are connected from: " + str(client_addr).encode())

    #unreachable - how do we gracefully terminate the server? Do we even want to do this?
    sock.close()
    sys.exit()



if __name__ == "__main__":
    start_server()
