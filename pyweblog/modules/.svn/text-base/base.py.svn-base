import re
import os
import logging
import datetime
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from django.template import TemplateSyntaxError

from config import *
from models import *
from filter import *
from theme import Theme
from widget import Widget
import memcache

# {{{ Base class
class PlogRequestHandler(webapp.RequestHandler):
	def __init__(self):
		pass

	def initialize(self, request, response):
		webapp.RequestHandler.initialize(self, request, response)

		self.login_user = users.get_current_user()
		self.is_login = (self.login_user != None)
		if self.is_login:
			self.user = User.all().filter('user = ', self.login_user).get() or User(user = self.login_user)
		else:
			self.user = None

		self.is_admin = users.is_current_user_admin()
		if self.is_admin:
			self.auth = 'admin'
		elif self.is_login:
			self.auth = 'login'
		else:
			self.auth = 'guest'

		self.widget = Widget(self)
		self.theme = settings.theme

		try:
			self.referer = self.request.headers['referer']
		except:
			self.referer = None

		self.template_values = {
				'config' : config,
				'settings' : settings,
				'self' : self,
				'theme' : self.theme,
				'W' : self.widget,
				}

	def param(self, name, **kw):
		return self.request.get(name, **kw)

	def write(self, s):
		self.response.out.write(s)

	def render(self, name, values=None):
		if values == None:
			values = self.template_values
			html = memcache.get('%s:page:%s' % (self.login_user, self.request.path_qs))

			if html == None:
				try:
					html = template.render(name, values)
				except TemplateSyntaxError, e: # if theme files are not found, fall back to default theme
					logging.warning(e)
					settings.theme
					self.redirect(settings.home_page)
					return
				memcache.set('%s:page:%s' % (self.login_user, self.request.path_qs), html)

			self.response.out.write(html)

	def error_404(self):
		logging.warning(self.request.path_qs)
		self.response.set_status(404)
		self.template_values.update({
			'url' : self.request.uri,
			})
		self.render(self.theme.error_404_page)

	def get_login_url(self, from_referer=False):
		if from_referer:
			dst = self.referer
			if not dst : dst = settings.home_page
			return users.create_login_url(dst)
		else:
			return users.create_login_url(self.request.uri)

	def get_logout_url(self, from_referer=False):
		if from_referer:
			dst = self.referer
			if not dst : dst = settings.home_page
			return users.create_logout_url(dst)
		else:
			return users.create_logout_url(self.request.uri)

	def chk_login(self, redirect_url=settings.home_page):
		if self.is_login:
			return True
		else:
			self.redirect(redirect_url)
			return False

	def chk_admin(self, redirect_url=settings.home_page):
		if self.is_admin:
			return True
		else:
			self.redirect(redirect_url)
			return False


# }}}

# {{{ common post operations
# {{{ new_article
def new_article(title, content, author = users.get_current_user(), tags = [], date = None, filter = default_filter, slug = None, type = 'post'):
	if filter:
		content = filter(content)

	if date == None:
		post = Post(
				title = title,
				content = content,
				author = author,
				tags = tags,
				type = type,
				slug = slug
				)
	else:
		post = Post(
				title = title,
				content = content,
				author = author,
				tags = tags,
				date = date,
				type = type,
				slug = slug
				)
	key = post.put()

	if type == 'post':
		update_tag_count(old_tags = [], new_tags = tags)

	all_post_tag = Tag.get_by_key_name('all_post_tag')
	all_post_tag.count += 1
	all_post_tag.put()

	memcache.notify_update('post')
	return key.id()
# }}}

# {{{ edit_article
def edit_article(postid, title = None, content = None, author = users.get_current_user(), tags = None, date = None, filter = default_filter, slug = None, type = 'post'):
	if filter:
		content = filter(content)

	post = Post.get_by_id(int(postid))
	if title:
		post.title = title
	if content:
		post.content = content
	if author:
		post.last_modify_by = author
	if date:
		post.last_modify_date = date
	if tags != None:
		old_tags = post.tags
		post.tags = tags
	if slug:
		post.slug = slug
	
	post.type = type

	post.put()

	if type == 'post' and tags != None:
		update_tag_count(old_tags = old_tags, new_tags = tags)

	memcache.notify_update('post')
# }}}

