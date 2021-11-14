#!/usr/bin/env python3

from sys import *
from socket import *
from threading import *
from sqlite3 import * #For future database implementation
from os import *
from time import *
import json
import ast

from ClientSendThread import ClientSendThread
from ClientRecvThread import ClientRecvThread


#----- Client Parameters -----
SERVER_HOST = '127.0.0.1'           #bind to public IP
SERVER_PORT = 50007
sock = socket(AF_INET, SOCK_STREAM) #connection object to the server
client_username = None
client_key = None                   #dictionary of client keys needed for user authorization
threads = []

def clear_screen():
    system('clear')


def login_attempt():
    clear_screen()
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
    except:
        print("Something went wrong...")
        return 0


def login_or_register():
    #offer client login options
    sleep(1)
    clear_screen()
    print()
    print("----- Welcome to Python CLI Secure Messaging! -----")
    print("OPTIONS:")
    print("--login          Log in to an existing user account.")
    print("--register       Create a new user account.")
    print("--exit           Gracefully exit Python CLI Secure Messaging.")
    print()

    #user option loop
    while True:

        try:
            #get user's option selection
            option = input(">> ")

            if not option:
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
                #To implement
                pass

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
    while True:

        #initial login/registration handling
        if(not login_or_register()):
            break

        #create an object able to stop a running thread immediately
        pill2kill = Event()

        #user has logged in: create 2 threads - one for sending, one for receiving
        global threads
        send_thread = ClientSendThread(sock, (SERVER_HOST, SERVER_PORT), client_username, pill2kill)
        threads.append(send_thread)
        recv_thread = ClientRecvThread(sock, (SERVER_HOST, SERVER_PORT), pill2kill)
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
                pill2kill.set()
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