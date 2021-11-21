from threading import Lock

#thread lock needed for resource contention
lock = Lock()

#required globals for the program
connections = []
