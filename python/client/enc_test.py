#!/usr/bin/env python3

import os
import time
import json
import sys
#sys.path.append('C:\\Users\\rodri\\Documents\\School\\SENG 360\\__project\\branch\\__main\\seng360-a3\\python')

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

from encryption import User
from server.DatabaseConnection import DatabaseConn

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
    # u2_msg1 = "First message from user2 to user1"
    # # print("Testing send_msg method\n")
    # print(user2.username, " -    Sending message to: ", user1.username)
    # u2_enc_msg1 = user2.encrypt_msg(user1.username, u2_msg1)
    # print(u2_enc_msg1)
    # print()
    
    # # print("Testing recv_msg method\n")
    # print(user1.username, " -   Receiving message from: ", user2.username)
    # u2_dec_msg1 = user1.decrypt_msg(user2.username, u2_enc_msg1)
    # print(u2_dec_msg1)
    # print()

    # if(u2_dec_msg1 != u2_msg1):
    #     print("ERROR - Messages don't match")
    #     return


    # u2_msg2 = "Second message from user2 to user1"
    # # print("Testing send_msg method\n")
    # print(user2.username, " -    Sending message to: ", user1.username)
    # u2_enc_msg2 = user2.encrypt_msg(user1.username, u2_msg2)
    # print(u2_enc_msg2)
    # print()
    
    # # print("Testing recv_msg method\n")
    # print(user1.username, " -   Receiving message from: ", user2.username)
    # u2_dec_msg2 = user1.decrypt_msg(user2.username, u2_enc_msg2)
    # print(u2_dec_msg2)
    # print()

    # if(u2_dec_msg2 != u2_msg2):
    #     print("ERROR - Messages don't match")
    #     return


    # u1_msg1 = "First message from user1 to user2"
    # # print("Testing send_msg method\n")
    # print(user1.username, " -    Sending message to: ", user2.username)
    # u1_enc_msg1 = user1.encrypt_msg(user2.username, u1_msg1)
    # print(u1_enc_msg1)
    # print()
    
    # # print("Testing recv_msg method\n")
    # print(user2.username, " -   Receiving message from: ", user1.username)
    # u1_dec_msg1 = user2.decrypt_msg(user1.username, u1_enc_msg1)
    # print(u1_dec_msg1)
    # print()

    # if(u1_dec_msg1 != u1_msg1):
    #     print("ERROR - Messages don't match")
    #     return

    #################################
    ##### Test image encryption #####
    #################################

    # open image and convert to bytes
    # with open("shrek.png", "rb") as image:
    #     b64string = base64.b64encode(image.read())

    # # convert img bytes to string
    # img_string = b64string.decode()
    

    # # Send image from user1 to user2
    # print("Sending message as: ", user1.username)
    # user1.send_msg(user2.username, img_string)
    # print()

    # # Receive image as user2 from user1
    # recv_img_string = user2.recv_msg(user1.username)

    # # Encode string
    # encoded_img_string = recv_img_string.encode()
    
    # # Convert encoded string to bytearray
    # img_bytes = bytearray(encoded_img_string)
    
    # # Convert bytearray to .png
    # f = io.BytesIO(base64.b64decode(img_bytes))

    # # Save image
    # pilimage = Image.open(f)
    # pilimage = pilimage.save("shrek_recv.png")
    # show_img = Image.open(pilimage)
    # show_img.show()



if __name__ == "__main__":
    main()

