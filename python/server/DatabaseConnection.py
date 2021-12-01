#!/usr/bin/env python3

import os.path
from sys import *
from socket import *
import sqlite3
import json
import ast
#from PIL import Image

'''
Database Connection class to handle communication from a server thread to the server's database resource (SQLite3 DB).
'''

class DatabaseConn():
    def __init__(self):
        self.db_connection = sqlite3.connect('python-sm.db', check_same_thread=False)
        #self.db_cursor = self.db_connection.cursor()

        #create both tables initially, if they are not created already
        self.create_Account_table()
        self.create_Message_table()


    def get_Account_row_count(self):
        cursor = self.db_connection.cursor()
        query = "SELECT COUNT(*) FROM Account"
        cursor.execute(query)
        count = int(cursor.fetchone()[0])
        return count


    def get_Message_row_count(self):
        cursor = self.db_connection.cursor()
        query = "SELECT COUNT(*) FROM Message"
        cursor.execute(query)
        count = int(cursor.fetchone()[0])
        return count

    def get_KeyBundle(self, recv_username):
        # See https://docs.python.org/3/library/sqlite3.html#row-objects for more info
        self.db_connection.row_factory = sqlite3.Row 
        cursor = self.db_connection.cursor()
        data = [recv_username]
        query = "SELECT * FROM KeyBundle WHERE username = ?"
        cursor.execute(query, data)
        return cursor.fetchone()

    def get_OTPK(self, recv_username):
        # See https://docs.python.org/3/library/sqlite3.html#row-objects for more info
        self.db_connection.row_factory = sqlite3.Row
        cursor = self.db_connection.cursor()
        data = [recv_username]
        query = "SELECT OneTimePrekey FROM OTPK WHERE username = ?"
        cursor.execute(query, data)
        return cursor.fetchone()

    def get_count_OTPK(self, username):
        cursor = self.db_connection.cursor()
        data = [username]
        query = "SELECT COUNT(*) FROM OTPK WHERE username = ?"
        cursor.execute(query, data)
        count = int(cursor.fetchone()[0])
        return count

    def insert_new_account(self, first_name, last_name, username, password):
        #get row count for ID field
        try:
            cursor = self.db_connection.cursor()
            row_count = self.get_Account_row_count()
            data = [row_count + 1, first_name, last_name, username, password]
            query = "INSERT INTO Account(id, first_name, last_name, username, password) VALUES(?, ?, ?, ?, ?)"
            cursor.execute(query, data)
            self.db_connection.commit()
            return 1
        
        except Exception as e:
            print("INSERT ACCOUNT ERROR: " + str(e))
            return 0


    def insert_new_message(self, owner_username, send_username, recv_username, encr_message):
        #get row count for ID field
        try:
            cursor = self.db_connection.cursor()
            row_count = self.get_Message_row_count()
            data = [row_count + 1, owner_username, send_username, recv_username, encr_message]
            query = "INSERT INTO Message(id, owned_username, send_username, recv_username, encr_message) VALUES(?, ?, ?, ?, ?)"
            cursor.execute(query, data)
            self.db_connection.commit()
            return 1

        except Exception as e:
            print("INSERT MESSAGE ERROR: " + str(e))
            return 0

    def insert_KeyBundle(self, username, public_IK, public_ED, public_SPK, SIG):
        try:
            cursor = self.db_connection.cursor()

            data = [username, public_IK, public_ED, public_SPK, SIG]
            query = "INSERT INTO KeyBundle VALUES(?, ?, ?, ?, ?)"
            cursor.execute(query, data)
            self.db_connection.commit()
            return 1
        
        except Exception as e:
            print("INSERT ERROR: " + str(e))
            return 0


    def insert_OTKP(self, username, public_OTPK):
        try:
            cursor = self.db_connection.cursor()

            data = [username, public_OTPK]
            query = "INSERT INTO OTPK VALUES(?, ?)"
            cursor.execute(query, data)
            self.db_connection.commit()
            return 1
        
        except Exception as e:
            print("INSERT ERROR: " + str(e))
            return 0

    def delete_OTPK(self, username, public_OTPK):
        try:
            cursor = self.db_connection.cursor()

            data = [username, public_OTPK]
            query = "DELETE FROM OTPK WHERE username = ? AND OneTimePrekey = ?"
            cursor.execute(query, data)
            self.db_connection.commit()
            return 1
        
        except Exception as e:
            print("DELETE OneTimePrekey ERROR: " + str(e))
            return 0

    def get_message_history(self, send_username, recv_username):
        cursor = self.db_connection.cursor()
        data = [send_username]
        query = "SELECT * FROM 'Message' WHERE owned_username LIKE ?"
        cursor.execute(query, data)
        messages = cursor.fetchall()
        return messages


    #deletes the converssation history for the requester's side only
    def delete_message_history(self, req_username, other_username):
        try:
            cursor = self.db_connection.cursor()
            data = [req_username, other_username, other_username]
            query = "DELETE FROM Message WHERE owned_username LIKE ? AND (send_username LIKE ? OR recv_username LIKE ?)"
            cursor.execute(query, data)
            self.db_connection.commit()
            return 1

        except Exception as e:
            print("DELETE HISTORY ERROR: " + str(e))
            return 0


    #deletes all conversation histories for a client - required once a sesssion is terminated!
    def delete_all_histories(self, req_username):
        try:
            cursor = self.db_connection.cursor()
            data = [req_username]
            query = "DELETE FROM Message WHERE owned_username LIKE ?"
            cursor.execute(query, data)
            self.db_connection.commit()
            return 1

        except Exception as e:
            print("DELETE HISTORY ERROR: " + str(e))
            return 0


    def is_valid_username_password(self, username, password):
        try:
            cursor = self.db_connection.cursor()
            data = [username, password]
            query = "SELECT * FROM Account WHERE username = ? AND password = ?"
            cursor.execute(query, data)
            entries_matched = len(cursor.fetchall())
            print("Amount of tuples returned: " + str(entries_matched))

            #check that there is exactly one entry matching the user/pass pair
            if(entries_matched != 1):
                return 0

            #login successful
            else: return 1

        except Exception as e:
            print("LOGIN CHECK ERROR: " + str(e))
            return 0

    
    def is_registered_user(self, username):
        try:
            cursor = self.db_connection.cursor()
            data = [username]
            query = "SELECT * FROM Account WHERE username = ?"
            cursor.execute(query, data)
            entries_matched = len(cursor.fetchall())
            #print("Amount of tuples returned: " + str(entries_matched))

            #check that there is exactly one entry matching the desired username
            if(entries_matched != 1):
                return 0

            #user retrieved
            else: return 1

        except Exception as e:
            print("FIND USER ERROR: " + str(e))
            return 0


    def create_Account_table(self):
        #safely check if table is already created before creating it
        cursor = self.db_connection.cursor()
        query = '''CREATE TABLE IF NOT EXISTS Account(
                    id INTEGER NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT NOT NULL PRIMARY KEY,
                    password TEXT)
                    '''
        cursor.execute(query)
        self.db_connection.commit()


    def create_Message_table(self):
        #safely check if table is already created before creating it
        cursor = self.db_connection.cursor()
        query = '''CREATE TABLE IF NOT EXISTS Message(
                    id INTEGER NOT NULL PRIMARY KEY,
                    owned_username TEXT NOT NULL,
                    send_username TEXT NOT NULL,
                    recv_username TEXT NOT NULL,
                    encr_message TEXT)
                    '''
        #Do we need to store any keys here??
        cursor.execute(query)
        self.db_connection.commit()

    def create_KeyBundle_table(self):
        cursor = self.db_connection.cursor()
        query = ''' CREATE TABLE IF NOT EXISTS KeyBundle(
                        username TEXT PRIMARY KEY,
                        IdentityKey TEXT NOT NULL,
                        EdwardsKey TEXT NOT NULL, 
                        SignedPrekey TEXT NOT NULL,
                        Signature TEXT NOT NULL
                    )        
                '''
        cursor.execute(query)
        self.db_connection.commit()


    def create_OTPK_table(self):
        cursor = self.db_connection.cursor()
        query = ''' CREATE TABLE IF NOT EXISTS OTPK(
                        username TEXT NOT NULL,
                        OneTimePrekey TEXT NOT NULL,
                        PRIMARY KEY(username, OneTimePrekey)
                    )
                '''
        cursor.execute(query)
        self.db_connection.commit()
