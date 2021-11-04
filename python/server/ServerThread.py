#!/usr/bin/env python3

from socket import *
from threading import *
import json
import ast
#from PIL import Image

'''
Basic ClientThread class for server-side handling of multiple threads.
'''

class ServerThread(Thread):
    def __init__(self, socket, address):    #Inherit from Thread class
        Thread.__init__(self)
        print("New client thread created")
        self.sock = socket
        self.addr = address
        self.start()


    def handle_login_req(self, client_username, client_password):
        #temporary check if username/login can be read from data
        #should instead query the database to retrieve a single tuple
        response = ""
        if(client_username == 'username' and client_password == 'password'):
            response = "{'response':'SUCCESS', 'message':'Successfully logged in.'}"
        else:
            response = "{'response':'FAILURE', 'message':'Login was not successful!'}"

        serialized_resp = json.dumps(response).encode()
        self.sock.send(serialized_resp)


    def new_connection(self):
        while True:
            try:
                client_data = self.sock.recv(1024)

            except:
                pass

            client_req = json.loads(client_data.decode())
            client_req = ast.literal_eval(client_req)

            print(isinstance(client_req, dict))
            print(client_req)
            print("Client sent request for: " + client_req['command'])

            if(client_req['command'] == 'login'):
                self.handle_login_req(client_req['username'], client_req['password'])

            #To implement
            elif(client_req['command'] == 'register'):
                pass


    #continuous execution of the thread
    def run(self):

        #authentication needs to be done first??
        #accept connection from client
        self.new_connection()

        while True:
            try:
                client_data = self.sock.recv(1024)

                #Image displaying with Pillow module
                #im = Image.open(r"C:\Users\Rbass\Documents\earbuds.jpg") 
                #im.show()
                print("Client sent: " + client_data.decode())
                response_msg = "You sent me some data"
                self.sock.send(response_msg.encode())

            except Exception as e:

                #thread exit case
                if(not client_data):
                    #must handle closing connection/removing conn object
                    break