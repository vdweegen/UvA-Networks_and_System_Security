## Netwerken en Systeembeveiliging Lab 5 - Distributed Sensor Network
## NAME: Cas van der Weegen / Alper Yerlibucak
## STUDENT ID: 6055338 / 10219358
import sys
import struct
from socket import *
from random import randint
from gui import MainWindow
from sensor import *
import select
import time
import math

# Get random position in NxN grid.
def random_position(n):
	x = randint(0, n)
	y = randint(0, n)
	return (x, y)

# Handles the PINGs	
def send_ping(sock, sensor_pos):
	global window
	window.writeln("Sending PING")
	ping_message = message_encode(MSG_PING, sequence_number, sensor_pos, (-1,-1), 0, 0)
	sock.sendto(ping_message, (mcast_addr[0], mcast_addr[1]))

# Handles the PONGs
def send_pong(socket, initiator, sensor_pos, address):
	global window
	window.writeln("Sending PONG to %s at %s" % (str(sensor_pos), str(address)))
	encoded_message = message_encode(MSG_PONG, sequence_number, initiator, sensor_pos, 0, 0)
	socket.sendto(encoded_message, address)

# Send echo
def send_echo(sock, message, echo_father):
	global window
	window.writeln("Sending echo message")
	message = message_encode(MSG_ECHO, message[1], message[2], (0, 0), OP_NOOP, 0)
	for (neighbor, address) in neighbor_list:
		if address != echo_father:
			sock.sendto(message, address)
			
# Sends an echo reply
def send_echo_reply(sock, message, address):
	global window
	window.writeln("Replying to echo message")
	encoded_message = message_encode(MSG_ECHO_REPLY,message[1], message[2],(-1,-1), OP_NOOP, 0)
	sock.sendto(encoded_message, address)

# Send echo with Payload
def send_echo_size(sock, message, echo_father):
	global window
	global size
	window.writeln("Sending echo message (with size)")
	encoded_message = message_encode(MSG_ECHO,message[1], message[2], (0, 0), OP_SIZE, size)
	for (neighbor, address) in neighbor_list:
		if address != echo_father:
			sock.sendto(encoded_message, address) 

# Send if operation is OP_SIZE
def send_echo_reply_size(sock, message, address, size):
	global window
	window.writeln("Replying to echo message (with size)")
	encoded_message = message_encode(MSG_ECHO_REPLY,message[1], message[2],(-1,-1),OP_SIZE, (size+1))
	sock.sendto(encoded_message, address)
	
# Handles Receiving Echo's
def recv_echo(sock, message, address):
	global echo_message
	global message_list
	global echo_father
	global window
	global size
	operation = message[4]
	window.writeln("Received echo message")
	
	if len(neighbor_list) == 1:
		echo_father = address
		if(operation == OP_SIZE):
			send_echo_reply_size(sock, message, echo_father, (size+1))
		else:
			send_echo_reply(sock, message, echo_father)
	elif echo_message != (message[1], message[2]):
		message_list = []
		echo_message = (message[1], message[2])
		echo_father = address
		send_echo(sock, message, address)
	else:
		send_echo_reply(sock, message, address)

# Handles depending on the type of message received
def handle_message(sock, mcast, message, address, range):
	global x
	global y
	global size
	global message_list
	global neighbor_replies
	global window
	decoded_message = message_decode(message)

	# Send pong if neighbor
	if decoded_message[0] == MSG_PING:
		init_x, init_y = decoded_message[2]
		if((x,y) == (init_x, init_y)):
			pass
		# Pythogorem A^2+B^2=C^2
		elif( math.sqrt(abs(x - init_x)**2 + abs(y - init_y)**2) <= range):
			send_pong(sock, (x,y), decoded_message[2], address)
		# Add non initiator to neighbors
	if decoded_message[0] == MSG_PONG:
		(non_initiator, address) = (decoded_message[2], address)
		global neighbor_list
		neighbor_list.append((non_initiator, address))
	if decoded_message[0] == MSG_ECHO:
		recv_echo(sock, decoded_message,address)
	if decoded_message[0] == MSG_ECHO_REPLY:
		window.writeln("Recieved echo reply")
		neighbor_replies.append(address)
		
		if(x == decoded_message[2][0] and y == decoded_message[2][1]):
			window.writeln("I am initiator")
			if(len(neighbor_replies) == len(neighbor_list)):
				window.writeln("wave ended")
				window.write("Neighbor replies:")
				window.writeln(neighbor_replies)
				window.write("Neighbors:")
				window.writeln(neighbor_list)
				size += 1
				if size > 1 :
						window.write("size: ")
						window.write(size)
						window.writeln(" ")
				neighbor_replies = []
			size = 0
		else:   
			window.writeln("I am not initiator")
			if decoded_message[4] == OP_SIZE:
				window.writeln("Received OPSIZE message")
				size += decoded_message[5]
			if(len(neighbor_replies) >= (len(neighbor_list)-1)):
				global echo_father
				if decoded_message[4] == OP_SIZE:
					send_echo_reply_size(sock, decoded_message, echo_father, size + 1)
				else:
					send_echo_reply(sock, decoded_message, echo_father)
					neighbor_replies = []
				size = 0