# {{{ delete_post
def delete_post(postid):
	# TODO we may need a logical delete here
	post = Post.get_by_id(int(postid))
	if not post : return

	comments = Comment.all().filter('post = ', post)
	for comment in comments:
		comment.delete()

	old_tags = post.tags
	type = post.type
	post.delete()

	if type == 'post':
		update_tag_count(old_tags = old_tags, new_tags = [])

	all_post_tag = Tag.get_by_key_name('all_post_tag')
	all_post_tag.count -= 1
	all_post_tag.put()

	memcache.notify_update('post')
# }}}

# {{{ new_comment
def new_comment(postid, content, author, nick, site):
	post = Post.get_by_id(int(postid))

	try:
		comment = Comment(post = post, content = content, author = author)
		comment.put()
		post.comment_count += 1
		post.put()
		change_user_info(author, nick, site)
		memcache.notify_update('comment')

		if config.comment_notify_email:
			try:
				msg = mail.EmailMessage(
						sender = post.author.email(),
						subject = (u'New Comment From %s(%s)' % (nick, self.login_user.email())).encode('utf-8')
						)
				msg.to = post.author.email()
				msg.body = (u'Comment on [%s] by %s(%s) at %s:\n %s\n\n%s'
						% (post.title, nick, self.login_user.email(), datetime.datetime.utcnow(), content,
						config.default_host + '%s/post/' % settings.app_root + str(post.key().id()))).encode('utf-8')
				msg.send()
			except Exception, e:
				logging.error(e)

	except db.BadValueError, e:
		raise
# }}}

# {{{ delete_comment
def delete_comment(commentid, user, is_admin):
	comment = Comment.get_by_id(int(commentid))
	if is_admin or user == commentid.author:
		postid = comment.post.key().id()
		comment.post.comment_count -= 1
		comment.post.put()
		comment.delete()
		memcache.notify_update('comment')
		return postid
	else:
		return 0
# }}}

# }}}

# {{{ utility functions
# {{{ post_count
def post_count(tag = None):
	if not tag:
		tag_count = Tag.get_by_key_name('all_post_tag')
		if not tag_count:
			tag_count = Tag(key_name = 'all_post_tag', name = None, count = Post.all().filter('type = ', 'post').count())
			tag_count.put()
		return tag_count.count
	else:
		tag_count = Tag.all().filter('name = ', tag).get()
		if tag_count:
			return tag_count.count
		else:
			return 0
# }}}

# {{{ split_tags
def split_tags(s):
	tags = list(set([t.strip() for t in re.split('[,;\\/\\\\]*', s) if t != ''])) #uniq
	return tags
# }}}

# {{{ update_tag_count
def update_tag_count(old_tags = None, new_tags = None):
	if old_tags == None and new_tags == None:
		tags = []
		posts = Post.all().filter('type = ', 'post')
		for post in posts:
			tags += post.tags
		tags_set = set(tags)
		for tag in tags_set:
			t = Tag.all().filter('name = ', tag).get()
			if t:
				t.count = tags.count(tag)
			else:
				t = Tag(name = tag, count = tags.count(tag))

			t.put()

	else:
		added = [t for t in new_tags if not t in old_tags]
		deleted = [t for t in old_tags if not t in new_tags]

		for tag in added:
			t = Tag.all().filter('name = ', tag).get()
			if t:
				t.count = t.count + 1
			else:
				t = Tag(name = tag, count = 1)

			t.put()

		for tag in deleted:
			t = Tag.all().filter('name = ', tag).get()
			if t:
				t.count = t.count - 1
				if t.count == 0:
					t.delete()
				else:
					t.put()
			else:
				t = Tag(name = tag, count = 1)
				t.put()
#}}}

# {{{ regenerate_password
def regenerate_password(user):
	'''
	Generate a random string for using as api password, api user is user's full email
	'''
	from random import sample
	from md5 import md5
	s = 'abcdefghijklmnopqrstuvwxyz1234567890'
	password = ''.join(sample(s, 8))
	admin = Admin.all().filter('user = ', user).get()
	if not admin:
		admin = Admin(user = user)
	admin.api_password = md5(user.email() + 'plog' + password).hexdigest()
	admin.put()
	return password
# }}}

# {{{ check_api_user_pass
def check_api_user_pass(email, password):
	from random import sample
	from md5 import md5

	user = users.User(email)
	admin = Admin.all().filter('user = ', user).get()

	if not admin:
		return None

	if admin.api_password == md5(user.email() + 'plog' + password).hexdigest():
		return user

	return None
