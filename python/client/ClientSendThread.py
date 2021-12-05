#!/usr/bin/env python3

from sys import *
import os
from socket import *
from threading import *
from queue import *
from time import *
import json
import ast
#from PIL import Image

import config
from encryption import User
import binascii

'''
Basic ClientSendThread class for the client-side to handle user interface/interaction & send requests to the server.
'''

class ClientSendThread(Thread):
    def __init__(self, socket, address, username):    #Inherit from Thread class
        '''
        Initializes a ClientSendThread instance as a subclass of threading.Thread.
        This thread handles client input, and outgoing requests to the server.
        Once initialized, the thread begins execution inside self.run(), which
        is called by the main thread (parent).

        Attributes
        ----------
        self.sock: socket.socket
            The server's socket connection object.

        self.addr: socket.AF_INET
            The server's IPv4 address that they are connected from. 

        self.username: str
            The username of the logged-in client account.

        self.exception: Exception
            Holds an exception that can be raised to the scope of the main thread.

        self.enc_user: encryption.User
            An instance of encryption.User class that handles both X3DH key exchange,
            and AES-GCM message encryption/decryption.

        Returns
        ----------
        None
        '''
        Thread.__init__(self) #provide a common event for interthread communication between send/receive threads
        self.sock = socket
        self.addr = address
        self.username = username
        #self.queue = queue
        self.exception = None
        self.enc_user = None

        if(not config.username):
            self.enc_user = User(username)
            config.username = self.enc_user
        else:
            self.enc_user = config.username


    #Override: to be able to pass the exception to the called thread (main)
    def join(self):
        '''
        Function override to be able to pass an exception to the caller thread
        (main thread), which can be handled in the parent scope. This is a workaround
        to be able to gracefully terminate the program by catching an exception
        in the parent.

        Thread.join() is blocking until the working thread returns or exits in any
        form, normally through correct behaviour returning from run().

        Parameters
        ----------
        None

        Returns
        ----------
        None
        '''
        Thread.join(self)

        #re-raise the caught exception for the caller thread
        if self.exception:
            raise self.exception

    
    def locked_print(self, message_str):
        '''
        Print function to handle the shared resource of stdout file descriptor.
        The Lock object is instantiated once and shared in the config file among
        both client threads. This lock must be acquired by a running thread before
        that thread can print any content to the screen. Once work is complete,
        the lock is released and can be acquired by any other thread.

        Solves the Producer/Consumer resource contention problem.

        Parameters
        ----------
        message_str: str
            The desired message to be printed to the console.

        Returns
        ----------
        None
        '''
        try:
            config.lock.acquire()
            print(message_str)
            config.lock.release()
            return

        except:
            #print("Error acquiring the lock for printing!")
            return


    def locked_input(self, prompt):
        '''
        Input function to receive user input. This function no longer uses a lock
        due to blocking issues in threads. Therefore it acts as a regular Python
        input() function.

        Parameters
        ----------
        prompt: str
            The prompt to show the user while asking for their input.

        Returns
        ----------
        user_input: str
            The user's input string.
        '''
        try:
            #config.lock.acquire()
            user_input = input(prompt)
            #config.lock.release()
            return user_input

        except:
            #print("Error acquiring the lock for input!")
            return


    def clear_screen(self):
        '''
        Function to clear the screen (stdout) for a running client. Checks
        whether the machine is running Windows or Linux, and then clears
        the screen appropriately.

        Parameters
        ----------
        None

        Returns
        ----------
        None
        '''
        os.system('cls' if os.name == 'nt' else 'clear')
        return


    def display_options(self):
        '''
        Function to display all main-menu user options for a client. Strings
        are formatted for the console. User commands all begin with a double
        dash delimiter.

        Parameters
        ----------
        None

        Returns
        ----------
        None
        '''
        #main menu introduction
        self.locked_print("")
        self.locked_print("----- Welcome to the main menu -----")

        #display all user options
        self.locked_print("OPTIONS:")
        self.locked_print("--chat:<username>                Start a secure chat with an existing user.")
        self.locked_print("--quit-chat                      Quit the current chat and return to the main menu.")
        self.locked_print("--history:<username>             View your conversation history with a user.")
        self.locked_print("--delete-history:<username>      Delete your conversation history with a specific user.")
        self.locked_print("--logout                         Log out of your account and return to the main menu.")
        self.locked_print("--delete-account                 Delete your account and return to the main menu.")
        self.locked_print("--exit                           Gracefully logout and exit Python CLI Secure Messaging.")
        self.locked_print("--options                        Display available options from this menu.")
        self.locked_print("")
        #**should add functionality for a user to view an image that was attached in a previous message**


    def close_server_conn(self):
        '''
        Closes the active connection with the server. The Socket object is
        shutdown and closed. Eventually returns scope to the main caller thread.

        Parameters
        ----------
        None

        Returns
        ----------
        None
        '''
        #notify the server that connection should be terminated
        self.sock.shutdown(SHUT_RDWR)
        self.sock.close()
        self.locked_print("(Send Thread) Connection was closed. Program is exiting gracefully.")
        return

    
    def serialize_chat_message(self, message, recv_username):
        '''
        Serializes chat messages to be sent to the server, then redirected
        to the receiver-side client. Serializing involves formatting the
        message as a request, and converting to a bytes-type object.

        Parameters
        ----------
        message: str
            The message to be serialized.

        recv_username: str
            The intended receiver-side client's username.

        Returns
        ----------
        None
        '''
        #format the message into a server request, then serialize
        formatted_req = "{'command':'message_sent','send_username':'%s','recv_username':'%s','message':'%s'}"%(self.username, recv_username, message)
        serialized_req = json.dumps(formatted_req).encode()
        return serialized_req


    def request_new_chat(self, recv_username):
        '''
        Initial request from clientA for a chat to be established
        with clientB. This request is sent to the server, and forwarded
        to the receiver client.

        Parameters
        ----------
        recv_username: str
            The intended receiver-side client's username.

        Returns
        ----------
        None
        '''
        os.system('clear')
        self.locked_print("Connecting with " + str(recv_username) + "...")
        try:
            #create sender-side client request
            connect_req = "{'command':'chat','send_username':'%s','recv_username':'%s','message':'Connect with user'}"%(self.username, recv_username)
            serialized_req = json.dumps(connect_req).encode()
            self.sock.send(serialized_req)

        except:
            self.locked_print("There was an issue with sending the chat request...")

        #server handles sending a chat request to the receiver
        #blocked until the other user accepts the chat request, and this client's own RecvThread triggers event
        config.shared_event.wait()

        #self.event.clear()
        
        #TODO: add the failure path - display error message & return to main menu

        #sender-side user chat scenario
        self.join_chat(recv_username)
        return


    def parse_main_menu_input(self, input_str):
        '''
        Parse all user input in the main-menu scope. User input is split into
        two parts, separated by the colon (:) that the user passes. Returns
        both the command and target username.

        Parameters
        ----------
        input_str: str
            The input string received from the user.

        Returns
        ----------
        args[0]: str
            The first part of the user's input, representing the command.

        args[1]: str
            The second part of the user's input, representing the target username.
        '''
        #place arguments into a list
        args = input_str.lower().split(":")

        #assert that there are only either 1 or 2 arguments
        if(len(args) > 2):
            raise ValueError("Please provide a command with 2 or less arguments.")

        elif(len(args) < 2):
            return args[0], None

        return args[0], args[1]

    
    def join_chat(self, other_username):
        '''
        SendThread initialization of entering a real-time chat with another user.
        The user can now input any text, and that text becomes sent as a message
        to the connected client. Quitting the chat involves the '--quit' command.

        **Note**: There is NO notification of clients at the other end of the chat
        that leave the real-time chat.

        Parameters
        ----------
        other_username: str
            The other client's username also connected to the chat.

        Returns
        ----------
        None
        '''
        #SendThread chat message loop
        while True:
            try:
                #get user input for writing a message to the connected user
                #TODO: may need to avoid input() + use an event here??
                user_message = self.locked_input("")

                if not user_message:
                    continue

                #check for user exit request
                if(user_message in ('--quit', '--quit-chat')):
                    #should notify the server on exit - to be able to notify the other client that user has dropped
                    #also must notify the RecvThread that exit was asked for - use a global flag/event?
                    self.locked_print("Exiting the chat session...")
                    break

                #encrypt the message, format & serialize, then send to server
                encrypted_msg = self.enc_user.encrypt_msg(other_username, user_message)
                
                # converting enc msg bytes to str
                to_hex = binascii.hexlify(encrypted_msg)
                str_enc_msg = to_hex.decode()

                serialized_req = self.serialize_chat_message(str_enc_msg, other_username)
                self.sock.send(serialized_req)

                #finally, print the client's own message to its own chat window
                self.locked_print("\033[A\033[A")
                self.locked_print("You: " + user_message)

            except:
                self.locked_print("There was an issue somewhere in the chat...")
        return


    def request_history(self, other_username):
        '''
        SendThread initialization of entering a real-time chat with another user.
        The user can now input any text, and that text becomes sent as a message
        to the connected client. Quitting the chat involves the '--quit' command.
        The SendThread blocks in this function until the server provides a response.

        **Note**: There is NO notification of clients at the other end of the chat
        that leave the real-time chat.

        Parameters
        ----------
        other_username: str
            The other client's username also connected to the chat.

        Returns
        ----------
        None
        '''
        #ask the server to retrieve conversation history
        try:
            req_conversation = "{'command':'history', 'my_username':'%s', 'other_username':'%s', 'message':'Retrieve conversation history'}"%(self.username, other_username)
            serialized_req = json.dumps(req_conversation).encode()
            self.sock.send(serialized_req)

            #blocks the sender thread here until the RecvThread prints out full convo history
            config.shared_event.wait()

        except:
            self.locked_print("There was an issue with sending the history request...")
        return


    def request_delete_history(self, other_username):
        '''
        Request to delete a user's conversation history with a specified client.
        The server receives this request and correctly deletes from the DB.
        Message histories that are deleted are permanently lost.

        The SendThread blocks in this function until the server provides a response.

        Parameters
        ----------
        other_username: str
            The associated client whose conversation history should be deleted.

        Returns
        ----------
        None
        '''
        #ask the server to delete conversation history with a specific user
        try:
            req_deletion = "{'command':'delete-history', 'my_username':'%s', 'other_username':'%s', 'message':'Delete a conversation history'}"%(self.username, other_username)
            serialized_req = json.dumps(req_deletion).encode()
            self.sock.send(serialized_req)

            #blocks the sender thread here until the RecvThread prints out confirmation of deletion
            config.shared_event.wait()

        except:
            self.locked_print("There was an issue with deleting the history...")
        return


    def request_delete_all_histories(self, my_username):
        '''
        Request to delete every conversation for a specific user.
        The server receives this request and correctly deletes from the DB.
        Message histories that are deleted are permanently lost.

        The SendThread blocks in this function until the server provides a response.

        Parameters
        ----------
        my_username: str
            The associated client whose set of conversation histories should be deleted.

        Returns
        ----------
        None
        '''
        #ask the server to delete all conversations owned by this client
        try:
            req_delete_all = "{'command':'delete-all-histories', 'my_username':'%s', 'message':'Delete all conversation histories'}"%(self.username)
            serialized_req = json.dumps(req_delete_all).encode()
            self.sock.send(serialized_req)

            #blocks the sender thread here until the RecvThread prints out confirmation of histories deletion
            config.shared_event.wait()

        except:
            self.locked_print("There was an issue with deleting all the histories...")
        return


    def request_delete_account(self, my_username):
        '''
        Request to delete a specific client account.
        The server receives this request and correctly deletes from the DB.
        Accounts that are deleted are permanently lost.

        The SendThread blocks in this function until the server provides a response.

        Parameters
        ----------
        my_username: str
            The associated client whose account should be deleted.

        Returns
        ----------
        None
        '''
        #ask the server to delete my account & accompanying message histories
        try:
            req_delete_account = "{'command':'delete-account', 'my_username':'%s', 'message':'Delete my account.'}"%(self.username)
            serialized_req = json.dumps(req_delete_account).encode()
            self.sock.send(serialized_req)

            #blocks the sender thread here until the RecvThread prints out confirmation of account deletion
            config.shared_event.wait()

        except:
            self.locked_print("There was an issue with deleting the client's account...")
        return


    def main_menu(self):
        '''
        The main program loop of the ClientSendThread. Continually accepts user input,
        and handles commands appropriately. Requests are serialized and sent to the server.

        Should this function return, this SendThread is terminated.

        Parameters
        ----------
        None

        Returns
        ----------
        0: int
            If zero is returned, the program should exit gracefully.
        
        1: int
            If one is returned, the thread should exit and return to the login scope.
        '''
        #continuously accept user input from the main menu
        while True:

            try:
                #get user input for writing a message
                user_input = self.locked_input(">> ")

                if not user_input:
                    continue

                #first parse the user input string
                option, recv_user = self.parse_main_menu_input(user_input)

                #display options to user
                if(option == "--options"):
                    self.clear_screen()
                    self.display_options()

                #handle starting a new chat
                elif(option == "--chat"):
                    self.request_new_chat(recv_user)

                #handle program exit
                elif(option == "--exit"):
                    #notify the server to delete message history for the client (session terminates)
                    self.request_delete_all_histories(self.username)

                    #MUST notify the server here to remove client from auth_users + connections lists
                    self.close_server_conn()
                    return 0

                #handle user logout - exit main menu scope
                elif(option == "--logout"):
                    #MUST notify the server here to remove client from auth_users + connections lists
                    #self.close_server_conn()

                    #notify the server to delete message history for the client (session terminates)
                    self.request_delete_all_histories(self.username)
                    return 1

                #handle user retrieving conversation history
                elif(option == "--history"):
                    self.request_history(recv_user)

                #handle user retrieving conversation history
                elif(option == "--delete-history"):
                    self.request_delete_history(recv_user)

                #handle account deletion (with all accompanying owned conversation histories)
                elif(option == "--delete-account"):
                    self.request_delete_account(self.username)
                    return 1

                #Receiver-side chat initialization for the SendThread
                elif(option == 'y'):
                    #set event to notify the RecvThread to continue its work
                    config.shared_event.set()

                    #wait for the RecvThread to enter the chat first (to display welcome message properly)
                    config.shared_event.clear()
                    config.shared_event.wait()

                    #receiver-side user chat scenario
                    self.join_chat(config.connected_username)

                else:
                    self.locked_print("Please pass a valid command.")
                    continue

            #catch argument length errors
            except ValueError as e:
                self.locked_print(e)

            #terminate the client threads on keyboard interrupt & exit program
            #**Windows bug fix for catching KeyboardInterrupts on input() - include EOFError**
            except (KeyboardInterrupt, EOFError) as e:
                self.locked_print(e)
                self.close_server_conn()
                return 0


    #Override: continuous execution of the sender thread
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
        #add this client's username/socket pair to the shared dictionary
        config.connections.update({self.username: self.sock})

        #first encounter with main menu - display options
        self.display_options()

        #--- Main Menu ---
        while True:
            #handle main menu interface
            #graceful program exit - throws an exception for the main thread to be notified
            if not (self.main_menu()):
                self.exception = BaseException
                return

            #user logged out - return to login menu
            break
        
        return
