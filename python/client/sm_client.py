#!/usr/bin/env python3

from sys import *
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


def display_options():
    #main menu introduction
    print()
    print("----- Welcome to the main menu -----")

    #display all user options
    print("OPTIONS:")
    print("--chat:<username>                Start a secure chat with an existing user.")
    print("--quit-chat                      Quit the current chat and return to the main menu.")
    print("--history:<username>             View your conversation history with a user.")
    print("--delete-history:<username>      Delete your conversation history with a specific user.")
    print("--logout                         Log out of your account and return to the main menu.")
    print("--delete-account                 Delete your account and return to the main menu.")
    print("--exit                           Gracefully logout and exit Python CLI Secure Messaging.")
    print("--options                        Display available options from this menu.")
    print()
    #**should add functionality for a user to view an image that was attached in a previous message**




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
    except Exception as e:
        print(e)


def login_or_register():

    #offer client login options
    print()
    print("----- Welcome to Python CLI Secure Messaging! -----")
    print("OPTIONS:")
    print("--login          Log in to an existing user account.")
    print("--register       Create a new user account.")
    print("--exit           Gracefully exit Python CLI Secure Messaging.")
    print()

    #user option loop
    while True:
        option = input(">> ")

        try:
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

            else:
                print("Please pass a valid command.")
                continue

        #terminate the client on keyboard interrupt
        except KeyboardInterrupt:
            close_server_conn()



def close_server_conn():
    #notify the server of a closing connection
    closing_req = "{'command':'exit', 'username':'%s'}"%(client_username)
    #must encrypt the closing req data here (encryption manager?)
    serialized_req = json.dumps(closing_req).encode()
    sock.send(serialized_req)

    #wait for server confirmation
    server_resp = json.loads(sock.recv(1024).decode())
    server_resp = ast.literal_eval(server_resp)

    #close the client-side socket if response was successful
    if(server_resp['response'] == 'SUCCESS'):
        print()
        print("Connection was closed. Program is exiting gracefully.")
        return 1
        #exit(0)

    else:
        print("Exit attempt failed!")
        return 0

#To implement
def enter_chat(recv_username):
    pass


def parse_main_menu_input(input_str):
    #place arguments into a list
    args = input_str.split(":")

    #assert that there are only either 1 or 2 arguments
    if(len(args) > 2):
        raise ValueError("Please provide a command with 2 or less arguments.")

    elif(len(args) < 2):
        return args[0], None

    return args[0], args[1]


def main_menu():
    #continuously accept user input from the main menu
    while True:

        try:
            #get user input for writing a message
            user_input = input(">> ")

            #first parse the user input string
            option, recv_user = parse_main_menu_input(user_input)

            #handle starting a chat
            if(option == "--chat"):
                enter_chat(recv_user)

            #handle program exit
            elif(option == "--exit"):
                if(close_server_conn()):
                    break

            else:
                print("Please pass a valid command.")
                continue

        except ValueError as e:
            print(e)

        #terminate the client on keyboard interrupt
        except KeyboardInterrupt:
            close_server_conn()

    #terminate client program
    exit(0)   


def start_client():

    #create socket connection
    sock.connect((SERVER_HOST, SERVER_PORT))

    #receive connection message from server
    recv_msg = sock.recv(1024).decode()
    print(recv_msg)

    #--- Login Menu ---
    while True:

        #initial login/register options
        login_or_register()

        #first encounter with main menu - display options
        display_options()

        #--- Main Menu ---
        while True:
            #poll the server for messages
            #recv_msg = client_sock.recv(1024)
            #print(recv_msg)

            main_menu()


    sock.close()


if __name__ == "__main__":
    start_client()