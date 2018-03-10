#File: topic.py
#Author: Nicholas Kao
#Last Modified: 3/4/18

#necessary imports
import socket
import sys
import select
import json


#create my socket using TCP and IP4 and set it to nonblocking to allow multiple connections
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
mySocket.setblocking(0)

#parse command line to check if correct format, read in command line args, and assign args to correct variables
if len(sys.argv) != 2:
	print('Incorrect number of command line args')
	quit()
port = int(sys.argv[1])
if port < 1024:
	print("Ivalid port number")
else:
	#print("Waiting for connections at port %s" % port)

	# format address and bind the socket to the address, allowing 100 concurrent connections
	address = ('localhost', port)
	mySocket.bind(address)
	#print("Server bound to address: " + address[0] + ":" + str(address[1]))
	mySocket.listen(100)

	#initialize list of inputs, outputs, topics, messages
	inputs = [mySocket]
	outputs = []
	topics = {}
	messages = []

	#while there are connections (a socket is in the input buffer), read and parse the input
	while inputs:
		[rs, ws, es] = select.select(inputs, outputs, inputs)
		for readable in rs:
			#if its my socket, add the new connection to the list of inputs and outputs
			if readable is mySocket:
				connection, clientAddress = readable.accept()
				connection.setblocking(0)
				inputs.append(connection)
				outputs.append(connection)
			# if the connection isnt my socket, decode the topic/message appropriately
			else:
				data = readable.recv(256).decode('utf-8')
				if len(data) > 0:
					data = json.loads(data)
					# if already registered, add the message to the list of messages to be transmitted
					if "destination" in data:
						topic = data['message']['topic']
						message = data['message']['text']
						messages.append(((str(topic) + ":" + str(message)), readable))
						if data:
							continue
						else:
							break
					# if not registered, check if the topic exists and either add it or add the connection to the current topic
					else:
						topic = data['topics']
						if topic in topics:
							topics[topic].append(readable)
						else: 
							topics[topic] = [readable]
				# on a disconnect, remove the connection from the inputs and outputs
				else:
					outputs.remove(readable)
					inputs.remove(readable)
		# while there are messages to be sent
		while messages:
			# break the messages into topic and message
			data = messages[0]
			text = data[0]
			sender = data[1]
			messages = messages[1:]
			text = text.split(":")
			topic = text[0]
			message = text[1]
			toSend = topics[topic]
			# for each client to send the message to, format it in json and send it
			for dest in toSend:
				if dest == sender:
					continue
				toSend = {"source":{"ip":'hostname', "port":port},"destination":{"ip":dest.getpeername()[0],"port":dest.getpeername()[1]},"message":{"topic":topic, "text":message}}
				dest.sendall(json.dumps(toSend).encode())





