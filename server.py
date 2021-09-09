#!/usr/bin/env python3
"""Server for multithreaded (asynchronous) chat application."""
from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, TCP_NODELAY
from threading import Thread
from datetime import datetime
import time
import signal
import sys

def sigterm_handler(_signo, _stack_frame):
    print("Exiting...")
    SERVER.close()
    sys.exit(0)
signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)
global log
log = []
active = []

def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        client, client_address = SERVER.accept()
        print("%s:%s has connected." % client_address)
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()

def saveLog():
    global log
    while(True):
        time.sleep(600) 
        if(log):
            print("Saving Log...")
            with open("server.log", "w+") as logfile:
                for item in log:
                    logfile.write("%s\n" % item.decode("utf8"))
            print("Saved.")


def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""

    name = client.recv(BUFSIZ).decode("utf8").lstrip(",|1234567890")
    clients[client] = name
    for elem in active:
        print(elem)
        client.send(bytes(elem))

    while True:
        msgsraw = client.recv(BUFSIZ)
        print(msgsraw)
        msgs = filter(None,msgsraw.decode("utf8").split("&&"))
        for msg in msgs:
            msg = bytes(msg, "utf8")
            if not bytes("!quit", "utf8") in msg:
                broadcast(msg, name)
            else:
                client.send(bytes("!quit", "utf8"))
                client.close()
                del clients[client]
                print("%s has left the chat." % name)
                break


def broadcast(msg, prefix=""):  # prefix is for name identification.
    """Broadcasts a message to all the clients."""
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    try:
        for sock in clients:
            sock.send(bytes(prefix+"||", "utf8")+msg+bytes("||"+current_time+"&&", "utf8"))
        log.append(bytes(prefix+"||", "utf8")+msg+bytes("||"+current_time, "utf8"))
        smsg = msg.decode("utf8")
        if(smsg.startswith("!rm")):
            smsgdate = smsg.split(" ")[1]
            [active.remove(elem) for elem in active if smsgdate+"&&" == elem.decode("utf8").split("||")[3]]
        else:
            active.append(bytes(prefix+"||", "utf8")+msg+bytes("||"+current_time+"&&", "utf8"))
        print(active)
    except BrokenPipeError:
        #print("BrokenPipe.. This probably shouldn't have happened...")
        pass

clients = {}
addresses = {}

HOST = ''
PORT = 33000
BUFSIZ = 1024
ADDR = (HOST, PORT)

SERVER = socket(AF_INET, SOCK_STREAM)
SERVER.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
SERVER.bind(ADDR)
if __name__ == "__main__":
    SERVER.listen(5)
    print("Waiting for connection...")
    ACCEPT_THREAD = Thread(target=accept_incoming_connections)
    saveLog_THREAD = Thread(target= saveLog)
    saveLog_THREAD.setDaemon(True)
    saveLog_THREAD.start()
    ACCEPT_THREAD.setDaemon(True)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()