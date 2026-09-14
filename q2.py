from ynified.query import Q
relax = lambda q,o: Q(o,q)








'''
	List

		:All,*
		:Trim
		:First
		:Last
		:Odd
		:Even
		:Random
		:1  		Index (0)
		:0..3 		Range BeginIndex..EndIndex (0..3)
'''

#print(relax('foo.0.bar.baz:*.age>sum',
print(relax('foo.0.bar.baz',
	{
		'foo': [{
			'bar': {
				'baz': [
						{'name': 'John', 'age': 50},
						{'name': 'Jane', 'age': 25},
						{'name': 'Jane', 'age': 25},
				]
			}
		}]
	}
))


#  Locator        Selector	   Reducer
#--------------|-----------|-------------
'foo.0.bar.baz : *.age     > sum '
'foo.0.bar.baz : {1,2}.age > avg '


