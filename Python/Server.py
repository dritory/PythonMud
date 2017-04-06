"""    

Basic MUD server module for creating text-based Multi-User Dungeon (MUD) games.

Contains one class, Server, which can be instantiated to start a server running
then used to send and receive messages from players.


most of the code is authored by: Mark Frimston - mfrimston@gmail.com
https://github.com/Frimkron/mud-pi
"""
import select
import socket
import time
import sys


class Server (object):


	_listen_socket = None
	_clients = {}
	_nextid = 0
	_events = []
	_new_events = []


	 #Used to store different types of occurences
	_EVENT_NEW_PLAYER = 1
	_EVENT_PLAYER_LEFT = 2
	_EVENT_COMMAND = 3

    # Different states we can be in while reading data from client
    # See _process_sent_data function
	_READ_STATE_NORMAL = 1
	_READ_STATE_COMMAND = 2
	_READ_STATE_SUBNEG = 3

    # Command codes used by Telnet protocol
    # See _process_sent_data function
	_TN_INTERPRET_AS_COMMAND = 255
	_TN_ARE_YOU_THERE = 246
	_TN_WILL = 251
	_TN_WONT = 252
	_TN_DO = 253
	_TN_DONT = 254
	_TN_SUBNEGOTIATION_START = 250
	_TN_SUBNEGOTIATION_END = 240



	# Constructor creates the server object and starts listening to players
	def __init__(self):

		print("Starting server...")
		self._clients = {}
		self._nextid = 0
		self._events = []
		self._new_events = []
		# create a new tcp socket
		self._listen_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

		self._listen_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)

		#binds the socket to a ip address and port.  23 is standart TELNET port
		self._listen_socket.bind(("0.0.0.0",23))

		self._listen_socket.setblocking(False)

		#start listening for connections
		self._listen_socket.listen(1)


	#checks for new players, disconnected players and new messages
	def update(self):

		self._check_for_new_connections()

		self._check_for_changed_states()

		# sets the new events to the list of events and resets new event list
		self._events = list(self._new_events)
		self._new_events = []


	def get_new_players (self):
		"""    
        Returns a list containing info on any new players that have entered the game 
        since the last call to 'update'. Each item in the list is a player id number.
        """
		retval = []

		for ev in self._events:
			if ev[0] == self._EVENT_NEW_PLAYER: retval.append(ev[1])
		return retval

	def get_disconnected_players (self):
		"""    
        Returns a list containing info on any players that have left the game since 
        the last call to 'update'. Each item in the list is a player id number.
        """
		retval = []

		for ev in self._events:
			if ev[0] == self._EVENT_PLAYER_LEFT: retval.append(ev[1])

		return retval

	def get_commands(self):
		"""    
        Returns a list containing any commands sent from players since the last call
        to 'update'. Each item in the list is a 3-tuple containing the id number of
        the sending player, a string containing the command (i.e. the first word of 
        what they typed), and another string containing the text after the command
        """
		retval = []

		for ev in self._events:
			if ev[0] == self._EVENT_COMMAND: retval.append((ev[1],ev[2],ev[3]))

		return retval

	def send_message(self,to,message):
		"""    
		Sends the text in the 'message' parameter to the player with the id number 
		given in the 'to' parameter. The text will be printed out in the player's
		terminal.
		"""
        # we make sure to put a newline on the end so the client receives the
        # message on its own line
		self._attempt_send(to,message+"\n\r")
	



	def shutdown (self):
		for cl in self._clients.values():
			#closes the socket, siconnecting the client
			cl.socket.shutdown()
			cl.socket.close()
		self._listen_socket.close()

	def _check_for_new_connections(self):

		# 'select' is used to check whether there is data waiting to be read
        # from the socket.  We pass in 3 lists of sockets, the first being
        # those
        # to check for readability.  It returns 3 lists, the first being
        # the sockets that are readable.  The last parameter is how long to
        # wait -
        # we pass in 0 so that it returns immediately without waiting
		rlist,wlist,xlist = select.select([self._listen_socket],[],[],0)

		# if the socket wasn't in the readable list, there's no data available,
        # meaning no clients waiting to connect, and so we can exit the method
        # here
		if self._listen_socket not in rlist: return

		# 'accept' returns a new socket and address info which can be used to
        # communicate with the new client
		joined_socket,addr = self._listen_socket.accept()

		# set non-blocking mode on the new socket.  This means that 'send' and
        # 'recv' will return immediately without waiting
		joined_socket.setblocking(False)

		# construct a new _Client object to hold info about the newly connected
        # client.  Use 'nextid' as the new client's id number
		self._clients[self._nextid] = Server._Client(joined_socket,addr[0],"",time.time())


		# add a new player occurence to the new events list with the player's id
        # number
		self._new_events.append((self._EVENT_NEW_PLAYER,self._nextid))
		print("New client connecting with address " + addr[0])
		# add 1 to 'nextid' so that the next client to connect will get a unique
        # id number
		self._nextid += 1

	
	def _check_for_changed_states(self):
		
		for id,cl in list(self._clients.items()):
			#check for disconnected clients
			if(not time.time() - cl.lastcheck < 5.0):

				self._attempt_send(id,"\x00")

				cl.lastcheck = time.time()

			# we use 'select' to test whether there is data waiting to be read from
            # the client socket.  The function takes 3 lists of sockets, the
            # first being
            # those to test for readability.  It returns 3 list of sockets, the
            # first being
            # those that are actually readable.
			rlist,wlist,xlist = select.select([cl.socket],[],[],0)

			if(cl.socket not in rlist): continue

			try:

				data = cl.socket.recv(4096).decode("latin1")

				message = self._process_received_data(cl,data)

				if message:

					# remove any spaces, tabs etc from the start and end of the message
					message = message.strip()

					# separate the message into the command (the first word) and
                    # its parameters (the rest of the message)
					command,params, = (message.split(" ",1) + ["",""])[:2]

					# add a command occurence to the new events list with the
                    # player's id number, the command and its parameters
					self._new_events.append((self._EVENT_COMMAND,id,command.lower(),params))

			except socket.error:
				self._handle_disconnect(id)

	def _handle_disconnect(self, clid):
		print("Client with id " + str(clid) + " has disconnected")
		#remove the client from the list
		del(self._clients[clid])
		# appends a new event
		self._new_events.append((self._EVENT_PLAYER_LEFT,clid))



	def _process_received_data(self,client,data):

		# the Telnet protocol allows special command codes to be inserted into
        # messages.  For our very simple server we don't need to response to
        # any
        # of these codes, but we must at least detect and skip over them so
        # that
        # we don't interpret them as text data.
        # More info on the Telnet protocol can be found here:
        # http://pcmicro.com/netfoss/telnet.html

		message = None
		state = self._READ_STATE_NORMAL


		for c in data:

			#normal state
			if state == self._READ_STATE_NORMAL:
				#special command
				if( ord(c) == self._TN_INTERPRET_AS_COMMAND):
					state = self._READ_STATE_COMMAND
				#new line means end of message
				elif c == "\n":
					#sets the message and resets the buffer
					message = client.buffer
					client.buffer = ""

				#backspace deletes last character
				elif c == "\x08":
					client.buffer = client.buffer [:-1]
				#otherwise add to the buffer
				else:
					client.buffer += c

			#command state
			elif state == self._READ_STATE_COMMAND:
				# the special 'start of subnegotiation' command code indicates that
                # the following characters are a list of options until we're told
                # otherwise. We switch into 'subnegotiation' state to handle this
				if( ord (c) == self._TN_SUBNEGOTIATION_START):
					state == self._READ_STATE_SUBNEG

				elif ord(c) in (self._TN_WILL, self._TN_WONT,self._TN_DO,self._TN_DONT):
					state = self._READ_STATE_COMMAND
				# for all other command codes, there is no accompanying data so 
                # we can return to 'normal' state.
				else:
					state = self._READ_STATE_NORMAL

			elif state == self._READ_STATE_SUBNEG:

				if ord(c) == self._TN_SUBNEGOTIATION_END:
					state = self._READ_STATE_NORMAL

		#returns the message which is either a string or None
		return message



	def _attempt_send(self,clid,data):
		if sys.version < '3' and type(data) != unicode: data = unicode(data,"latin1")
		try:
			#sends the data
			self._clients[clid].socket.sendall(bytearray(data,"latin1"))

		except KeyError: pass

		#socket.error is raised if there is a connection problem or the client has
		#disconnected
		except socket.error:
			self._handle_disconnect(clid)

	# each connected client.  Stores information about the client
	class _Client(object):

		socket = None
		address = ""
		buffer = ""
		lastcheck = 0

		def __init__(self,socket,address,buffer,lastcheck):
			self.socket = socket
			self.address = address
			self.buffer = buffer
			self.lastcheck = lastcheck
