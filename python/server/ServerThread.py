#!/usr/bin/env python3

from sys import *
from socket import *
from threading import *
import json
import ast
#from PIL import Image

import config
from DatabaseConnection import DatabaseConn

'''
Basic ServerThread class for server-side handling of multiple clients.
'''

class ServerThread(Thread):
    def __init__(self, socket, address):    #Inherit from Thread class
        Thread.__init__(self)
        print("New server thread created for client at: " + str(address))
        self.sock = socket
        self.addr = address
        self.db_conn = None
        #self.username? To determine if the client is logged in, so 'send', etc can be performed
        self.start()


    def handle_new_chat(self, send_username, recv_username):
        #Step 2 - send a request to the receiving client to establish connection
        req_to_connect = "{'command':'req_chat_from', 'response':'SUCCESS', 'send_username':'%s', 'message':'ClientA has requested to chat!'}"%(send_username)
        serialized_req = json.dumps(req_to_connect).encode()
        recv_socket = config.connections.get(str(recv_username))
        recv_socket.send(serialized_req)

        #Step 3 - receive response from the receiver-side client & parse it
        recv_data = recv_socket.recv(1024)
        recv_response = json.loads(recv_data.decode())
        recv_response = ast.literal_eval(recv_response)

        if(recv_response['command'] != 'accept_chat_req' or recv_response['recv_username'] != recv_username):
            print("Error establishing the connection!")
            return

        #Step 4 - forward response to the sender-side client
        #self.sock.send(recv_data)
        response = ""
        if(self.db_conn.is_registered_user(recv_username)): #FIX: also needs to check for recv account activity at the time of the request
            response = "{'command':'chat_confirmed', 'response':'SUCCESS', 'message':'Successfully connected to ClientB.'}"

        else:
            response = "{'command':'chat_confirmed', 'response':'FAILURE', 'message':'Username could not be found!'}"

        serialized_resp = json.dumps(response).encode()
        self.sock.send(serialized_resp)


    def handle_send_message(self, send_client, recv_client, encr_message, image_attached=None):
        #implement receiving a message from sender and forwarding to the receiver
        #-user authenticity established before this point (via digital signature)
        #-message is encrypted by sender (basic AES here?) and can only be decrypted by receiver (via private key?) once received
        #-every new encrypted message should be added to storage at the server *TWICE*:
        #     -->Once from perspective of the sender & Again from the perspective of the receiver (send/recv users are swapped)
        #     -->This will allow one user to delete their message history w/o affecting the other's
        #     (potentially include pre-populated DB with some messages)
        #-**optional** should a receiving user NOT be online, the server should still store the message and notify the sender.
        #   Then, upon connection of the receiving user to the server, the waiting encrypted message should be forwarded

        #reformat & redirect the message to the receiving client
        forwarded_msg = "{'command':'message_recv', 'send_username':'%s', 'recv_username':'%s', 'message':'%s'}"%(send_client, recv_client, encr_message)
        serialized_msg = json.dumps(forwarded_msg).encode()

        #TODO: Store the encrypted message twice (forward, reverse) in the DB's Message table

        #send to the correct receiving client via its socket connection
        recv_socket = config.connections.get(str(recv_client))
        recv_socket.send(serialized_msg)
        return

    
    def handle_registration(self, client_first, client_last, client_username, client_password):
        #implement registration with database here
        #User fields: account_id, username, password, first_name, last_name
        #-check that username is unique
        #-get next ID and assign it to the new user
        #-store new account info in the DB - the password (others?) should certainly be stored in encrypted form

        #pass account info to database object for account creation
        response = ""
        if(self.db_conn.insert_new_account(client_first, client_last, client_username, client_password)):
            response = "{'response':'SUCCESS', 'message':'Successfully created account.'}"

        else:
            response = "{'response':'FAILURE', 'message':'Account creation was not successful!'}"

        serialized_resp = json.dumps(response).encode()
        self.sock.send(serialized_resp)
        return


    def add_active_connection(self, client_username):
        #add the Socket connections to the global - to be referenced by other server threads
        config.connections.update({client_username: self.sock})
        return


    def handle_login_req(self, client_username, client_password):
        #check if account is registered & that it is not currently connected with the server
        #FIX!! config.auth....
        response = ""
        if(client_username not in config.authorized_users and self.db_conn.is_valid_username_password(client_username, client_password)):
            response = "{'response':'SUCCESS', 'message':'Successfully logged in.'}"
        else:
            response = "{'response':'FAILURE', 'message':'Login was not successful!'}"

        print(response)
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
            #add authenticated user to config's global list

            #parse the client's request
            client_req = json.loads(client_data.decode())
            client_req = ast.literal_eval(client_req)

            #print(isinstance(client_req, dict))
            print(client_req)
            print("Client sent request for: " + client_req['command'])

            #handle various client requests
            if(client_req['command'] == 'login'):
                self.handle_login_req(client_req['username'], client_req['password'])

                #add the logged in client to active connections as: {username: Socket conn}
                self.add_active_connection(client_req['username'])

            #To implement
            elif(client_req['command'] == 'register'):
                self.handle_registration(client_req['first'], client_req['last'], client_req['username'], client_req['password'])

            #To implement
            elif(client_req['command'] == 'send'):
                self.handle_send_message(client_req['send_username'], client_req['recv_username'], client_req['message'], None) #How do we handle image?

            #handle client requesting new chat with another user
            # - receive request from client A
            # - ask client B to establish connection
            # - receive response from client B
            # - notify client A that the request was accepted & connection can be established
            elif(client_req['command'] == 'chat'):
                #Step 1 - receive request from sending client to establish a new chat connection
                self.handle_new_chat(client_req['send_username'], client_req['recv_username'])

            #Shouldn't need exit handling - returning from the thread above properly cleans it up
            '''elif(client_req['command'] == 'exit'):
                self.close_client_connection()'''


    #continuous execution of the thread - function override
    def run(self):        
        #create a database connection object for this server thread
        self.db_conn = DatabaseConn()

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