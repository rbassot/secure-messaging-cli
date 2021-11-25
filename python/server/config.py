from threading import Event

#required globals for the program
connections = {}        #client username as index; Socket connection obj as value
authorized_users = {}

#event object such that two ServerThreads can synchronize with eachother (for chat establishment)
shared_event = Event()
shared_event.clear()

