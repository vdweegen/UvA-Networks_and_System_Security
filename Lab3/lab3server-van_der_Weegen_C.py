####################################################
# Assignment 3 (three) - Chat system                #
# Netwerken en Systeembeveiliging                  #
# File: lab3server-van_der_Weegen_C.py             #
#                                                  #
# Cas van der Weegen                               #
# Computer Sciences                                #
# Stud. nr. 6055338                                #
####################################################
import socket
import select
import sys

HOST = "localhost"
PORT = 12345

# DEFINE VARIABLES
count = 0
members = {}

# Send data to all the clients
def say_data(data):
    all_members = members.keys()
    for member in all_members:
        member.sendall(data)

# Server message (basicly the same)
def server_message(data):
    all_members = members.keys()
    for member in all_members:
        member.sendall("<" + data + ">")
    
# Whisper message
def send_whisper(data, sender, receiver):
    inf = "[" + members[sender] + " to " + receiver + "]: "
    data = inf + data
    sender.sendall(data)
    
    all_members = members.keys()
    for member in all_members:
        if members[member] == receiver:
            member.sendall(data)

# Checks if a name is in use
def check_use(name):
    if name in members.values():
        return True
    return False

# Handles a nickname request from sender
def handle_request(text, sender):
    if len(text) > 2 or len(text) < 2:
        sender.sendall("""<Usage of /nick: /nick <enter_name>>""")

    elif(check_use(text[1])) :
        sender.sendall("""<This nickname is already taken>""")

    else:
        temp = members[sender]
        members[sender] = text[1]
        server_message(temp + " is now known as " + members[sender])

# Handle a whisper request from sender
def handle_whisper(text, sender):
    if len(text) < 3:
        sender.sendall("""<Usage of /whisper: /whisper <user> <text>>""")
        
    elif(not check_use(text[1])):
        sender.sendall("""<This user doesn't exist>""")
        
    elif(members[sender] == text[1]):
        sender.sendall("""<You can't whisper to yourself>""")
        
    else:
        send_whisper(" ".join(text[2:]), sender, text[1])

def handle_list(text, sender):
    if len(text) > 1:
        sender.sendall("""<Usage of /list: /list>""")
    else:
        data = "Online users:\n"
        all_members = members.keys()
        for member in all_members:
            data += members[member] + "\n"
        sender.sendall(data)

def main():
    chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chat_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    chat_server.bind((HOST, PORT))
    input = [chat_server]
    print "Started listening on %s" % HOST
    chat_server.listen(5)
    while True:
        input_ready, _, _ = select.select(input,[],[])

        for tag in input_ready:
            if tag == chat_server:
                client, _ = chat_server.accept()

                input.append(client)
                global members
                global count
                members[client] = "Guest" + str(count)
                count += 1
                server_message(members[client] + " entered the room")
                print "%s connected" % members[client]

            else:
                talk = tag.recv(1024)
                
                if talk:
                    commands = talk.split(" ")

                    if commands[0] == "/say":
                        say_data( members[tag] + ": " +
                                " ".join(commands[1:]))
                        
                    elif commands[0] == "/nick":
                        handle_request(commands, tag)

                    elif commands[0] == "/whisper":
                        handle_whisper(commands, tag)
                    
                    elif commands[0] == "/list":
                        handle_list(commands, tag)
                        
                    elif commands[0] == "/help":
                        tag.sendall("<The commands available are:>\n")
                        tag.sendall("\t/nick - change your nickname\n")
                        tag.sendall("\t/whisper - send a private message\n")
                        tag.sendall("\t/say - send a message\n")
                        tag.sendall("\t/list - list all users\n")

                    # Unknown command
                    else:
                        tag.sendall("<Unknown Command, type /help for a list of commands>")

                # Remove the users tag
                else:
                    server_message(members[tag] +" logged off")
                    print "%s disconnected" % members[tag]
                    input.remove(tag)
                    del members[tag]
                    tag.close()
                    


if __name__ == "__main__":
    main()