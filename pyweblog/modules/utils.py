import re

from google.appengine.api.datastore_errors import BadValueError

# copied from web.py
class Storage(dict):
    """
    A Storage object is like a dictionary except `obj.foo` can be used
    in addition to `obj['foo']`.
    
        >>> o = storage(a=1)
        >>> o.a
        1
        >>> o['a']
        1
        >>> o.a = 2
        >>> o['a']
        2
        >>> del o.a
        >>> o.a
        Traceback (most recent call last):
            ...
        AttributeError: 'a'
    
    """
    def __getattr__(self, key): 
        try:
            return self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __setattr__(self, key, value): 
        self[key] = value
    
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError, k:
            raise AttributeError, k
    
    def __repr__(self):     
        return '<Storage ' + dict.__repr__(self) + '>'


class RegExpValidator():
	def __init__(self, regexp):
		self.regexp = regexp
		self.pattern = re.compile(regexp)

	def __call__(self, value):
		if value == None:
			value = ''
		if not self.pattern.match(value):
			raise BadValueError('Value should be in this format: "%s".', self.regexp)
		return True
