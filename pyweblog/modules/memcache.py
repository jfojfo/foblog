import re
import logging
from datetime import datetime
from google.appengine.api import memcache
from google.appengine.ext import db

from config import config

logging.info('module memcache reloaded')


class LastModified(db.Model):
	item_name = db.StringProperty()
	last_modified = db.DateTimeProperty()

utcnow = datetime.utcnow()
obj_last_modify = {
		'post' : utcnow,
		'comment' : utcnow,
		'config' : utcnow,
		'link' : utcnow,
		'upload' : utcnow,
		}

for key in obj_last_modify:
	item = LastModified.get_by_key_name(key)
	if not item:
		item = LastModified(key_name = key, item_name = key, last_modified = obj_last_modify[key])
		item.put()
	else:
		obj_last_modify[key] = item.last_modified

refresh_roles = {
		'.+:page:.+' : ('comment', 'post', 'config', 'link', 'upload'),
		'(guest|login|admin):widget:recentcomments.*' : ('comment', 'config'),
		'(guest|login|admin):widget:recentposts.*' : ('post', 'config'),
		'(guest|login|admin):widget:link.*' : ('link', 'config'),
		'(guest|login|admin):widget:.*' : ('comment', 'post', 'link', 'config'), # TODO check this line...
		'feed:post' : ('post', 'config'),
		'feed:tag:.*' : ('post', 'config'),
		}

class MemcacheItem:
	def __init__(self, key, value):
		self.key = key
		self.value = value
		self.timestamp = datetime.utcnow()

def check_expire(memcache_item):
	for role in refresh_roles:
		if re.match(role, memcache_item.key):
			for obj in refresh_roles[role]:
				if memcache_item.timestamp < obj_last_modify[obj]:
					return True
			return False
	logging.warning('No refresh role for %s' % key)
	return True


def notify_update(key):
	if not config.enable_memcache:
		return
	logging.info('%s has been changed, some memcache item need update' % key)
	obj_last_modify[key] = datetime.utcnow()
	item = LastModified.get_by_key_name(key)
	item.last_modified = obj_last_modify[key]
	item.put()

def get(key):
	if not config.enable_memcache:
		return None

	key = key[:250]

	item = memcache.get(key)
	if item == None:
		logging.debug('NONE Memcache item %s' % key)
		return None
	else:
		if check_expire(item):
			logging.info('NEED REFRESH Memcache item %s' % key)
			return None
		else:
			logging.debug('HIT Memcache item %s' % key)
			return item.value

def set(key, value, time=0):
	if not config.enable_memcache:
		return

	key = key[:250]
	if memcache.set(key, MemcacheItem(key, value), time):
		logging.debug('SET Memcache item %s' % key)
	else:
		logging.error('SET Memcache item %s FAILED!' % key)

