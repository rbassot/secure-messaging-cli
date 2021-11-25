#!/usr/bin/env python3

from sys import *
from os import *
from time import *
from socket import *
from threading import *
from queue import *
import json
import ast
#from PIL import Image

import config

'''
Basic ClientRecvThread class for the client-side to continually listen to the server.
'''

class ClientRecvThread(Thread):
    def __init__(self, socket, address, username):    #Inherit from Thread class
        Thread.__init__(self) #provide a common event for interthread communication between send/receive threads
        self.sock = socket
        self.addr = address
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

    
    def join_chat(self, other_username):
        #initial chat welcoming
        self.locked_print("Now chatting with " + str(other_username) + ".")
        self.locked_print("")

        #allow the SendThread to enter the chat
        config.shared_event.set()
        config.shared_event.clear()

        #listen to the chat and handle incoming messages
        while True: #test if an event trigger is needed to break out of this loop
            try:
                message_data = self.sock.recv(1024).decode()

                #chat connection was closed - stop listening
                if not(message_data):
                    return

                #parse the message into a dictionary
                message_json = json.loads(message_data)
                message_json = ast.literal_eval(message_json)

                #print out the formatted message to the client console
                if(message_json['command'] == 'message_recv'):
                    message_str = str(other_username) + ": " + str(message_json['message'])
                    self.locked_print('\033[94m' + message_str + '\033[0m')

            #exit chat on any exception
            except Exception as e:
                self.locked_print(str(e))
                return


    #Sender-side chat initialization for the RecvThread
    def confirm_chat_opened(self, confirm_msg, recv_username):
        self.clear_screen()
        self.locked_print(confirm_msg)
        sleep(1)

        #set the event such that the sender thread can continue
        config.shared_event.set()

        #listen to the new chat
        #receiver-side user chat scenario
        self.join_chat(recv_username)

        return


    def print_received_message(self, sender, message):
        #print formatted message to the console
        self.locked_print(str(sender) + ": " + str(message))
        return

    
    #Receiver-side chat initialization for the RecvThread
    #listener thread actually peforms a send here, to establish chat connection
    def accept_chat_req(self, send_username):
        #ask user if connecti0n should be established
        config.connected_username = send_username
        self.locked_print("Would you like to chat with " + send_username + "? Answer Y/N")
        
        #wait on SendThread to accept the request
        config.shared_event.wait()
        #create formatted response string for the server
        resp_to_connect = "{'command':'accept_chat_req', 'response':'SUCCESS', 'send_username':'%s', 'recv_username':'%s', 'message':'The other client accepted the chat request.'}"%(send_username, self.username)
        serialized_resp = json.dumps(resp_to_connect).encode()
        self.sock.send(serialized_resp)

        #set the event such that this client's sender thread can continue
        #self.event.set() REMOVE THIS?

        #listen to the new chat
        #receiver-side user chat scenario
        self.clear_screen()
        self.locked_print("You accepted to join the chat.")
        sleep(1)
        self.join_chat(send_username)


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
                    self.clear_screen()
                    self.accept_chat_req(server_resp['send_username'])

                #Enter Chat Part 6 - receive 'new chat' response from a receiver client
                if(server_resp['command'] == 'chat_confirmed'):
                    self.confirm_chat_opened(server_resp['message'], server_resp['recv_username'])

                #receive chat estabished confirmation from a receiver client
                #if(server_resp['command'] == 'req_chat_from'):

                #Pretty sure this is unneeded, due to listener thread handling chats in 'join_chat()'
                '''#handle regular message received case
                elif(server_resp['command'] == 'message_recv'):
                    self.print_received_message(server_resp['send_username'], server_resp['message'])'''

            except (KeyboardInterrupt, OSError):
                return 0


    #continuous execution of the receiver thread - function override
    def run(self):
        self.listen()
        return
