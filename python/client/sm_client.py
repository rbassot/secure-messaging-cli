#!/usr/bin/env python3

from socket import *
from sqlite3 import * #For future database implementation
from os import *
from time import *
import json
import ast


#----- Client Parameters -----
SERVER_HOST = '127.0.0.1'           #bind to public IP
SERVER_PORT = 50007
sock = socket(AF_INET, SOCK_STREAM) #connection object to the server
client_username = None
client_key = None                   #dictionary of client keys needed for user authorization

def clear_screen():
    system('clear')


def login_attempt():
    username = input("Username: ")
    password = input("Password: ")

    try:
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
    except Exception as e:
        print(e)


def login_or_register():

    #offer client login options
    print()
    print("----- Welcome to Python CLI Secure Messaging! -----")
    print("OPTIONS:")
    print("--login          Log in to an existing user account.")
    print("--register       Create a new user account.")

    #user option loop
    while True:
        option = input("Select an option: ")

        #handle login
        if(option == "--login"):
            result = login_attempt()

            if(result):
                clear_screen()
                print("Logged in as " + client_username)
                break

        #handle account registration
        elif(option == "--register"):
            pass

        else:
            print("Please pass a valid command.")
            continue

    #FIX!!
    while True:
        pass


def start_client():

    #create socket connection
    sock.connect((SERVER_HOST, SERVER_PORT))

    #receive connection message from server
    recv_msg = sock.recv(1024).decode()
    print(recv_msg)

    #initial login/register options
    login_or_register()

    while True:
        #poll the server for messages
        #recv_msg = client_sock.recv(1024)
        #print(recv_msg)

        #get user input for writing a message
        send_msg = input("Send your message in format [@user:message]")

        if send_msg == 'exit':
            break
        else:
            sock.send(send_msg.encode())


    sock.close()


if __name__ == "__main__":
    start_client()