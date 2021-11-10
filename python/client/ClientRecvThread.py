#!/usr/bin/env python3

from sys import *
from socket import *
from threading import *
import json
import ast
#from PIL import Image

import config

'''
Basic ClientRecvThread class for the client-side to continually listen to the server.
'''

class ClientRecvThread(Thread):
    def __init__(self, socket, address, event):    #Inherit from Thread class
        Thread.__init__(self)
        self.sock = socket
        self.addr = address
        self.kill_event = event
        #self.username? To determine if the client is logged in, so 'send', etc can be performed


    def listen(self):
        while not self.kill_event:
            try:
                server_data = self.sock.recv(1024)

                #server closed the connection - terminate the threads
                if not(server_data):
                    return 1

            except (KeyboardInterrupt, OSError):
                return 0


    #continuous execution of the receiver thread - function override
    def run(self):
        self.listen()
        return
