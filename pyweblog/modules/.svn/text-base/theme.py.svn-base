import os
import logging

from config import *

logging.info('module theme reloaded')

class Theme:
	def __init__(self, name='default'):
		self.name = name
		self.mapping_cache = {}
		self.dir = '%s/themes/%s' % (settings.app_root, name)
		self.server_dir = os.path.join(os.getcwd(), 'themes', self.name)

	def __getattr__(self, name):
		if self.mapping_cache.has_key(name):
			return self.mapping_cache[name]
		else:
			path = os.path.join(self.server_dir, 'templates', name + '.html')
			if not os.path.exists(path):
				path = os.path.join(os.getcwd(), 'themes', 'default', 'templates', name + '.html')
			self.mapping_cache[name] = path
			return path

settings.theme = Theme(config.theme)