# }}}

# {{{ change_user_info
def change_user_info(user, nick, site):
	'''
	Change the information of a login user after comment.
	'''
	nick = nick.strip()
	nick = nick[:30]
	if len(nick) == 0 : nick = user.nickname()

	site = site.strip()
	if site == 'http://':
		site = None
	if not site: site = None

	userinfo = User.all().filter('user = ', user).get()
	if not userinfo:
		userinfo = User(user = user)

	try:
		userinfo.dispname = nick
		userinfo.website = site
		userinfo.put()
	except Exception, e:
		pass
# }}}

# {{{ render_dict
def render_dict(d):
	html = '<table border="1" cellpadding="2" cellspacing="0">\n'
	for key in d:
		html += '<tr><td>%s</td><td>%s</td></tr>\n' % (cgi.escape(key), cgi.escape(str(d[key])))
	html += '</table>'
	return html
# }}}

# {{{ check_data_integrity
def check_data_integrity(fixit = False):
	msgs = []
	all_posts = Post.all().filter('type = ', 'post')
	actual_count = all_posts.count()
	display_count = Tag.get_by_key_name('all_post_tag').count
	if not display_count == actual_count:
		if fixit:
			tmp = Tag.get_by_key_name('all_post_tag')
			tmp.count = actual_count
			tmp.put()
		else:
			msgs.append('ALL POST COUNT ERROR, should be %d, got %d' % (actual_count, display_count))


	tag_count = {}

	for post in all_posts:
		actual_comment_count = Comment.all().filter('post = ', post).count()
		display_comment_count = post.comment_count
		if not actual_comment_count == display_comment_count:
			if fixit:
				post.comment_count = actual_comment_count
				post.put()
			else:
				msgs.append('COMMENT COUNT FOR %s ERROR, should be %d, got %d' % (post.key().id(), actual_comment_count, display_comment_count))

		tags = post.tags
		for tag in tags:
			if tag_count.has_key(tag):
				tag_count[tag] += 1
			else:
				tag_count[tag] = 1


	for tag in Tag.all():
		if tag.name:
			if not tag_count.has_key(tag.name):
				if fixit:
					tag.delete()
				else:
					msgs.append('UNWANTED Tag(s) %s' % tag.name)

			else:
				if not tag.count  == tag_count[tag.name]:
					if fixit:
						tag.count = tag_count[tag.name]
						tag.put()
					else:
						msgs.append('TAG COUNT FOR %s ERROR, should be %d, got %d' % (tag.name, tag_count[tag.name], tag.count))

				del tag_count[tag.name]

	if len(tag_count) > 0:
		if fixit:
			for tag in tag_count:
				tmp = Tag(name = tag, count = tag_count[tag])
				tmp.put()
		else:
			msgs.append('NOT COUNTED Tag(s) %s' % tag_count)

	return msgs
# }}}

# {{{ format_date
def format_date(dt):
	return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
# }}}

# {{{ cache_expires
def cache_expires(response, seconds=0, **kw):
	"""
	Set expiration on this request.  This sets the response to
	expire in the given seconds, and any other attributes are used
	for cache_control (e.g., private=True, etc).

	this function is modified from webob.Response
	it will be good if google.appengine.ext.webapp.Response inherits from this class...
	"""
	if not seconds:
		# To really expire something, you have to force a
		# bunch of these cache control attributes, and IE may
		# not pay attention to those still so we also set
		# Expires.
		response.headers['Cache-Control'] = 'max-age=0, must-revalidate, no-cache, no-store'
		response.headers['Expires'] = format_date(datetime.datetime.utcnow())
		if 'last-modified' not in self.headers:
			self.last_modified = format_date(datetime.datetime.utcnow())
		response.headers['Pragma'] = 'no-cache'
	else:
		response.headers['Cache-Control'] = 'max-age=%d' % seconds
		response.headers['Expires'] = format_date(datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds))
# }}}

# {{{ reconfig
def reconfig():
	global config

	if not config.app_root:
		settings.app_root = ''
	else:
		settings.app_root = '/' + config.app_root.strip('/ ')

	settings.home_page = settings.app_root + '/'
	settings.theme = Theme(config.theme)
# }}}

# }}}

