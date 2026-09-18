from ynified.tools.ipv4 import parse_ipv4

VERSION = "ynified 0.1"

def cmd(items):
	print("CMD")

def string_normalize(items):
	if isinstance(items, str):
		return items
	done = ""
	for i in items:
		done += i.value
	return done

def get(url, ct='txt'):
	#...WGET
	print("GET", url, ct)
	return f"{url}({ct})"


# Experimental
def If(node):
	items = list(node.value)
	if len(items) == 5:
		op    = items[0].value
		left  = items[1].value
		right = items[2].value
		true  = items[3].value
		false = items[4].value
		if (op=='='):
			done = true if left == right else false
		if (op=='>'):
			done = true if left > right else false
		if (op=='<'):
			done = true if left < right else false
		if (op=='>='):
			done = true if left >= right else false
		if (op=='<='):
			done = true if left <= right else false
		if (op=='!='):
			done = true if left != right else false
	else:
		raise Exception("Expected 5 arguments")
	return done


# Custom tags
custom_tags = {
		
		#
		"$"                 : lambda cls, node: cmd(node.value),
		"pragma:signature"  : lambda cls, node: VERSION,
		"pragma:archetype"  : lambda cls, node: 'YMG1', # FIXME
		"pragma:target"     : lambda cls, node: 'json', # FIXME
		"pragma:compressed" : lambda cls, node: true, # FIXME

		"ext:uuid4"     : lambda cls, node: str(__import__("uuid").uuid4()),
		"ext:timestamp" : lambda cls, node: __import__("datetime").datetime.now().strftime(node.value),
		"ext:joinstr"   : lambda cls, node: string_normalize(node.value),
		#ext:sha256

		"cast:int"      : lambda cls, node: int(node.value),
		"cast:float"      : lambda cls, node: float(node.value),
		"cast:str"      : lambda cls, node: str(node.value),
		
		"get:base64"    : lambda cls, node: get(string_normalize(node.value), ct='b64'),
		"get:text"      : lambda cls, node: get(string_normalize(node.value), ct='txt'),
		"get:binary"    : lambda cls, node: get(string_normalize(node.value), ct='bin'),

		"fmt:ipv4"           : lambda cls, node: parse_ipv4(node.value),
		#fmt:ipv6
		#fmt:mac

		#password|secret
		#encrypt
		
		#math-const (pi)
		"math"           : lambda cls, node: 3.1415 if node.value=="pi" else 0,

		# Experimental
		"if"             : lambda cls, node: If(node),
		"string-reverse" : lambda cls, node: node.value[::-1],
}
