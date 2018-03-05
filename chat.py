#File: chat.py
#Author: Nicholas Kao
#Last Modified: 3/4/18

#necessary imports
import socket
import sys
import select
import json

#parse command line to check if correct format, read in command line args
args = sys.argv[1:]
if len(args) >= 2 and len(args) < 4:
	mode = args[0]
else:
	print('Incorrect number of arguments passed')
	exit()


#create my socket using TCP and IP4
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if mode == '-direct': #operating in direct mode
	#assign args to correct variables
	port = args[1]
	address = ('localhost', int(port))
	if len(args) == 3:
		address = args[2]
		address = address.split(':')
		address = (address[0],int(address[1]))
	if port == "0": #operating in client mode
		print("Client using address: " + address[0] + ":" + str(address[1]))
		mySocket.connect(address)
		try:
			#until disconnecting, take keyboard input, format it correctly, and send it to the other client
			while True:
				toSend = {"source":{"ip":"127.0.0.1", "port":mySocket.getsockname()[1]},"destination":{"ip":"127.0.0.1","port":address[1]},"message":{"topic":'direct'}}
				[rs, ws, es] = select.select([sys.stdin, mySocket], [], [], 1)
				if sys.stdin in rs:
					message = input()
					if message == 'quit()': #if 'quit()' is entered, the connection will be sevxered
						mySocket.close()
						break
					toSend['message']['text'] = message
					print(toSend)
					toSend = json.dumps(toSend).encode()
					mySocket.sendall(toSend)
				if mySocket in rs: #if the socket has incoming messages
					#receive, decode, and print the message
					data = mySocket.recv(200).decode('utf-8')
					if len(data) > 0:
						data = json.loads(data)
						topic = data['message']['topic']
						message = data['message']['text']
						print("%s: %s" % (topic, message))
					if data:
						continue
					else:
						break
		#close the socket
		finally:
			mySocket.close()

	elif int(port) > 1023: #operating in server mode
		#bind to the supplied address and wait for a single connection
		mySocket.bind(address)
		print("Server bound to address: " + address[0] + ":" + str(address[1]))
		mySocket.listen(1)

		#wait until a connection is accepted
		while True:
			print("Server is waiting for a client to connect")
			connection, clientAddress = mySocket.accept()

			try:
				print("Connection to client at address: " + clientAddress[0] + ":" + str(clientAddress[1]) + "\n")
				#same control flow and behavior as lines 36-58 above
				while True:
					toSend = {"source":{"ip":'127.0.0.1', "port":address[1]},"destination":{"ip":clientAddress[0],"port":clientAddress[1]},"message":{"topic":'direct'}}
					[rs, ws, es] = select.select([sys.stdin, connection], [], [], 1)
					if sys.stdin in rs:
						message = input()
						if message == 'quit()':
							connection.close()
							mySocket.close()
							quit()
						toSend['message']['text'] = message
						print(toSend)
						toSend = json.dumps(toSend).encode()
						connection.sendall(toSend)
					elif connection in rs:
						data = connection.recv(200).decode('utf-8')
						if len(data) > 0:
							data = json.loads(data)
							topic = data['message']['topic']
							message = data['message']['text']
							print("%s: %s" % (topic, message))
						if data:
							continue
						else:
							connection.close()
							break
			# if the client disconnects, due to quiting or ketboard interrupt, print information and close the connection
			finally:
				print("Closing connection to client at address: " + clientAddress[0] + ":" + str(clientAddress[1]))
				connection.close()

	else: #trying to use a port number that is already assigned
		print("Invalid port number")
#topic mode
elif mode == '-topic':

	#parse command line args and connect to supplied address
	address = args[1]
	address = address.split(':')
	address = (address[0],int(address[1]))
	topic = args[2]
	mySocket.connect(address)

	try:
		#send registration message based on command line args
		regMess = {"source":{'ip':address[0], 'port':address[1]}, 'topics':topic}
		mySocket.sendall(json.dumps(regMess).encode())

		#while connected, send and receive messages (similar to code above, as well)
		while True:
			toSend = {"source":{"ip":'127.0.0.1', "port":mySocket.getsockname()[1]},"destination":{"ip":address[0],"port":address[1]},"message":{"topic":topic}}
			[rs, ws, es] = select.select([sys.stdin, mySocket], [], [], 1)
			if sys.stdin in rs:
				message = input()
				if message == 'quit()':
					mySocket.close()
					break
				toSend['message']['text'] = message
				print(toSend)
				mySocket.sendall(json.dumps(toSend).encode())
			if mySocket in rs:
				data = mySocket.recv(200).decode('utf-8')
				if len(data) > 0:
					data = json.loads(data)
					topic = data['message']['topic']
					message = data['message']['text']
					print("%s: %s" % (topic, message))
				#print(data)
				if data:
					continue
				else:
					break

	finally:
		mySocket.close()


