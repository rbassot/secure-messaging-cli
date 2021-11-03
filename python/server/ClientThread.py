#!/usr/bin/env python3

import socket
from threading import *

'''
Basic ClientThread class for server-side handling of multiple threads.
'''

class ClientThread(Thread):
    def __init__(self, socket, address):    #Inherit from Thread class
        Thread.__init__(self)
        print("New client thread created")
        self.sock = socket
        self.addr = address
        self.start()

    #continuous execution of the thread
    def run(self):
        while True:
            try:
                client_data = self.sock.recv(1024)
                print("Client sent: " + client_data.decode())
                response_msg = "You sent me some data"
                self.sock.send(response_msg.encode())

            except Exception as e:

                #thread exit case
                if(not client_data):
                    #must handle closing connection/removing conn object
                    break