def main(mcast_addr, sensor_pos, sensor_range, sensor_val, grid_size, ping_period):
	"""
	mcast_addr: udp multicast (ip, port) tuple.
	sensor_pos: (x,y) sensor position tuple.
	sensor_range: range of the sensor ping (radius).
	sensor_val: sensor value.
	grid_size: length of the  of the grid (which is always square).
	ping_period: time in seconds between multicast pings.
	"""
	global sequence_number
	sequence_number = 0
	global echo_message
	echo_message = (-1,-1)
	global echo_father
	echo_father = (0,0)
	global size
	size = 0
	global neighbor_list
	neighbor_list = []
	global neighbor_replies
	neighbor_replies = []
	global message_list
	message_list = []
	global value
	value = sensor_val
	global x
	global y
	(x,y) = sensor_pos

	# -- Create the multicast listener socket. --
	mcast = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
	# Sets the socket address as reusable so you can run multiple instances
	# of the program on the same machine at the same time.
	mcast.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	# Subscribe the socket to multicast messages from the given address.
	mreq = struct.pack('4sl', inet_aton(mcast_addr[0]), INADDR_ANY)
	mcast.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
	mcast.bind(mcast_addr)

	# -- Create the sock-to-sock socket. --
	sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
	# Set the socket multicast TTL so it can send multicast messages.
	sock.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, 5)
	# Bind the socket to a random port.
	if sys.platform == 'win32': # windows special case
		sock.bind( ('localhost', INADDR_ANY) )
	else: # should work for everything else
		sock.bind( ('', INADDR_ANY) )

	# -- make the gui --
	global window
	window = MainWindow()
	window.writeln( 'my address is %s:%s' % sock.getsockname() )
	window.writeln( 'my position is (%s, %s)' % sensor_pos )
	window.writeln( 'my sensor value is %s' % sensor_val )

	# Send ping to all other users and start clock
	send_ping(sock, sensor_pos)
	start = time.time()

	# For select
	sockets = [mcast, sock]

	# -- This is the event loop. --
	while window.update():
	# Resend every x seconds (either default is set by commandline)
		if ((time.time() - start) > ping_period):
			neighbor_list = []
			send_ping(sock, (x,y))
			start = time.time()
		
		# Read the imputs (both socket & mcast)
		read, write, error = select.select(sockets,[],[],0)
		for s in read:
			message, address = s.recvfrom(1024)
			handle_message(sock, mcast, message, address, sensor_range)
		line = window.getline()
	# Send unicast Ping
		if line == 'ping':
			window.writeln("Sending ping over multicast %s:%s" % (mcast_addr[0], mcast_addr[1]))
			neighbor_list = []
			send_ping(sock, (x,y))
	# Print all neighbors
		elif line == 'list':
			if neighbor_list == []:
				window.writeln("No neighbors")
			for neighbor in neighbor_list:
				window.writeln("%s:%s" % (neighbor[0],neighbor[1]))
	# Print Position
		elif line == 'position':
			window.writeln("(%s,%s)" % (x , y))
	# Send echo
		elif line == 'echo':
			sequence_number += 1
			window.writeln("Sending echo...")
			encoded_message = message_encode(MSG_ECHO, sequence_number, (x,y), (-1, -1), OP_NOOP, 0) 
			for i in neighbor_list:
				sock.sendto(encoded_message, i[1])
	# Send echo with operation
		elif line == 'size':
			sequence_number += 1
			window.writeln("Starting wave...")
			encoded_message = message_encode(MSG_ECHO, sequence_number, (x,y), (-1, -1), OP_SIZE, 0) 
			for i in neighbor_list:
				sock.sendto(encoded_message, i[1])
	# Move the node			
		elif line == 'move':
			x = randint(0, grid_size)
			y = randint(0, grid_size)
			window.writeln("New position is: (%s, %s)" % (x,y))
			# Send ping to let users know new location
			send_ping(sock, (x,y))
	# Change the node value
		elif line == 'value':
			value = randint(0, 100)
			window.writeln("New value is: %s" % value)

# -- program entry point --
if __name__ == '__main__':
	import sys, argparse
	p = argparse.ArgumentParser()
	p.add_argument('--group', help='multicast group', default='224.1.1.1')
	p.add_argument('--port', help='multicast port', default=50000, type=int)
	p.add_argument('--pos', help='x,y sensor position', default=None)
	p.add_argument('--grid', help='size of grid', default=100, type=int)
	p.add_argument('--range', help='sensor range', default=50, type=int)
	p.add_argument('--value', help='sensor value', default=-1, type=int)
	p.add_argument('--period', help='period between autopings (0=off)',
		default=5, type=int)
	args = p.parse_args(sys.argv[1:])
	if args.pos:
		pos = tuple( int(n) for n in args.pos.split(',')[:2] )
	else:
		pos = random_position(args.grid)
	if args.value >= 0:
		value = args.value
	else:
		value = randint(0, 100)
	mcast_addr = (args.group, args.port)
	main(mcast_addr, pos, args.range, value, args.grid, args.period)
