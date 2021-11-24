from threading import Lock

#thread lock needed for resource contention - stdout file descriptor
lock = Lock()

#variable to store username of the client at other end of connection - share between threads
#mainly needed for the receiver-side client to determine who to send to in its SendThread
connected_username = None