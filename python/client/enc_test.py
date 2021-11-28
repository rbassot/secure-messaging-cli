#!/usr/bin/env python3

import os
import time
import json
import sys
sys.path.append('C:\\Users\\rodri\\Documents\\School\\SENG 360\\__project\\secure_message\\enc_branch\\seng360-a3\\python')

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

from encryption import User
from server.DatabaseImpl import DatabaseConn

# Image conversion
from PIL import Image
import io
import base64

def main():
    print("----- Testing Encryption Implementation -----")
    print()

    server = DatabaseConn()

    print("Creating user1, Alice...")
    user1 = User(username="alice")
    print(server.get_KeyBundle(user1.username))
    print()

    print("Creating user2, Bob...")
    user2 = User(username="bob")
    print(server.get_KeyBundle(user2.username))
    print()


    ####################################
    ##### Test send + recv methods #####
    ####################################

    # print("Testing send_msg method")
    # print("Sending message as: ", user2.username)
    # user2.send_msg(user1.username, "hello from user2")
    # print()
    
    # print("Testing recv_msg method")
    # print(user1.username, " -   Received as message from: ", user2.username)
    # user1.recv_msg(user2.username)
    # print()


    #################################
    ##### Test image encryption #####
    #################################

    # open image and convert to bytes
    with open("shrek.png", "rb") as image:
        b64string = base64.b64encode(image.read())

    # convert img bytes to string
    img_string = b64string.decode()
    

    # Send image from user1 to user2
    print("Sending message as: ", user1.username)
    user1.send_msg(user2.username, img_string)
    print()

    # Receive image as user2 from user1
    recv_img_string = user2.recv_msg(user1.username)

    # Encode string
    encoded_img_string = recv_img_string.encode()
    
    # Convert encoded string to bytearray
    img_bytes = bytearray(encoded_img_string)
    
    # Convert bytearray to .png
    f = io.BytesIO(base64.b64decode(img_bytes))

    # Save image
    pilimage = Image.open(f)
    pilimage = pilimage.save("shrek_recv.png")
    show_img = Image.open(pilimage)
    show_img.show()



if __name__ == "__main__":
    main()

