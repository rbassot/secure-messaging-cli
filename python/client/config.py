from threading import Lock

#thread lock needed for resource contention - stdout file descriptor
lock = Lock()