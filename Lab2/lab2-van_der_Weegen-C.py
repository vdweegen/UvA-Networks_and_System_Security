import socket
import time
import os.path
import subprocess
import sys
from os import path
from cStringIO import StringIO

host = ''
port = 8080

current_date = time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime())

print 'Setting up socket....'
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print 'Socket up'

print 'Binding address & port...'
try:
    c.bind((host, port))
except socket.error, msg:
    print 'Bind Failed'
    quit()
    
print 'Bind complete'

print 'Start listening...'
try:
    c.listen(1)
except:
    print 'Cannot Launch'
    quit
    
print 'Socket listening'

if host == '':
    host = '127.0.0.1'

print 'Server online ' + 'at: ' + host + ':' + str(port) 

while 1:
    csock, addr = c.accept()
    try:
        request = csock.recv(1024)
    except:
        csock.close()

    print 'Connected with ' + addr[0] + ':' + str(addr[1])
    operation = request.split(' ')
    try: 
        file = ('.' + operation[1])
    except:
        continue
    
    if operation[1].startswith('/cgi-bin'):
        if operation[1] == '/cgi-bin/':
            file = '//cgi-bin/env.py'
            operation[1] = '/cgi-bin/env.py'
        if operation[0] == 'GET' and os.path.exists(path.relpath(file[2:])):
            csock.send('HTTP/1.1 200 OK\r\n')
            f = open(path.relpath(file[2:]), 'r')
            old_stdout = sys.stdout
            lines = f.readlines()
            for line in lines:
                sys.stdout = stdout = StringIO()
                exec line
                csock.send(stdout.getvalue())
                sys.stdout = old_stdout
            f.close()
                                    
        elif operation[0] != 'GET':
            csock.send('HTTP/1.1 501 Not Implemented\r\n Date:'+current_date+'\n\r Content-Type: text/html\r\n Connection:close\r\n\r\n')
            csock.send('501 Not Implemented')
        else:
            csock.send('HTTP/1.1 404 Not Found\r\nDate:'+current_date+'\r\nContent-Type:text/html\r\nConnection:close\r\n\r\n')
            csock.send('404 Not Found!')
        csock.close()	          
    else:
        if operation[1] == '/':
            file = './index.html'
      
        if operation[0] == 'GET' and os.path.exists(file):
            csock.send('HTTP/1.1 200 OK\r\n Date:'+current_date+'\n\r Content-Type: text/html\r\n Connection:close\r\n\r\n')        
            handle = open(file[2:], 'r')
            response = handle.read()
            handle.close()
            csock.send(response)
        elif operation[0] != 'GET':
            csock.send('HTTP/1.1 501 Not Implemented\r\n Date:'+current_date+'\n\r Content-Type: text/html\r\n Connection:close\r\n\r\n')
            csock.send('501 Not Implemented')
        else:
            csock.send('HTTP/1.1 404 Not Found\r\nDate:'+current_date+'\r\nContent-Type:text/html\r\nConnection:close\r\n\r\n')
            csock.send('404 Not Found!')
        csock.close()	