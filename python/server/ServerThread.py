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
        '''
        Initializes a ServerThread instance as a subclass of threading.Thread.
        This thread handles the entirety of one client's requests, once that client
        has authenticated and logged in. Once initialized, the thread begins execution
        inside self.start().

        Attributes
        ----------
        self.sock: socket.socket
            The client's socket connection object.

        self.addr: socket.AF_INET
            The client's IPv4 address that they are connected from. 

        self.db_conn: sqlite3.connect
            The database connection object to communicate with the SQLite3 DB.

        Returns
        ----------
        None
        '''
        Thread.__init__(self)
        self.sock = socket
        self.addr = address
        self.db_conn = None
        #self.username? To determine if the client is logged in, so 'send', etc can be performed
        print("New server thread created for client at: " + str(address))
        self.start()


    def handle_new_chat(self, send_username, recv_username):
        '''
        Server-side handling of a chat request from ClientA. Sends a 'request to chat from
        ClientA' to ClientB. This ServerThread - associated with ClientA - will block until
        confirmation is received at the ClientB ServerThread, which triggers an event to
        release the blocked thread.

        Parameters
        ----------
        send_username: str
            ClientA's (the sender-side client) username.

        recv_username: str
            ClientB's (the receiver-side client) username.

        Returns
        ----------
        None
        '''
        #Step 2 - send a request to the receiving client to establish connection
        # req_to_connect = "{'command':'req_chat_from', 'response':'SUCCESS', 'send_username':'%s', 'message':'ClientA has requested to chat!'}"%(send_username)
        req_to_connect = {
            'command':"req-chat-from", 
            'response':"SUCCESS", 
            'send_username': send_username, 
            'message':"ClientA has requested to chat!"
        }
        print("Step2: ", req_to_connect)
        serialized_req = json.dumps(req_to_connect).encode()
        receiver_socket = config.connections.get(str(recv_username))
        receiver_socket.send(serialized_req)

        #Step 3 - block this ServerThread A until the receiving client responds to ServerThreadB
        config.shared_event.wait()

        #Step 6 - notify the sender client that the receiver confirmed the chat req
        # sender_conn_confirm = "{'command':'chat_confirmed', 'response':'SUCCESS', 'send_username':'%s', 'recv_username':'%s', 'message':'The other client accepted the chat request.'}"%(send_username, recv_username)
        # serialized_confirm = json.dumps(sender_conn_confirm).encode()
        sender_conn_confirm = {
            'command':'chat-confirmed', 
            'response':'SUCCESS', 
            'send_username':send_username, 
            'recv_username':recv_username, 
            'message':'The other client accepted the chat request.'
        }
        serialized_confirm = json.dumps(sender_conn_confirm).encode()
        #confirm with the sender client that the connection is established
        self.sock.send(serialized_confirm)

        #Finally return to listener scope to to wait for messages from the sender-side client
        return


    def accept_chat_request(self):
        '''
        Server-side handling of a chat response received from ClientB. This function only
        releases the blocked ServerThreadA, clears the event, and then returns to then
        wait for any messages coming from ClientB (directed towards client A).

        Parameters
        ----------
        None

        Returns
        ----------
        None
        '''
        #Step 5 - notify ServerThread A that the receiver's response was received
        config.shared_event.set()
        config.shared_event.clear()

        #Finally return to listener scope to wait for messages from the receiver-side client
        return

    
    #REMOVE
    '''def confirm_new_chat(self, send_username, recv_username):
        #Step 4 - forward response to the sender-side client
        #self.sock.send(recv_data)
        response = ""
        if(self.db_conn.is_registered_user(recv_username)): #FIX: also needs to check for recv account activity at the time of the request
            response = "{'command':'chat-confirmed', 'response':'SUCCESS', 'recv_username':'%s', 'message':'Successfully connected to ClientB.'}"%(recv_username)

        else:
            response = "{'command':'chat-confirmed', 'response':'FAILURE', 'message':'Username could not be found!'}"

        print("This is the response to confirm on the sender-side: " + response)
        serialized_resp = json.dumps(response).encode()
        self.sock.send(serialized_resp)'''


    def handle_send_message(self, send_client, recv_client, encr_message, image_attached=None):
        '''
        Server-side sending of a message from one client to another. The receiver client's
        socket object is found in the shared config file, and used to forward the sent message.
        Messages arrive at the server in encrypted form, and are unchanged when they are sent,
        achieving forward secrecy for the transmission. Lastly, to obtain message histories,
        each message is stored twice in the DB - once for each owner of that message. This is
        required to separate Alice's history from Bob's history, where each of them can view
        the correct perspective of their chats, and delete a conversation history without
        affecting the history of other users.

        Parameters
        ----------
        send_client: str
            The sending client's username.

        recv_client: str
            The intended receiver client's username.

        encr_message: str
            The AES-GCM encrypted message, in string format.

        Returns
        ----------
        None
        '''
        #reformat & redirect the message to the receiving client
        # forwarded_msg = "{'command':'message_recv', 'send_username':'%s', 'recv_username':'%s', 'message':'%s'}"%(send_client, recv_client, encr_message)
        forwarded_msg = {
            'command':'message-recv', 
            'send_username': send_client, 
            'recv_username': recv_client, 
            'message':encr_message
        }
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


    def handle_exit_chat(self, send_client, recv_client):
        #send a response for chat termination to BOTH clients
        # sender_resp = "{'command':'exit-chat', 'send_username':'%s', 'recv_username':'%s', 'message':'The chat has been closed.'}"%(send_client, recv_client)
        sender_resp = {
            'command':'exit-chat', 
            'send_username':send_client, 
            'recv_username':recv_client, 
            'message':'The chat has been closed.'
        }
        serialized_send_resp = json.dumps(sender_resp).encode()

        # receiver_resp  = "{'command':'exit-chat', 'send_username':'%s', 'recv_username':'%s', 'message':'%s has closed the chat - Hit ENTER to return to the main menu.'}"%(send_client, recv_client, send_client)
        receiver_resp = {
            'command':'exit-chat', 
            'send_username':send_client, 
            'recv_username':recv_client, 
            'message':send_client + ' has closed the chat - Hit ENTER to return to the main menu.'
        }
        serialized_recv_resp = json.dumps(receiver_resp).encode()

        #send both responses to each client's socket
        self.sock.send(serialized_send_resp)
        recv_socket = config.connections.get(str(recv_client))
        recv_socket.send(serialized_recv_resp)
        return

    
    def handle_registration(self, client_first, client_last, client_username, client_password):
        '''
        Server-side handling of a request to register a new client account. Account information
        is inserted into the Account table in the DB. This table has a primary key on the 'username'
        attribute, and therefore enforces unique usernames accross all registered accounts.

        Parameters
        ----------
        client_first: str
            The registering client's first name.

        client_last: str
            The registering client's last name.

        client_username: str
            The registering client's account username.

        client_password: str
            The registering client's account password.

        Returns
        ----------
        None
        '''
        #pass account info to database object for account creation
        response = ""
        if(self.db_conn.insert_new_account(client_first, client_last, client_username, client_password)):
            # response = "{'response':'SUCCESS', 'message':'Successfully created account.'}"
            response = {
                'response':'SUCCESS',
                'message':'Successfully created account.'
            }
        else:
            # response = "{'response':'FAILURE', 'message':'Account creation was not successful!'}"
            response = {
                'response':'FAILURE',
                'message':'Account creation was not successful!'
            }

        serialized_resp = json.dumps(response).encode()
        self.sock.send(serialized_resp)
        return


    def handle_account_deletion(self, client_username):
        '''
        Server-side deletion of a client's account. Deletes all associated records
        from all four tables - Account, Message, OTPK, KeyBundle.

        Parameters
        ----------
        client_username: str
            The username of the client account to be deleted.

        Returns
        ----------
        None
        '''
        #delete client's account record from the database AND all of their owned message histories
        #TODO: extend this to delete all OTPKs and public key bundle
        response = ""
        if(self.db_conn.delete_account(client_username) and self.db_conn.delete_all_histories(client_username)):
            # response = "{'command':'delete-account', 'response':'SUCCESS', 'message':'Successfully deleted your account information.'}"
            response = {
                'command':'delete-account', 
                'response':'SUCCESS', 
                'message':'Successfully deleted your account information.'
            }

        else:
            # response = "{'command':'delete-account', 'response':'FAILURE', 'message':'Account deletion was not successful!'}"
            response = {
                'command':'delete-account', 
                'response':'FAILURE', 
                'message':'Account deletion was not successful!'
            }

        serialized_resp = json.dumps(response).encode()
        self.sock.send(serialized_resp)
        return


    def add_active_connection(self, client_username):
        '''
        ServerThread publishing of resources for other ServerThreads to access. The connected
        client's username and socket object is published to the config file. This allows
        other ServerThreads to send messages to clients to which they are not associated.

        Parameters
        ----------
        client_username: str
            The username of the client information being published.

        Returns
        ----------
        None
        '''
        #add the Socket connections to the global - to be referenced by other server threads
        config.connections.update({client_username: self.sock})
        return


    def handle_login_req(self, client_username, client_password):
        '''
        Server-side handling of a client login request. Checks against the DB
        to ensure that the client is registered and properly authenticates.
        Then, sends a SUCCESS response to the client if authentication is
        successful.

        Parameters
        ----------
        client_username: str
            The username of the client account to be authenticated.

        client_password: str
            The password of the client account to be authenticated.

        Returns
        ----------
        None
        '''
        #check if account is registered & that it is not currently connected with the server
        #FIX!! config.auth.... to assert no duplicate connections to the same account!
        response = ""
        if(client_username not in config.authorized_users and self.db_conn.is_valid_username_password(client_username, client_password)):
            # response = "{'response':'SUCCESS', 'message':'Successfully logged in.'}"
            response = {
                'response':'SUCCESS',
                'message':'Successfully logged in.'
            }

        else:
            # response = "{'response':'FAILURE', 'message':'Login was not successful!'}"
            response = {
                'response':'FAILURE', 
                'message':'Login was not successful!'
            }

        serialized_resp = json.dumps(response).encode()
        self.sock.send(serialized_resp)
        return


    def retrieve_history(self, this_username, other_username):
        '''
        Server-side retrieving of a client's history with the specified client.
        The list of messages is a list of tuples, that contain information for the
        owner of the message, the sender/receiver, and the encrypted message itself.
        Tuples are sent to the client in raw format, and are parsed on arrival.

        Parameters
        ----------
        this_username: str
            The username of the client account requesting their history.

        other_username: str
            The username of the other client who was part of the conversation history being requested.

        Returns
        ----------
        None
        '''
        #retrieve all messages from the DB for this users conversation history with specific client
        messages = self.db_conn.get_message_history(this_username, other_username)
        #print(messages, type(messages))
        if(not messages):
            print("There were no messages in the client's history!")

        #send the list of messages (could be empty!) back over to the client
        # print("entering history resp...")
        # history_resp = '''{"command":"history", "response":"SUCCESS", "message_list":"%s", "other_username":"%s", "message":"Successfully retrieved conversation history."}'''%(messages, other_username)
        history_resp = (json.dumps({
            'command':'history',
            'response':'SUCCESS',
            'message_list':messages,
            'other_username': other_username,
            'message': 'Successfully retrieved conversation history.'
        })).encode()
        # history_resp = "{\'command\':\'history\', \'response\':\'SUCCESS\', \'message_list\':\'%s\', \'other_username\':\'%s\', \'message\':\'Successfully retrieved conversation history.\'}"%(messages, other_username)
        # print("entering serialized resp...")

        # serialized_resp = json.dumps(history_resp).encode()

        # print(serialized_resp, type(serialized_resp))
        # print()
        # print("sending serialized resp...")
        # print("LENGTH", len(serialized_resp))
        # losing first 1024 bytes, prepend to make up for loss
        #random_bytes = b'b'*1024
        try:
            #to change!!!
            sent_size = self.sock.send(history_resp)
            #print("sent size:", sent_size)
        except Exception as e:
            print(e)
        
        return


    def delete_history(self, this_username, other_username):
        '''
        Server-side deleting of a client's history with the specified client.
        Only the history owned by the requesting client is deleted. This allows
        deletion to take place only in on client's environment - the other 
        involved client can continue to view that conversation history.

        Parameters
        ----------
        this_username: str
            The username of the client account requesting their history to be deleted.

        other_username: str
            The username of the other client who was part of the conversation history being deleted.

        Returns
        ----------
        None
        '''
        #delete all messages corresponding to the user's history with the specified client
        if(not self.db_conn.delete_message_history(this_username, other_username)):
            print("Error deleting message history!")
            return

        #send confirmation of deletion back to the client
        # del_history_resp = "{'command':'delete-history', 'response':'SUCCESS', 'message':'Successfully deleted your conversation history with %s.'}"%(other_username)
        del_history_resp = {
            'command':'delete-history',
            'response':'SUCCESS',
            'message':'Successfully deleted your conversation history with ' + other_username + '.'
        }
        serialized_resp = json.dumps(del_history_resp).encode()
        self.sock.send(serialized_resp)
        return

    
    def delete_all_histories(self, this_username):
        '''
        Server-side deleting of every conversation history existing for the requesting
        client. This operation is performed at every session termination for a client - 
        logout, program exit, and account deletion. The reason for history deletion is
        because Alice has no way of retrieving her private keys to decrypt past messages,
        without saving a state outside of program execution.

        Parameters
        ----------
        this_username: str
            The username of the client account requesting all their histories to be deleted.

        Returns
        ----------
        None
        '''
        #delete all messages corresponding to the user's history with the specified client
        if(not self.db_conn.delete_all_histories(this_username)):
            print("Error deleting message history!")
            return

        #send confirmation of deletion back to the client
        # delete_all_resp = "{'command':'delete-all-histories', 'response':'SUCCESS', 'message':'Successfully deleted all your conversation histories.'}"
        delete_all_resp = {
            'command':'delete-all-histories',
            'response':'SUCCESS',
            'message':'Successfully deleted all your conversation histories.'
        }
        serialized_resp = json.dumps(delete_all_resp).encode()
        self.sock.send(serialized_resp)
        return


    def new_connection(self):
        '''
        The main program loop of the ServerThread. Requests from the associated client
        are waited upon, where the ServerThread blocks until a request is received.
        The request is parsed and the request handling method used is determined by
        the type of request that was sent ('command' parameter).

        Should this function return, this ServerThread is terminated.

        Parameters
        ----------
        None

        Returns
        ----------
        None
        '''
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
            # print(client_req)
            # client_req = ast.literal_eval(client_req)

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

            elif(client_req['command'] == 'exit-chat'):
                self.handle_exit_chat(client_req['send_username'], client_req['recv_username'])

            #Step 4 - receive response from the receiver client (on ServerThread B)
            elif(client_req['command'] == 'accept-chat-req'):
                self.accept_chat_request()

            #basic redirection of a chat message from ClientA to ClientB
            elif(client_req['command'] == 'message-sent'):
                self.handle_send_message(client_req['send_username'], client_req['recv_username'], client_req['message'], None) #How do we handle image?

            #handle client requesting conversation history with a specific user
            elif(client_req['command'] == 'history'):
                self.retrieve_history(client_req['send_username'], client_req['recv_username'])

            #handle deleting the client's history from the database
            elif(client_req['command'] == 'delete-history'):
                self.delete_history(client_req['send_username'], client_req['recv_username'])

            #handle deleting ALL the client's histories from the database
            elif(client_req['command'] == 'delete-all-histories'):
                self.delete_all_histories(client_req['send_username'])

            #handle deleting the client's account + ALL their conversation histories
            elif(client_req['command'] == 'delete-account'):
                self.handle_account_deletion(client_req['send_username'])
            
            #Shouldn't need exit handling - returning from the thread above properly cleans it up
            '''elif(client_req['command'] == 'exit'):
                self.close_client_connection()'''


    #continuous execution of the thread - function override
    def run(self):
        '''
        threading.Thread function override to instantiate objects and determine the flow of the
        thread's execution. When this function returns, the thread terminates.

        Parameters
        ----------
        None

        Returns
        ----------
        None
        '''       
        #create a database connection object for this server thread
        self.db_conn = DatabaseConn()

        #accept connection from client
        self.new_connection()

        #temporary return to terminate the thread - where will this be placed?
        return
