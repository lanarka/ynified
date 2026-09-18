import ipaddress 

class BadIPAddress(Exception):
	pass

def parse_ipv4(address):
		try:
			ip = ipaddress.ip_address(address)
		except ValueError:
			raise BadIPAddress()
		return {"$ipv4": list(ip.packed)}