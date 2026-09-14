"""
	ynimerge
"""
import json, yaml

def info(img):
	print(img)

class Merge():
	"""
	demo.cpio
		META-INF	
		simple.bson
		complex.bson

	META-INF:
		manifest:
		  name:
		  description:
		  ...

		build:
		  volumes: [simple,complex]
		  sha: ...
		  generated: NOW
		  yni-version: SIGNATURE
	    ynimg-version: SIGNATURE

	simple: ...
	complex: ...
	"""
	def __init__(self, config):
		self.config = config
		self.image = {}

def build_from(build_fn):
	img = YMG2(build_fn)
	#img.build()
	info(img.image)

if __name__ == '__main__':
	import sys
	if len(sys.argv) == 2:
		build_from(sys.argv[1])
	else:
		print("usage: ymg2 <output><objects>...")
