import bson
import json

def load(filename, fmt='bson'):
	if fmt=='bson':
		fh = open(filename, 'rb') 
		data = fh.read()
		fh.close()
		return bson.loads(data)

	if fmt=='json':
		fh = open(filename, 'r') 
		data = fh.read()
		fh.close()
		return json.loads(data)
