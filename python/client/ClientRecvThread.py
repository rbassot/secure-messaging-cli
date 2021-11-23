#!/usr/bin/env python3

from sys import *
from os import *
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
    def __init__(self, socket, address, username, event):    #Inherit from Thread class
        Thread.__init__(self, args=(event)) #provide a common event for interthread communication between send/receive threads
        self.sock = socket
        self.addr = address
        self.event = event
        self.username = username

    
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


    def confirm_chat_opened(self, confirm_msg):
        self.clear_screen()
        self.locked_print(confirm_msg)

        #set the event such that the sender thread can continue
        self.event.set()

        return


    def print_received_message(self, sender, message):
        #print formatted message to the console
        self.locked_print(str(sender) + ": " + str(message))
        return

    
    #listener thread actually peforms a send here, to establish chat connection
    def accept_chat_req(self, send_username):
        #ask user if connectin should be established
        option = self.locked_input("Would you like to enter a chat with " + send_username + " ? Answer Y/N").lower()
        if(option != 'y'):
            return

        #create formatted response string for the server
        resp_to_connect = "{'command':'accept_chat_req', 'send_username':'%s', 'recv_username':'%s', 'message':'" + str(self.username) + "' has accepted the chat request.}"(send_username, self.username)
        serialized_resp = json.dumps(resp_to_connect).encode()
        self.sock.send(serialized_resp)

        #set the event such that this client's sender thread can continue
        #self.event.set()


    def listen(self):
        while True: #test if an event trigger is needed to break out of this loop
            try:
                server_data = self.sock.recv(1024).decode()

                #server closed the connection - terminate the threads
                if not(server_data):
                    return 1

                #parse the server's message into a dictionary
                server_resp = json.loads(server_data)
                server_resp = ast.literal_eval(server_resp)
                self.locked_print("Server response type: " + str(server_resp['response']))

                #Enter Chat Part 2 - receive chat request from a sender client
                if(server_resp['command'] == 'req_chat_from'):
                    self.accept_chat_req(server_resp['send_username'])

                #Enter Chat Part 4 - receive 'new chat' response from a receiver client
                if(server_resp['command'] == 'chat_confirmed'):
                    self.confirm_chat_opened(server_resp['message'])

                #receive chat estabished confirmation from a receiver client
                #if(server_resp['command'] == 'req_chat_from'):

                #handle regular message received case
                elif(server_resp['command'] == 'message_recv'):
                    self.print_received_message(server_resp['send_username'], server_resp['message'])

            except (KeyboardInterrupt, OSError):
                return 0


    #continuous execution of the receiver thread - function override
    def run(self):
        self.listen()
        return
