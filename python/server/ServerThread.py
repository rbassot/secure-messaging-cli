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
        print("Step2: " + req_to_connect)
        serialized_req = json.dumps(req_to_connect).encode()
        receiver_socket = config.connections.get(str(recv_username))
        receiver_socket.send(serialized_req)

        #Step 3 - block this ServerThread A until the receiving client responds to ServerThreadB
        config.shared_event.wait()

        #MOVE TO SERVERTHREAD B SIDE
        '''
        #Step 3 - receive response from the receiver-side client & parse it
        recv_data = receiver_socket.recv(1024)
        recv_response = json.loads(recv_data.decode())
        recv_response = ast.literal_eval(recv_response)
        serv1_socket = recv_response['serv_socket']
        print("Step4: " + recv_response)

        #FIX: assert that the received response from receiver-side client was a correct response
        if(recv_response['command'] != 'accept_chat_req' or recv_response['recv_username'] != recv_username):
            print("Error establishing the connection!")
            return
        '''

        #Step 6 - notify the sender client that the receiver confirmed the chat req
        sender_conn_confirm = "{'command':'chat_confirmed', 'response':'SUCCESS', 'send_username':'%s', 'recv_username':'%s', 'message':'The other client accepted the chat request.'}"%(send_username, recv_username)
        serialized_confirm = json.dumps(sender_conn_confirm).encode()

        #confirm with the sender client that the connection is established
        self.sock.send(serialized_confirm)

        #Finally return to listener scope to to wait for messages from the sender-side client
        return


    def accept_chat_request(self):
        #Step 5 - notify ServerThread A that the receiver's response was received
        config.shared_event.set()
        config.shared_event.clear()

        #Finally return to listener scope to wait for messages from the receiver-side client
        return

    
    def confirm_new_chat(self, send_username, recv_username):
        #Step 4 - forward response to the sender-side client
        #self.sock.send(recv_data)
        response = ""
        if(self.db_conn.is_registered_user(recv_username)): #FIX: also needs to check for recv account activity at the time of the request
            response = "{'command':'chat_confirmed', 'response':'SUCCESS', 'recv_username':'%s', 'message':'Successfully connected to ClientB.'}"%(recv_username)

        else:
            response = "{'command':'chat_confirmed', 'response':'FAILURE', 'message':'Username could not be found!'}"

        print("This is the response to confirm on the sender-side: " + response)
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

        #store the encrypted message once in the DB's Message table twice - once for each owner of the message, for separate histories
        try:
            self.db_conn.insert_new_message(send_client, send_client, recv_client, encr_message)
            self.db_conn.insert_new_message(recv_client, send_client, recv_client, encr_message)

        except:
            print("Error with storing the message to the DB!")
            return

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
        return


    def retrieve_history(self, this_username, other_username):
        #retrieve all messages from the DB for this users conversation history with specific client
        messages = self.db_conn.get_message_history(this_username, other_username)
        if(not messages):
            print("There were no messages in the client's history!")

        #send the list of messages (could be empty!) back over to the client
        history_resp = '''{"command":"history", "response":"SUCCESS", "message_list":"%s", "other_username":"%s", "message":"Successfully retrieved conversation history."}'''%(messages, other_username)
        serialized_resp = json.dumps(history_resp).encode()
        self.sock.send(serialized_resp)
        return


    def delete_history(self, this_username, other_username):
        #delete all messages corresponding to the user's history with the specified client
        if(not self.db_conn.delete_message_history(this_username, other_username)):
            print("Error deleting message history!")
            return

        #send confirmation of deletion back to the client
        del_history_resp = "{'command':'delete-history', 'response':'SUCCESS', 'message':'Successfully deleted your conversation history with %s.'}"%(other_username)
        serialized_resp = json.dumps(del_history_resp).encode()
        self.sock.send(serialized_resp)
        return

    
    def delete_all_histories(self, this_username):
        #delete all messages corresponding to the user's history with the specified client
        if(not self.db_conn.delete_all_histories(this_username)):
            print("Error deleting message history!")
            return

        #send confirmation of deletion back to the client
        delete_all_resp = "{'command':'delete-all-histories', 'response':'SUCCESS', 'message':'Successfully deleted all your conversation histories.'}"
        serialized_resp = json.dumps(delete_all_resp).encode()
        self.sock.send(serialized_resp)
        return


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
            print("Client sent request to " + current_thread().name + " for: " + client_req['command'])

            #handle various client requests
            if(client_req['command'] == 'login'):
                self.handle_login_req(client_req['username'], client_req['password'])

                #add the logged in client to active connections as: {username: Socket conn}
                self.add_active_connection(client_req['username'])

            #To implement
            elif(client_req['command'] == 'register'):
                self.handle_registration(client_req['first'], client_req['last'], client_req['username'], client_req['password'])

            #handle client requesting new chat with another user:
            # 1 - receive request from client A (on ServerThread A)
            # 2 - ask client B to establish connection (from ServerThread A)
            # 3 - BLOCK ServerThread A on event, until ServerThread B triggers it
            # 4 - receive response from client B (on ServerThread B)
            # 5 - trigger the event from ServerThread B to notify ServerThread A to continue
            # 6 - notify client A that the request was accepted & connection can be established (from ServerThread A)
            elif(client_req['command'] == 'chat'):
                #Step 1 - receive request from sending client to establish a new chat connection
                self.handle_new_chat(client_req['send_username'], client_req['recv_username'])

            #Step 4 - receive response from the receiver client (on ServerThread B)
            elif(client_req['command'] == 'accept_chat_req'):
                self.accept_chat_request()

            #basic redirection of a chat message from clientA to clientB
            elif(client_req['command'] == 'message_sent'):
                self.handle_send_message(client_req['send_username'], client_req['recv_username'], client_req['message'], None) #How do we handle image?

            #handle client requesting conversation history with a specific user
            elif(client_req['command'] == 'history'):
                self.retrieve_history(client_req['my_username'], client_req['other_username'])

            #handle deleting the client's history from the database
            elif(client_req['command'] == 'delete-history'):
                self.delete_history(client_req['my_username'], client_req['other_username'])

            #handle deleting ALL the client's histories from the database
            elif(client_req['command'] == 'delete-all-histories'):
                self.delete_all_histories(client_req['my_username'])
            
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