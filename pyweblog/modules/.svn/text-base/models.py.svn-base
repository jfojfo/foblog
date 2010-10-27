import os
from utils import RegExpValidator

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.ext.db import djangoforms
from google.appengine.ext import db


__all__ = ['Post', 'Comment', 'Tag', 'Admin', 'User', 'UploadFile', 'Link', 'ConfigForm']

class Post(db.Model):
	title = db.StringProperty(required=True)
	date = db.DateTimeProperty(auto_now_add=True)
	author = db.UserProperty(required=True)
	content = db.TextProperty(required=True)
	last_modify_date = db.DateTimeProperty()
	last_modify_by = db.UserProperty()
	tags = db.StringListProperty()
	type = db.StringProperty(default = 'post', choices = ['post', 'page'])
	slug = db.StringProperty() # a URL-friendly name  TODO: verify
	comment_count = db.IntegerProperty(default = 0)

	def comment_count_disp(self):
		cnt = self.comment_count
		if cnt == 0:
			return 'No Comments'
		if cnt == 1:
			return '1 Comment'

		return '%d Comments' % cnt

	def author_disp(self):
		admin = Admin.all().filter('user = ', self.author).get()
		return unicode(admin)

class Comment(db.Model):
	post = db.ReferenceProperty(Post)
	date = db.DateTimeProperty(auto_now_add=True)
	author = db.UserProperty(required=True)
	content = db.TextProperty(required=True)
	last_modify_date = db.DateTimeProperty()
	last_modify_by = db.UserProperty()

	def author_disp(self):
		user = User.all().filter('user = ', self.author).get()
		if user:
			return unicode(user)
		else:
			return self.author.nickname()

	def author_with_url(self):
		user = User.all().filter('user = ', self.author).get()
		if user:
			if (user.website):
				return u'<a href="%s" target="_blank">%s</a>' % (user.website, user)
			else:
				return unicode(user)
		else:
			return self.author.nickname()


class Tag(db.Model):
	name = db.StringProperty()
	count = db.IntegerProperty(required=True)

class Admin(db.Model):
	user = db.UserProperty(required = True)
	dispname = db.StringProperty()
	api_password = db.StringProperty()

	def __unicode__(self):
		if self.dispname:
			return self.dispname
		else:
			return self.user.nickname()

	def __str__(self):
		return self.__unicode__().encode('utf-8')

class User(db.Model):
	user = db.UserProperty(required = True)
	dispname = db.StringProperty()
	website = db.LinkProperty()

	def __unicode__(self):
		if self.dispname:
			return self.dispname
		else:
			return self.user.nickname()

	def __str__(self):
		return self.__unicode__().encode('utf-8')


class UploadFile(db.Model):
	data = db.BlobProperty()
	orig_name = db.StringProperty()
	ext = db.StringProperty()
	date = db.DateTimeProperty(auto_now_add=True)

	def name(self):
		if self.ext:
			return str(self.key()) + '.' + self.ext
		else:
			return str(self.key())


class Link(db.Model):
	url = db.LinkProperty(required=True)
	text = db.StringProperty(required=True)
	tags = db.StringListProperty()
	description = db.StringProperty()


class Config(db.Expando):
	plog_title = db.StringProperty(default = 'Plog')
	plog_subtitle = db.StringProperty(default = '')
	app_root = db.StringProperty(default = '', validator = RegExpValidator(r'^[\w\-\/]*$'))
	posts_per_page = db.IntegerProperty(default = 10)
	comments_per_page = db.IntegerProperty(default = 10)
	recent_posts = db.IntegerProperty(default = 5)
	recent_comments = db.IntegerProperty(default = 5)
	perma_post_url = db.StringProperty(default = '/post/%id%') # available tags: id, postid, slug, yyyy, mm, dd
	perma_page_url = db.StringProperty(default = '/%slug%')
	tag_base = db.StringProperty(default = '/tag')
	rss_posts = db.IntegerProperty(default = 10)
	default_host = db.StringProperty(default = 'http://%s.appspot.com' % os.environ['APPLICATION_ID'])
	site_keywords = db.StringProperty(default = '')
	site_description = db.StringProperty(default = '')
	theme = db.StringProperty(required = True, default = 'default', choices = os.listdir('themes'))
	custom_header = db.TextProperty(default = '')
	custom_sidebar = db.TextProperty(default = '')
	custom_sidebar1 = db.TextProperty(default = '')
	custom_sidebar2 = db.TextProperty(default = '')
	custom_footer = db.TextProperty(default = '')
	enable_memcache = db.BooleanProperty(default = False)
	comment_notify_email = db.BooleanProperty(default = False)


class ConfigForm(djangoforms.ModelForm):
	class Meta:
		model = Config

