#!/usr/bin/env python3

from sys import *
from os import *
from socket import *
from threading import *
from time import *
import json
import ast
#from PIL import Image

import config

'''
Basic ClientSendThread class for the client-side to handle user interface/interaction & send requests to the server.
'''

class ClientSendThread(Thread):
    def __init__(self, socket, address, username, event):    #Inherit from Thread class
        Thread.__init__(self)
        self.sock = socket
        self.addr = address
        self.username = username    #self.username? To determine if the client is logged in, so 'send', etc can be performed
        self.kill_event = event
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


    def enter_chat(self, recv_username):
        system('clear')
        self.locked_print("Connecting with " + str(recv_username) + "...")
        try:
            connect_req = "{'cmd':'chat','send_username':'%s','recv_username':'%s','message':'Connect with user'}"%(self.username, recv_username)
            serialized_req = json.dumps(connect_req).encode()
            self.sock.send(serialized_req)

        except:
            self.locked_print("There was an issue with sending the chat request...")
        return


    def parse_main_menu_input(self, input_str):
        #place arguments into a list
        args = input_str.split(":")

        #assert that there are only either 1 or 2 arguments
        if(len(args) > 2):
            raise ValueError("Please provide a command with 2 or less arguments.")

        elif(len(args) < 2):
            return args[0], None

        return args[0], args[1]


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

                #handle starting a chat
                if(option == "--chat"):
                    self.enter_chat(recv_user)

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
