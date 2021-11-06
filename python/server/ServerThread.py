#!/usr/bin/env python3

from sys import *
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
        #self.username? To determine if the client is logged in, so 'send', etc can be performed
        self.start()


    def handle_send_message(self, encr_message, send_client, recv_client, image_attached):
        #implement receiving a message from sender and forwarding to the receiver
        #-user authenticity established before this point (via digital signature)
        #-message is encrypted by sender (SHA256?) and can only be decrypted by receiver (via private key?) once received
        #-every new encrypted message should be added to storage at the server *TWICE*:
        #     -->Once from perspective of the sender & Again from the perspective of the receiver (send/recv users are swapped)
        #     -->This will allow one user to delete their message history w/o affecting the other's
        #     (potentially include pre-populated DB with some messages)
        #-**optional** should a receiving user NOT be online, the server should still store the message and notify the sender.
        #   Then, upon connection of the receiving user to the server, the waiting encrypted message should be forwarded
        pass

    
    def handle_registration(self, client_username, client_password, client_first, client_last):
        #implement registration with database here
        #User fields: account_id, username, password, first_name, last_name
        #-check that username is unique
        #-get next ID and assign it to the new user
        #-store new account info in the DB - the password (others?) should certainly be stored in encrypted form
        pass


    def handle_login_req(self, client_username, client_password):
        #temporary check if username/login can be read from data
        #should instead query the database to retrieve a single tuple
        #FIX!!
        response = ""
        if(client_username == 'u' and client_password == 'p'):
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

            #0 bytes of data sent - connection must have been closed by the client
            if not client_data:
                print("Client at " + str(self.addr) + " has closed the connection.")
                return

            #***authentication check against the client required.***
            #handle parsing the client's request here, which should be in the form of ciphertext + signature

            #parse the client's request
            client_req = json.loads(client_data.decode())
            client_req = ast.literal_eval(client_req)

            print(isinstance(client_req, dict))
            print(client_req)
            print("Client sent request for: " + client_req['command'])

            #handle various client requests
            if(client_req['command'] == 'login'):
                self.handle_login_req(client_req['username'], client_req['password'])

            #To implement
            elif(client_req['command'] == 'register'):
                self.handle_registration()

            #To implement
            elif(client_req['command'] == 'send'):
                self.handle_send_message()

            #Shouldn't need exit handling - returning from the thread above properly cleans it up
            '''elif(client_req['command'] == 'exit'):
                self.close_client_connection()'''


    #continuous execution of the thread - function override
    def run(self):

        #authentication needs to be done first??
        #accept connection from client
        self.new_connection()

        #temporary return to terminate the thread - where will this be placed?
        return

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