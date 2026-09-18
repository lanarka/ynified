"""
	ynified query example
"""
from ynified.lib import load
from ynified.query import Q

obj = load("examples/simple.bson")

print(Q(obj, "hello"))
