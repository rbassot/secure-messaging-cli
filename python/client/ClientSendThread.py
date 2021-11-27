#!/usr/bin/env python3

from sys import *
from os import *
from socket import *
from threading import *
from queue import *
from time import *
import json
import ast
#from PIL import Image

import config

'''
Basic ClientSendThread class for the client-side to handle user interface/interaction & send requests to the server.
'''

class ClientSendThread(Thread):
    def __init__(self, socket, address, username):    #Inherit from Thread class
        Thread.__init__(self) #provide a common event for interthread communication between send/receive threads
        self.sock = socket
        self.addr = address
        self.username = username
        #self.queue = queue
        self.exception = None


    #Override: to be able to pass the exception to the called thread (main)
    def join(self):
        Thread.join(self)

        #re-raise the caught exception for the caller thread
        if self.exception:
            raise self.exception

    
    #Function to acquire shared resource (stdout file descriptor) before printing to screen
    def locked_print(self, message_str):
        try:
            config.lock.acquire()
            print(message_str)
            config.lock.release()
            return

        except:
            #print("Error acquiring the lock for printing!")
            return


    #Function to acquire shared resource (stdin file descriptor) before receiving user input
    def locked_input(self, prompt):
        #if the sender thread is the only thread using stdin, do we need to lock on input?
        try:
            #config.lock.acquire()
            user_input = input(prompt)
            #config.lock.release()
            return user_input

        except:
            #print("Error acquiring the lock for input!")
            return


    def clear_screen(self):
        system('clear')
        return


    def display_options(self):
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
        #notify the server that connection should be terminated
        self.sock.shutdown(SHUT_RDWR)
        self.sock.close()
        self.locked_print("(Send Thread) Connection was closed. Program is exiting gracefully.")
        return

    
    def serialize_chat_message(self, message, recv_username):
        #format the message into a server request, then serialize
        formatted_req = "{'command':'message_sent','send_username':'%s','recv_username':'%s','message':'%s'}"%(self.username, recv_username, message)
        serialized_req = json.dumps(formatted_req).encode()
        return serialized_req


    #Sender-side chat initialization for the SendThread
    def request_new_chat(self, recv_username):
        #retrieve requested user's public key bundle from the server DB
        #(sending placeholder message)
        #establish X3DH authentication
    
        #on every new message, recalculate the shared key prior to sending

        #locked_print req'd here
        system('clear')
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
        #place arguments into a list
        args = input_str.lower().split(":")

        #assert that there are only either 1 or 2 arguments
        if(len(args) > 2):
            raise ValueError("Please provide a command with 2 or less arguments.")

        elif(len(args) < 2):
            return args[0], None

        return args[0], args[1]

    
    #generic client handling of a chat
    def join_chat(self, other_username):
        #self.clear_screen()
        #SendThread chat message loop
        while True:
            try:
                #get user input for writing a message to the connected user
                #TODO: may need to avoid input() + use an event here??
                user_message = self.locked_input("")

                if not user_message:
                    continue

                #check for user exit request
                if(user_message == '--exit'):
                    #should notify the server on exit - to be able to notify the other client that user has dropped
                    #also must notify the RecvThread that exit was asked for - use a global flag/event?
                    self.locked_print("Exiting the chat session...")
                    break

                #format & serialize the message, then send to server
                serialized_req = self.serialize_chat_message(user_message, other_username)
                self.sock.send(serialized_req)

                #finally, print the client's own message to its own chat window
                self.locked_print("\033[A\033[A")
                self.locked_print("You: " + user_message)

            except:
                self.locked_print("There was an issue somewhere in the chat...")
        return


    def request_history(self, other_username):
        #ask the server to retrieve conversation history
        try:
            req_conversation = "{'command':'history','my_username':'%s','other_username':'%s','message':'Retrieve conversation history'}"%(self.username, other_username)
            serialized_req = json.dumps(req_conversation).encode()
            self.sock.send(serialized_req)

            #probably block the sender thread here until the RecvThread prints out full convo history?
            config.shared_event.wait()

        except:
            self.locked_print("There was an issue with sending the history request...")
        return


    def main_menu(self):
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
                    #MUST notify the server here to remove client from auth_users + connections lists
                    self.close_server_conn()
                    return 0

                #handle user logout - exit main menu scope
                elif(option == "--logout"):
                    #MUST notify the server here to remove client from auth_users + connections lists
                    #self.close_server_conn()
                    return 1

                #handle user retrieving conversation history
                elif(option == "--history"):
                    self.request_history(recv_user)

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


    #Override: continuous execution of the receiver thread
    def run(self):
        #add this client's username/socket pair to the shared dictionary
        config.connections.update({self.username: self.sock})

        #first encounter with main menu - display options
        self.display_options()

        #--- Main Menu ---
        while True:
            #handle main menu interface
            #graceful program exit - throws an exception for the main thread to be notified
            if not (self.main_menu()):
                self.locked_print("Raising BaseException")
                self.exception = BaseException
                return

            #user logged out - return to login menu
            break
        
        return
