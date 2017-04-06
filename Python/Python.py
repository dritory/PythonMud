import time
import glob, os
import importlib
from Server import Server

print("Hello world")

players = {}

remembered_players = {}

modules = {}

server = Server()

class Room:
	name = ""
	description = ""
	exits = {}
	position = ()
	def __init__(self, name, description, exits, position):
		self.name = name
		self.description = description
		self.exits = exits
		self.position = position

rooms = {}
def add_room (name, position,description):
	if ( position is not None) or len (position) >= 2: 
		x = position[0]
		y = position[1]
		exits = {}
		new_exits = []
		if(x > 0 and (x - 1, y ) in rooms.keys() and rooms[(x - 1,y)] is not None):
			exits["west"] = rooms[(x - 1,y)]
			new_exits.append([rooms[(x - 1,y)], "east"])

		if((x + 1, y) in rooms.keys() and rooms[(x + 1,y)] is not None):
			exits["east"] = rooms[(x + 1,y)]
			new_exits.append([rooms[(x + 1,y)], "west"])

		if(y > 1 and (x, y - 1) in rooms.keys() and rooms[(x,y - 1)] is not None):
			exits["south"] = rooms[(x,y - 1)]
			new_exits.append([rooms[(x,y - 1)], "north"])

		if((x, y + 1) in rooms.keys() and rooms[(x,y + 1)] is not None):
			exits["north"] = rooms[(x,y + 1)]
			new_exits.append([rooms[(x,y + 1)], "south"])

		rooms[tuple(position)] = Room(name, description, exits, position)

		for ne in new_exits:
			ne[0].exits[ne[1]] = rooms[tuple(position)]

add_room ("Nowhere", (0,0),"You are standing in thin air. How peculiar!")
add_room ("Nowhere", (1,0),"You are still standing in thin air. Weird!")


def _handle_new_modules():
	for dr in os.listdir("Modules/"): 
		if not os.path.isdir(os.path.join("Modules/" ,dr)): continue
		
		for file in os.listdir(os.path.join("Modules/", dr)):
			if str(file).startswith("__init__"): continue
			if not file.endswith(".py"): continue
			file = file[:-3]
			if file in modules.keys(): continue
			try:
				
				module = importlib.import_module("Modules." + dr + "." + file )
				modules[file] = module
				print("Loaded module "+file)
				try:
					module.initialize()
					#module lacks an update function
				except AttributeError: pass
				#print("Module has these functions:")
				#print (module)
				#print (dir(module)) 
			except ModuleNotFoundError:
				print("Module not found for file:" + "Modules" +  "." + dr +"."+ file)
			
_handle_new_modules()

def _handle_new_players():

	for id in server.get_new_players():

		players[id] = {
			"name": None,
			"position" : (0,0),
		}

		server.send_message(id,"Greetings new player! What is your name?")

def _handle_disconnected_players():

	
	for id in server.get_disconnected_players():

		if id not in players: continue
		remembered_players[players[id]["name"]] = players[id]
		for pid,pl in players.items():
			server.send_message(pid,"%s quit the game" % players[id]["name"])
		

		del(players[id])

def _handle_new_commands():

	for id, command, params in server.get_commands():

		if id not in players: continue
		
		
		if  players[id]["name"] is None:
			if not command in remembered_players:

				players[id]["name"] = command
				for pid, pl in players.items():
					server.send_message(pid,"%s entered the game" %  players[id]["name"])
	
				server.send_message(id,"Welcome to the game, %s. Type 'help' for a list of commands. Have fun!" %  players[id]["name"])
				remembered_players[command] = players[id]
			else:
				players[id] = remembered_players[command]
				server.send_message(id,"Welcome back, %s. Type 'help' for a list of commands. Have fun!" %  players[id]["name"])

			server.send_message(id,rooms[players[id]["position"]].description)

		elif command == "go":

			ex = params.lower()
			if ex != "":
				rm = rooms[tuple(players[id]["position"])]
				if ex in rm.exits.keys():
					
					if(rm.exits[ex] in rooms.values()):
						players[id]["position"] = tuple(rm.exits[ex].position)
						rm = rooms[tuple(players[id]["position"])]
						server.send_message(id,"You arrive at the '%s'" % rm.name)
						server.send_message(id,rm.description)
					else:
						print ("Room '%s' does not exist" % rm.exits[ex].name)
						server.send_message(id,"This place does not exist: '%s'" % rm.exits[ex].name)
				else:
					server.send_message(id,"Unknown exit '%s'" % ex)
			else:
				server.send_message(id,"Go where?")
				continue
		# 'help' command
		elif command == "help":

		# send the player back the list of possible commands
			server.send_message(id,"Commands:")
			server.send_message(id,"  say <message>  - Says something out loud, e.g. 'say Hello'")
			server.send_message(id,"  look           - Examines the surroundings, e.g. 'look'")
			server.send_message(id,"  go <exit>      - Moves through the exit specified, e.g. 'go outside'")
		elif command == "look":
			rm = rooms[tuple(players[id]["position"])]
			server.send_message(id,rm.description)
			if len(rm.exits) > 0:
				server.send_message(id,"There is " + str(len(rm.exits)) + " exits here:")
				for ex in rm.exits.keys():
					
					server.send_message(id,ex +": "+ rm.exits[ex].name)
			else:
				server.send_message(id,"It seems that there is no exits here. You are pretty much stuck.")
		else:
			server.send_message(id,"Unknown command '%s'" % command)
while True:
	time.sleep(0.2)
	server.update()
	_handle_new_players()
	_handle_disconnected_players()
	_handle_new_commands()

	for module in modules.values():
		try:
			module.update()
		#module lacks an update function
		except AttributeError: 
			pass
			