#!/usr/bin/env python3

from sys import *
from socket import *
from threading import *
from queue import *
from sqlite3 import * #For future database implementation
import os
from time import *
import json
import ast
import binascii

import config

from ClientSendThread import ClientSendThread
from ClientRecvThread import ClientRecvThread

from cryptography.hazmat.primitives import hashes

#----- Client Parameters -----
SERVER_HOST = '127.0.0.1'                    #bind to public IP
SERVER_PORT = 50007
sock = socket(AF_INET, SOCK_STREAM)          #connection object to the server for client-to-client interactions
#chat_socket = socket(AF_INET, SOCK_STREAM)   #connection object to the server to create 
client_username = None
client_key = None                            #dictionary of client keys needed for user authorization
threads = []

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
    return


def register_attempt():
    clear_screen()
    first_name = input("First name: ")
    last_name = input("Last name: ")
    username = input("Username: ")
    password = input("Password: ")

    try:
        # # encrypt pass
        # reg_digest = hashes.Hash(hashes.SHA256())
        # salt = os.urandom(16)
        # reg_digest.update(password.encode('utf-8'))
        # bytes_enc_pass = reg_digest.finalize()
        # bytes_enc_pass += salt  # cant convert to str
        # salt = None
        # # parse encrypted_pass to str format and send to server
        # hex_enc_pass = binascii.hexlify(bytes_enc_pass)     # hexlift bytes -> can convert to str
        # str_enc_pass = hex_enc_pass.decode()                # encrypted_pass in str format

        #send formatted login data to server
        login_req = "{'command':'register', 'first':'%s', 'last':'%s', 'username':'%s', 'password':'%s'}"%(first_name, last_name, username, password)
        #must encrypt the login data here (encryption manager?)
        serialized_req = json.dumps(login_req).encode()
        sock.send(serialized_req)

        #receive response from server
        server_resp = json.loads(sock.recv(1024).decode())
        server_resp = ast.literal_eval(server_resp)
        print("Server response type: " + str(server_resp['response']))

        if(server_resp['response'] == 'SUCCESS'):
            print(server_resp['message'])
            return 1

        elif(server_resp['response'] == 'FAILURE'):
            print("Registration attempt failed!")
            return 0

    #FIX!!
    except:
        print("Something went wrong...")
        return 0


def login_attempt():
    clear_screen()
    username = input("Username: ")
    password = input("Password: ")

    try:
        # retrive hash ed pass from server
        # get salt
        # calculate hash from password typed
        # compare if hashes are equal!

        # encode_pass = entries_matched['password'].encode('utf-8')
        # reg_enc_pass = binascii.unhexlify(encode_pass)
        # print(reg_enc_pass)

        # # get salt
        # salt = reg_enc_pass[-16:]

        # # hash types password and compare
        # login_digest = hashes.Hash(hashes.SHA256())
        # login_digest.update(password.encode('utf-8'))
        # enc_pass = login_digest.finalize()
        # enc_pass += salt
        # salt = None
        
        # print(enc_pass)

        # if(enc_pass != reg_enc_pass):
        #     return 0
        # else:
        #     return 1

        #send formatted login data to server
        login_req = "{'command':'login', 'username':'%s', 'password':'%s'}"%(username, password)
        #must encrypt the login data here (encryption manager?)
        serialized_req = json.dumps(login_req).encode()
        sock.send(serialized_req)

        #receive response from server
        server_resp = json.loads(sock.recv(1024).decode())
        server_resp = ast.literal_eval(server_resp)
        print("Server response type: " + str(server_resp['response']))

        if(server_resp['response'] == 'SUCCESS'):
            print("Log in attempt was successful.")
            global client_username
            client_username = username
            sleep(1)
            return 1

        elif(server_resp['response'] == 'FAILURE'):
            print("Log in attempt failed!")
            return 0

    #FIX!!
    except:
        print("Something went wrong...")
        return 0


def display_login_options():
    #display welcome message & user login menu options
    print("")
    print("----- Welcome to Python CLI Secure Messaging! -----")
    print("OPTIONS:")
    print("--login          Log in to an existing user account.")
    print("--register       Create a new user account.")
    print("--exit           Gracefully exit Python CLI Secure Messaging.")
    print("")


def login_or_register():
    #offer client login options
    sleep(1)
    clear_screen()
    display_login_options()

    #user option loop
    while True:

        try:
            #get user's option selection
            option = input(">> ")

            if not option:
                continue

            #handle options
            if(option == "--options"):
                clear_screen()
                display_login_options()
                continue

            #handle login
            if(option == "--login"):
                result = login_attempt()

                if(result):
                    clear_screen()
                    print("Logged in as " + client_username)
                    break

            #handle account registration
            elif(option == "--register"):
                result = register_attempt()
                
                if(result):
                    clear_screen()
                    print("Account registration successful.")
                    continue

            #handle program exit
            elif(option == "--exit"):
                close_server_conn()
                return 0

            else:
                print("Please pass a valid command.")
                continue

        #terminate the client on keyboard interrupt
        except KeyboardInterrupt:
            close_server_conn()
            return 0

    return 1


def close_server_conn():
    #notify the server that connection should be terminated
    sock.shutdown(SHUT_RDWR)
    sock.close()
    print("Connection was closed. Program is exiting gracefully.")
    return


def start_client():

    #create socket connection
    sock.connect((SERVER_HOST, SERVER_PORT))

    #receive connection message from server
    recv_msg = sock.recv(1024).decode()
    print(recv_msg)

    #--- Login Menu ---
    while True: #TO FIX: Needs to handle reconnecting to the server - The server should drop the prev closed connection then?

        #initial login/registration handling
        if(not login_or_register()):
            break

        #user has logged in: create 2 threads - one for sending, one for receiving
        global threads
        send_thread = ClientSendThread(sock, (SERVER_HOST, SERVER_PORT), client_username)
        threads.append(send_thread)
        recv_thread = ClientRecvThread(sock, (SERVER_HOST, SERVER_PORT), client_username)
        threads.append(recv_thread)

        #set threads to daemons for auto cleanup on program exit
        send_thread.daemon = True
        recv_thread.daemon = True
        
        send_thread.start()
        recv_thread.start()

        #delay loop to check for connection closing
        while True:
            try:
                send_thread.join()
                recv_thread.join()

                #return to login menu scope
                print("Logging out of " + client_username)
                break

            #exit program - daemon threads are cleaned up automatically
            except (BaseException, KeyboardInterrupt) as e:
                print("Gracefully closing the client program.")
                return

    return


if __name__ == "__main__":
    start_client()