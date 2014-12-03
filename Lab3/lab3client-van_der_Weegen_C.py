####################################################
# Assignment 3 (three) - Chat system                #
# Netwerken en Systeembeveiliging                  #
# File: lab3client-van_der_Weegen_C.py             #
#                                                  #
# Cas van der Weegen                               #
# Computer Sciences                                #
# Stud. nr. 6055338                                #
####################################################
import socket
import gui
import time
import select
import sys

HOST = "localhost"
PORT = 12345

def main():
    chat_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chat_client.connect((HOST, PORT))
    chat_client.setblocking(0)
    w = gui.MainWindow()
    # Handle received and sent data
    while w.update():
        try:
            while True:
                data = chat_client.recv(1024)
                if not data:
                    break
                w.writeln(data),

        except socket.error:
            pass

        try:
            line = w.getline()

            if data:
                chat_client.sendall(line)
        except socket.error:
            pass

            

if __name__ == "__main__":
    main()