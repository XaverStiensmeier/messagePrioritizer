#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import tkinter
from tkinter import ttk
from tkinter import messagebox
import sys
import time
import signal
import audioFile
global sound_thread
sound_thread = None
index = None
sounds = {
    "-1": "oc.wav",
    "1" : "fanfare2.wav",
    "2" : "fanfare.wav",
    "4" : "receive.wav",
    "8" : "receiveQ.wav"
}
global counter
counter = 0
def sigterm_handler(_signo, _stack_frame):
    global counter
    print("Exiting...")
    if(counter):
        quitExecutor()
    else:
        counter +=1
        quitHandler()
signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)

def quitHandler():
    client_socket.send(bytes("!quit","utf8"))
def quitExecutor():
    top.destroy()
    client_socket.close()
    sys.exit(0)

def getHighPrio():
    allIndizes = tree.get_children()
    allChildren = []
    for indize in allIndizes:
        allChildren.append(tree.item(indize)['values'])
    return min(allChildren, key = lambda t: t[1])

def removeItem(event):
    try:
        index = tree.selection()[0]
        date = tree.item(index)['values'][3]
        client_socket.send(bytes("!rm {}&&".format(date), "utf8"))
    except IndexError:
        pass

def removeItembyIndex(index):
    try:
        tree.delete(index)
        playSelectedSound("-1")
    except IndexError:
        pass

def removeItembyDate(date):
    allIndizes = tree.get_children()
    allChildren = []
    for indize in allIndizes:
        if(tree.item(indize)['values'][3] == date):
            removeItembyIndex(indize)

def recaller():
    global index
    while(True):
        print("Recalling...")
        waiter = 300
        priority = 1
        if(tree.get_children()):
            try:
                name,priority,content = getHighPrio()
                if(priority<8):
                    messagebox.showwarning("Aufgabe", name+": "+content+"\nPriorität: "+str(priority))
                else:
                    priority=1
            except (IndexError,tkinter.TclError) as e:
                priority = 9
                pass
        time.sleep(waiter*priority)

def select_entry(event):
    global index
    try:
        index = tree.selection()[0]
        content = tree.item(index)['values'][2]
        messagebox.showinfo("Aufgabe", content)
    except IndexError:
        pass

#https://stackoverflow.com/questions/1966929/tk-treeview-column-sort
def treeview_sort_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(key=lambda t: int(t[0]), reverse=reverse)
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)
    tv.heading(col,
               command=lambda: treeview_sort_column(tv, col, not reverse))

def playSound(file):
    a = audioFile.AudioFile(file)
    a.playclose()

def playSelectedSound(number):
    global sound_thread
    if(not sound_thread or not sound_thread.is_alive()):
        sound_thread = Thread(target=playSound, args=(["src/audio/{}".format(sounds[number])]), kwargs={})
        sound_thread.start()

def showMessagebox(text):
    messagebox.showinfo("Neue wichtige Aufgabe", text)
def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msgs = client_socket.recv(BUFSIZ).decode("utf8")
            msgs = list(filter(None,msgs.split("&&")))
            for msg in msgs:
                handleReceive(msg)
        except (OSError, IndexError) as e:  # Possibly client has left the chat.
            print("No connection... (OS or IndexError)")
            print(e)
            quitExecutor()
        except tkinter.TclError as e:
            print("No connection... (TclError)")

def handleReceive(msg):
    data = msg.split("||")
    if(data[1].startswith("!rm")):
        removeItembyDate(data[1].split(" ")[1])
    elif("quit!" in data[1]):
        quitExecutor()
    else:
        if(int(data[1])<9):
            playSelectedSound(data[1])
            if(int(data[1])==1):
                top.lift()
                showMessagebox(data[2])
                #text_thread = Thread(target=showMessagebox, args=([data[2]]), kwargs={})
                #text_thread.start()
        tree.insert('', 'end', values=data)
    treeview_sort_column(tree,"Prio", False)

def send(event=None, prefix=9):  # event is passed by binders.
    """Handles sending of messages."""
    msg = my_msg.get()
    if(msg):
        my_msg.set("")  # Clears input field.
        client_socket.send(bytes(str(prefix)+"||"+msg.replace("&&","&").replace("||","|")+"&&", "utf8"))

def on_closing(event=None):
    """This function is to be called when the window is closed."""
    if messagebox.askokcancel("Beenden", "Bist du sicher, dass du das Programm beenden möchtest?"):
        quitHandler()

top = tkinter.Tk()
top.title("Priorime")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()  # For the messages to be sent.
scrollbar = tkinter.Scrollbar(messages_frame)  # To navigate through past messages.
# Following will contain the messages.
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
tree = ttk.Treeview(messages_frame, columns=["Wer", "Prio","Aufgabe", "Zeit"], show='headings')
tree.column("Aufgabe", width=300)
tree.column("Wer", width=50)
tree.column("Prio", width=50)
tree.column("Zeit", width=50)
tree.bind('<<TreeviewSelect>>', select_entry)
tree.bind('r',removeItem)
for column in ["Wer", "Prio", "Aufgabe","Zeit"]:
    tree.heading(column, text=column)
tree.pack(side="left", fill=tkinter.BOTH)
messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack(fill="both")
ni_button = tkinter.Button(text="Unwichtig", command=lambda: send(prefix=8))
ni_button.pack(side="left", fill="both", expand=True)
med_button = tkinter.Button(text="Medium", command=lambda: send(prefix=4))
med_button.pack(side="left", fill="both", expand=True)
vi_button = tkinter.Button(text="Extrem wichtig", command=lambda: send(prefix=1))
vi_button.pack(side="right", fill="both", expand=True)
i_button = tkinter.Button(text="Wichtig", command=lambda: send(prefix=2))
i_button.pack(side="right", fill="both", expand=True)

top.protocol("WM_DELETE_WINDOW", on_closing)

#----Now comes the sockets part----
with open("client.conf", "r") as client:
    HOST,PORT = client.readline().strip("\n").split(",")
    NAME = client.readline().strip("\n")
    RECALLER = not int(client.readline().strip("\n")) == 0
if(not HOST):
    HOST = input('Enter host: ')
if(not PORT):
    PORT = input('Enter port: ')
PORT = int(PORT)
if(not NAME):
    NAME = input('Enter name: ')

BUFSIZ = 1024
ADDR = (HOST, PORT)

client_socket = socket(AF_INET, SOCK_STREAM)
client_socket.connect(ADDR)
client_socket.send(bytes(NAME, "utf8"))
try:
    if(RECALLER):
        recaller_thread = Thread(target=recaller)
        recaller_thread.setDaemon(True)
        recaller_thread.start()

    receive_thread = Thread(target=receive)
    receive_thread.setDaemon(True)
    receive_thread.start()
except (KeyboardInterrupt, SystemExit):
    cleanup_stop_thread()
    sys.exit()
tkinter.mainloop()  # Starts GUI execution.