"""
	ynified query
"""
import shlex
import re


class QueryCompilerError(Exception):
	pass


class DataError(QueryCompilerError):
	pass


class ParseError(QueryCompilerError):
	pass


class QueryCompiler:
	QUOTE = '"'
	DOT = '.'

	def __init__(self, query):
		self.query = query
		self.parsed = self.parse()

	def special_match(self, data, search=re.compile(r'[^.,~a-zA-Z0-9]').search):
		return not bool(search(data))

	def is_quoted(self, data):
		return data[0] == self.QUOTE

	def remove_quotes(self, data):
		return data[1:-1]

	def parse(self):
		if not isinstance(self.query, str):
			raise ParseError("Expected string object!")
		# is not empty
		elements = list(shlex.shlex(self.query))	
		if not len(elements):
			raise ParseError("No element's found!")
		# check for illegal characters and remove dots
		_elements = []
		for element in elements:
			if not self.is_quoted(element):
				if self.special_match(element):
					if not element == self.DOT:
						_elements.append(element)
				else:
					raise ParseError("Illegal character \"%s\"" % element)
			else:
				if not element == self.DOT:
					_elements.append(element)
		# create integers for index
		done = []
		for element in _elements:
			try:
				element = int(element)
			except:
				pass
			done.append(element)
		# generate python syntax string
		py_str = ''
		for element in done:
			if isinstance(element, int):
				py_str += "[%s]" % element 
			else:
				if self.is_quoted(element):
					py_str += "['%s']" % self.remove_quotes(element)
				else:
					py_str += "['%s']" % element
		return py_str

	def throw(self, data):
		eval_str = "data%s" % self.parsed
		try:
			done = eval(eval_str)
		except:
			raise DataError("Data evaluation error!")
		return done


def Q(data, query):
	qc = QueryCompiler(query)
	return qc.throw(data)


if __name__ == '__main__':
	### Test ###
	test = lambda q: print("Test... '%s' =>" % q, Q(sample_data, q), type(Q(sample_data, q)))

	sample_data = [[1, 2, dict(FOO=10, bar=[100, 200, 
			dict(baz=99 ,spam={"Hello World#$" : "Hey!"})])], dict(x='X')]

	#test('')
	#test('foo."Bar Baz"$')
	#test('+1')
	test('0.0')
	test('1.x')
	test('0.2.FOO')
	test('0.2.bar.2.baz')
	test('0.2.bar.2.spam."Hello World#$" #Note')
	test('0,1')
	test('0.{x}.FOO')
	###test('foo.bar.baz.5~7')
	###test('foo.bar.baz.~4')
