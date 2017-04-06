from math import sqrt
import perlin

h = 25
w = 50
maxd = sqrt(((w/2))**2 + ((h/2))**2)
def __init__(self):
		
	return

OCEAN = 0
BEACH = 1
VOLCANO = 2
SNOW_MOUNTAIN = 3
BARE_MOUNTAIN = 4
SCHORCHED_MOUNTAIN = 5
TEMPERATE_DESERT = 6
SHRUBLAND = 7
TAIGA = 8
ICE = 9
TROPICAL_GRASSLAND = 10
TEMPERATE_GRASSLAND = 11
TUNDRA = 12
TEMPERATE_FOREST = 13
TEMPERATE_RAIN_FOREST = 14
TROPICAL_RAIN_FOREST =15

def update ():
	
	return
noise = perlin.SimplexNoise(256,None,None)
def generate_world ():
	
	elevation_map = [[x for x in range(w)] for y in range(h)]
	moisture_map = [[x for x in range(w) ] for y in range(h)]
	tempeture_map = [[x for x in range(w) ] for y in range(h)]
	for y in range(h):
		for x in range(w):
			

			m = 0.5 * noise.noise2(2 * x, 2 * y)
			m += 0.25 * noise.noise2(4* x, 4 * y)
			m += 0.125 * noise.noise2(8 * x,8 * y)
			m =(m + 1) / 2
			moisture_map[y][x] = m

			
			e = 1 * noise.noise2(1 * x, 1 * y)
			e += 0.5 * noise.noise2(2* x, 2 * y)
			e += 0.25 * noise.noise2(4 * x,4 * y)
			e =(e + 1) / 2

			d =  sqrt(((w/2)- x)**2 + ((h/2) - y)**2) / maxd
			elevation_map[y][x] = e -  1.7*pow(d,4)

			d = pow(abs((h/2)-y),2)
			t = ((- d * e * 10  ) / 100 + 5) * 10
			tempeture_map[y][x]  = t
		#print ("Temp: " + str(tempeture_map[y][0]) +" Y: " + str(y))
	for i in elevation_map:
		#print()
		for o in i:
			"""
			if o > 0.8:
				print ('^',end='')
				continue
			if o > 0.5:
				print ('+',end='')
				continue
			
			
			if o < 0.10:
				print ('~', end ='')
				continue
			print ('"',end='')
			"""
def initialize():
	generate_world ()
	return