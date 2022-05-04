#!/usr/bin/env python3
"""Script for Tkinter GUI chat client."""
from socket import AF_INET, socket, SOCK_STREAM, SOL_SOCKET, SO_KEEPALIVE
from threading import Thread
import tkinter
from tkinter import ttk, messagebox, Toplevel, Frame, Label, CENTER
import sys
import time
import signal
import audioFile
import playsound

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

def popup(title="", text=""):
    # Create an instance of window
    win=Toplevel()

    # Set the geometry of the window
    win.geometry("700x350")

    # Create a frame widget
    frame=Frame(win, width=300, height=300)
    frame.grid(row=0, column=0, sticky="NW")

    # Create a label widget 
    label_title=Label(win, text=title, font='Arial 17 bold', wraplengt=650)
    label_title.place(relx=0.5, rely=0.1, anchor=CENTER)
    label_text=Label(win, text=text, font='Arial 15', wraplengt=650)
    label_text.place(relx=0.5, rely=0.23, anchor=CENTER)
    style = ttk.Style()
    style.configure("BW.GreenButton", background="green")
    b = tkinter.Button(win, text="Okay", width=25, font="Arial 15", command=win.destroy, bg="#00FF00")
    b.place(relx=0.5, rely=0.85, anchor=CENTER)
    win.bind("<Return>", lambda event: win.destroy())

def removeItem(event):
    try:
        index = tree.selection()[0]
        date = tree.item(index)['values'][3]
        client_socket.send(bytes("!rm {}&&".format(date), "utf8"))
    except IndexError as e:
        print("removeItem",e)

def removeItembyIndex(index):
    try:
        tree.delete(index)
        playSelectedSound("-1")
    except IndexError as e:
        print(e)

def removeItembyDate(date):
    allIndizes = tree.get_children()
    allChildren = []
    for indize in allIndizes:
        if(tree.item(indize)['values'][3] == date):
            removeItembyIndex(indize)

def recaller(name,prio,text,date,ind):
    while(ind in tree.get_children()):
        time.sleep(int(prio)*RECALLER)
        if ind in tree.get_children():
            popup("Recaller", f"Wer: {name}\nPriorität: {prio}\nAufgabe: {text}\nDate: {date[:5]}")

def select_entry(event):
    extend_item(event)

def extend_item(event):
    global index
    try:
        index = tree.selection()[0]
        content = tree.item(index)['values'][2]
        popup("Aufgabe", content)
    except IndexError as e:
        children = tree.get_children()
        if children:
            child_id = children[0]
            tree.focus(child_id)
            tree.selection_set(child_id)

#https://stackoverflow.com/questions/1966929/tk-treeview-column-sort
def treeview_sort_column(tv, col, reverse):
    l = [(tv.set(k, col), k) for k in tv.get_children('')]
    l.sort(key=lambda t: int(t[0]), reverse=reverse)
    for index, (val, k) in enumerate(l):
        tv.move(k, '', index)
    tv.heading(col,
               command=lambda: treeview_sort_column(tv, col, not reverse))

def play_audio(file):
    #a = audioFile.AudioFile(file)
    #a.playclose()
    if(RECALLER):
        try:
            playsound.playsound(file)
        except playsound.PlaysoundException:
            playsound.playsound("src/audio/receive.wav")

def playSelectedSound(number):
    global sound_thread
    if(not sound_thread or not sound_thread.is_alive()):
        sound_thread = Thread(target=play_audio, args=(["src/audio/{}".format(sounds[number])]), kwargs={})
        sound_thread.start()

def receive():
    """Handles receiving of messages."""
    while True:
        try:
            msgs = client_socket.recv(BUFSIZ).decode("utf8")
            msgs = list(filter(None,msgs.split("&&")))
            for msg in msgs:
                handleReceive(msg)
        except IndexError as e:  # Possibly client has left the chat.
            print("You have left the chat.")
            quitExecutor()
        except tkinter.TclError as e:
            print("receive",e)

def handleReceive(msg):
    data = msg.split("||")
    if(data[1].startswith("!rm")):
        removeItembyDate(data[1].split(" ")[1])
    elif("quit!" in data[1]):
        quitExecutor()
    else:
        ind = tree.insert('', 'end', values=data)
        if(int(data[1])<9):
            playSelectedSound(data[1])
            if(int(data[1])==1 and RECALLER):
                top.lift()
                popup("Wichtige Aufgabe!", data[2])
        if(RECALLER):
            recaller_thread = Thread(target=recaller, args=data+[ind], daemon=True)
            recaller_thread.start()
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
#tree.bind('<<TreeviewSelect>>', select_entry)
tree.bind('r',removeItem)
tree.bind('e',extend_item)
for column in ["Wer", "Prio", "Aufgabe","Zeit"]:
    tree.heading(column, text=column)
tree.pack(expand="yes", fill=tkinter.BOTH)
messages_frame.pack(fill='both', expand="yes")

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send)
entry_field.pack(fill="both")
ni_button = tkinter.Button(text="Unwichtig", command=lambda: send(prefix=8))
ni_button.pack(side="left", fill="both", expand=True)
med_button = tkinter.Button(text="Medium", command=lambda: send(prefix=4))
med_button.pack(side="left", fill="both", expand=True)
i_button = tkinter.Button(text="Wichtig", command=lambda: send(prefix=2))
i_button.pack(side="left", fill="both", expand=True)
vi_button = tkinter.Button(text="Extrem wichtig", command=lambda: send(prefix=1))
vi_button.pack(side="left", fill="both", expand=True)

top.protocol("WM_DELETE_WINDOW", on_closing)

#----Now comes the sockets part----
with open("client.conf", "r") as client:
    HOST,PORT = client.readline().strip("\n").split(",")
    NAME = client.readline().strip("\n")
    RECALLER = int(client.readline().strip("\n"))
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
client_socket.setsockopt(SOL_SOCKET, SO_KEEPALIVE, 1)
client_socket.connect(ADDR)
client_socket.send(bytes(NAME, "utf8"))
receive_thread = Thread(target=receive, daemon=True)
receive_thread.start()
tkinter.mainloop()  # Starts GUI execution.