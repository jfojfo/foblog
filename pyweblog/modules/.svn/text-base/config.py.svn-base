import os
import logging
from models import Config
from utils import Storage

__all__ = [ 'config', 'settings', ]

logging.info('module config reloaded')

settings = Storage()

config = Config.get_by_key_name('default')

if not config:
	config = Config(key_name = 'default')
	config.put()

if not config.app_root:
	settings.app_root = ''
else:
	settings.app_root = '/' + config.app_root.strip('/ ')

settings.home_page = settings.app_root + '/'

