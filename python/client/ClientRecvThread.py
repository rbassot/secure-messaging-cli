#!/usr/bin/env python3

import binascii
from sys import *
import os
from time import *
from socket import *
from threading import *
from queue import *
import json
import ast
#from PIL import Image

import config
from encryption import User
import binascii

'''
Basic ClientRecvThread class for the client-side to continually listen to the server.
'''

class ClientRecvThread(Thread):
    def __init__(self, socket, address, username):    #Inherit from Thread class
        Thread.__init__(self) #provide a common event for interthread communication between send/receive threads
        self.sock = socket
        self.addr = address
        self.username = username
        self.enc_user = None

        if(not config.username):
            self.enc_user = User(username)
            config.username = self.enc_user
        else:
            self.enc_user = config.username

    
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
            print("Error acquiring the lock for input!")
            return

    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        return

    
    def join_chat(self, other_username):
        #initial chat welcoming
        self.locked_print('\033[1m' + "Now chatting with " + str(other_username) + "." + '\033[0m')
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
                # message_json = ast.literal_eval(message_json)

                #print out the formatted message in blue to the client console
                if(message_json['command'] == 'message-recv'):
                    # convert str message to hex, then to a bytes type
                    enc_msg_hex = message_json['message'].encode('utf-8')
                    enc_msg_bytes = binascii.unhexlify(enc_msg_hex)

                    # decrypt the AESGCM-encrypted message
                    decrypt_msg = self.enc_user.decrypt_msg(other_username, enc_msg_bytes, False)

                    message_str = str(other_username) + ": " + str(decrypt_msg)
                    self.locked_print('\033[94m' + message_str + '\033[0m')

                #server-sent notification that the chat was closed
                elif(message_json['command'] == 'exit-chat'):
                    self.locked_print('\033[1m' + message_json['message'] + '\033[0m')

                    #reset the shared connected_username variable
                    config.connected_username = None

                    #release the blocked sender thread
                    config.shared_event.set()
                    config.shared_event.clear()
                    return


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
        config.shared_event.clear()

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
        #ask user if connection should be established
        config.connected_username = send_username
        self.locked_print("Would you like to chat with " + send_username + "? Answer Y/N")
        
        #wait on SendThread to accept the request
        config.shared_event.wait()
        #create formatted response string for the server
        resp_to_connect = (json.dumps({
            'command':'accept-chat-req',
            'response':'SUCCESS', 
            'send_username': send_username, 
            'recv_username':self.username,
            'message':'The other client accepted the chat request.'
        })).encode()
        self.sock.send(resp_to_connect)

        #set the event such that this client's sender thread can continue
        #self.event.set() REMOVE THIS?

        #listen to the new chat
        #receiver-side user chat scenario
        self.clear_screen()
        self.locked_print("You accepted to join the chat.")
        sleep(1)
        self.join_chat(send_username)


    def format_message_history(self, other_username, message_list):
        #format each message list and print to client screen
        self.clear_screen()
        self.locked_print("")
        self.locked_print("--- Conversation history with " + str(other_username) + ": ---")

        for row in message_list:
            try:
                #decrypt the sent messages from the server, then format and print to screen
                encr_message = str(row[4])
                # #decrypt...

                enc_msg_hex = encr_message.encode('utf-8')
                enc_msg_bytes = binascii.unhexlify(enc_msg_hex)

                #own messages to the other client (outgoing)
                if(str(row[2]) == self.username):
                    decrypted_msg = self.enc_user.decrypt_msg(other_username, enc_msg_bytes, True)
                    message = decrypted_msg
                    self.locked_print("You: " + message)

                #own messages from the other client (incoming)
                elif(str(row[2]) == other_username):
                    decrypted_msg = self.enc_user.decrypt_msg(other_username, enc_msg_bytes, False)
                    message = decrypted_msg
                    message_str = other_username + ": " + message
                    self.locked_print('\033[94m' + message_str + '\033[0m')

            except Exception as e:
                self.locked_print(e)
                return

        self.locked_print("")
        return


    def listen(self):
        running = True

        while running: #test if an event trigger is needed to break out of this loop
            try:
                # getting size of serialized data
                data = b''
                part = b''

                while True:
                    part = self.sock.recv(1024)
                    data += part

                    if len(part) < 1024:
                        break
                
                server_data = data
                server_data = server_data.decode()

                #server closed the connection - terminate the threads
                if not(server_data):
                    return 1

                #parse the server's message into a dictionary
                server_resp = json.loads(server_data)
                # server_resp = ast.literal_eval(server_resp)

                #check server response type for state of the response
                #self.locked_print("Server response type: " + str(server_resp['response']))

                #Enter Chat Part 2 - receive chat request from a sender client
                if(server_resp['command'] == 'req-chat-from'):
                    self.clear_screen()
                    self.accept_chat_req(server_resp['send_username'])

                #Enter Chat Part 6 - receive 'new chat' response from a receiver client
                elif(server_resp['command'] == 'chat-confirmed'):
                    self.confirm_chat_opened(server_resp['message'], server_resp['recv_username'])

                #handle receiving conversation history from the server
                elif(server_resp['command'] == 'history'):
                    #destringify the message list back into a list - apply literal_eval again
                    # message_list = ast.literal_eval(server_resp['message_list'])
                    message_list = server_resp['message_list']
                    if message_list:
                        self.format_message_history(server_resp['other_username'], message_list)
                    else:
                        self.locked_print("")
                        self.locked_print("There is no message history with " + server_resp['other_username'] + " to be displayed.")

                    #release the SendThread to ask for input again
                    config.shared_event.set()
                    config.shared_event.clear()

                #handle deleting conversation history with a specific client from the server
                elif(server_resp['command'] == 'delete-history'):
                    self.locked_print(server_resp['message'])
                    config.shared_event.set()
                    config.shared_event.clear()

                #handle deleting ALL conversation histories - required at the end of every session
                elif(server_resp['command'] == 'delete-all-histories'):
                    self.locked_print(server_resp['message'])
                    config.shared_event.set()
                    config.shared_event.clear()
                    return 1

                #handle your account deletion - terminates the session
                elif(server_resp['command'] == 'delete-account'):
                    self.locked_print(server_resp['message'])
                    config.shared_event.set()
                    config.shared_event.clear()
                    return 1
                

            #exit on any exception type
            except Exception as e:
                self.locked_print(e)
                return 0

        return


    #Override: continuous execution of the receiver thread
    def run(self):
        self.listen()
        return
