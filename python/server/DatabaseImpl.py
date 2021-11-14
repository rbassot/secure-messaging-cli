#!/usr/bin/env python3

from sys import *
from socket import *
import sqlite3
import json
import ast
#from PIL import Image

'''
Database Implementation class to handle the server's database resource (SQLite3 DB).
'''

class DatabaseImpl():
    def __init__(self):
        self.db_connection = sqlite3.connect('python-sm.db')
        self.create_Accounts_table()
        self.create_Messages_table()

    def get_row_count(self, table_name):
        query = "SELECT COUNT(*) FROM " + str(table_name) + ";"
        return int(self.db_connection.execute(query))

    def add_new_account(self, id, first_name, last_name, username, password):
        data = [(id, first_name, last_name, username, password)]
        query = '''INSERT INTO Account VALUES(?, ?, ?, ?, ?)'''
        self.db_connection.execute(query, data)

    def create_Accounts_table(self):
        query = '''CREATE TABLE Account(
                    id INTEGER NOT NULL AUTOINCREMENT,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT PRIMARY KEY,
                    password TEXT);
                    '''
        self.db_connection.execute(query)


    def create_Messages_table(self):
        query = '''CREATE TABLE Message(
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    send_username TEXT,
                    recv_username TEXT,
                    encr_message TEXT);
                    '''
        #Do we need to store any keys here??
        self.db_connection.execute(query)

