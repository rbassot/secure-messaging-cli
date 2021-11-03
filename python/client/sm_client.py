#!/usr/bin/env python3

from socket import *
from sqlite3 import * #For future database implementation


#----- Client Parameters -----
SERVER_HOST = '127.0.0.1'   #bind to public IP
SERVER_PORT = 50007
client_key = None           #dictionary of client keys needed for user authorization

def start_client():

    #create socket connection
    client_sock = socket(AF_INET, SOCK_STREAM)
    client_sock.connect((SERVER_HOST, SERVER_PORT))

    #receive connection message from server
    recv_msg = client_sock.recv(1024).decode()
    print(recv_msg)

    while True:
        #poll the server for messages
        #recv_msg = client_sock.recv(1024)
        #print(recv_msg)

        #get user input for writing a message
        send_msg = input("Send your message in format [@user:message]")

        if send_msg == 'exit':
            break
        else:
            client_sock.send(send_msg.encode())


    client_sock.close()


if __name__ == "__main__":
    start_client()