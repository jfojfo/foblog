import sys
import wsgiref.handlers

sys.path.append('modules')
from base import *
from models import *
from api import dispatcher
from django.utils.html import linebreaks, escape, urlize
from django.utils.feedgenerator import Rss201rev2Feed, Atom1Feed
from mimetypes import types_map
from google.appengine.api import mail

# {{{ Handlers
# {{{ Plog
class NewPost(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			self.current_page = "new"
			self.template_values.update({
				'mode' : 'new',
				})
			self.render(self.theme.editpost_page)

	def post(self):
		if self.chk_admin():
			title = self.param('title')
			content = self.param('post_content')
			tags = split_tags(self.param('tags'))
			type = self.param('type')

			try:
				new_article(title = title, author = self.login_user, content = content, tags = tags, type = type)

				self.redirect(settings.home_page)
			except db.BadValueError, e:
				self.redirect(settings.home_page)

class NewComment(PlogRequestHandler):
	def post(self):
		if self.chk_login():
			content = self.param('comment_content')
			postid = self.param('postid')
			nick = self.param('nick')
			site = self.param('site')
			#post = Post.get_by_id(int(postid))

			try:
				new_comment(postid = postid, content = content, author = self.login_user, nick = nick, site = site)
				self.redirect('%s/post/%s' % (settings.app_root, postid))
			except db.BadValueError, e:
				self.redirect(settings.home_page)

class EditPost(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			self.current_page = "new"
			postid = self.request.path[len(settings.app_root) + len('/admin/editpost/'):]
			post = Post.get_by_id(int(postid))
			self.template_values.update({
				'post' : post,
				'mode' : 'edit',
				})
			self.render(self.theme.editpost_page)

	def post(self):
		if self.chk_admin():
			postid = self.request.path[len(settings.app_root) + len('/admin/editpost/'):]
			edit_article(
					postid = postid,
					title = self.param('title'),
					content = self.param('post_content'),
					tags = split_tags(self.param('tags')),
					slug = self.param('slug'),
					type = self.param('type')
					)

			self.redirect(settings.home_page)

class DeletePost(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			postid = self.param('postid')
			delete_post(int(postid))
			self.redirect(settings.home_page)

class DeleteComment(PlogRequestHandler):
	def get(self):
		if self.chk_login():
			commentid = self.param('commentid')
			postid = delete_comment(commentid, self.login_user, self.is_admin)
			if postid:
				self.redirect('%s/post/%d' % (settings.app_root, postid))
			else:
				self.redirect(settings.home_page)

class PostList(PlogRequestHandler):
	def get(self):
		self.current_page = "home"
		page = 0
		show_prev = False
		show_next = False

		all_posts = Post.all().filter('type = ', 'post')
		max_page = (post_count() - 1) / config.posts_per_page

		if self.request.path.startswith('%s/page/' % settings.app_root):
			page = int(self.request.path[len(settings.app_root) + len('/page/'):])

			if page < 0 or page > max_page:
				self.error_404()
				return

		posts = all_posts.order('-date').fetch(config.posts_per_page, offset = page * config.posts_per_page)

		show_prev = not (page == 0)
		show_next = not (page == max_page)

		if not posts:
			show_prev = False
			show_next = False

		self.template_values.update({
				'posts' : posts,
				'show_prev' : show_prev,
				'show_next' : show_next,
				'show_page_panel' : show_prev or show_next,
				'prev' : page - 1,
				'next' : page + 1,
				'max_page' : max_page,
				})

		self.render(self.theme.postlist_page)

class PostListTag(PlogRequestHandler):
	def get(self):
		self.current_page = "home"
		page = 0
		show_prev = False
		show_next = False

		params = self.request.path[len(settings.app_root) + 1:].split('/')
		if len(params) == 4:
			page = int(params[3])

		import urllib2
		tag = urllib2.unquote(params[1]).decode('utf-8')

		all_posts = Post.all().filter('type = ', 'post').filter('tags =', tag)
		max_page = (post_count(tag) - 1) / config.posts_per_page
		posts = all_posts.order('-date').fetch(config.posts_per_page, offset = page * config.posts_per_page)

		show_prev = not (page == 0)
		show_next = not (page == max_page)

		if not posts:
			self.error_404()

		self.template_values.update({
				'tag' : tag,
				'posts' : posts,
				'show_prev' : show_prev,
				'show_next' : show_next,
				'show_page_panel' : show_prev or show_next,
				'prev' : page - 1,
				'next' : page + 1,
				'max_page' : max_page,
				})

		self.render(self.theme.postlist_page)

class ViewPost(PlogRequestHandler):
	def get(self):
		self.current_page = "home"
		postid = self.request.path[len(settings.app_root) + len('/post/'):]
		post = Post.get_by_id(int(postid))
		comments = Comment.all().filter('post = ', post).order('date')

		if not post:
			self.error_404()
		else:
			self.template_values.update({
					'post' : post,
					'comments' : comments,
					})

			self.render(self.theme.viewpost_page)

class Feed(PlogRequestHandler):
	def get(self):
		feed_type = self.param('type')
		if feed_type.lower() == 'atom' or feed_type.lower() == 'atom1':
			feed_type = 'atom1'
		else:
			feed_type = 'rss2'

		tag = self.param('tag')

		feed_title = config.plog_title

		if tag:
			feed_title += u' - Tag: ' + tag
			posts = Post.all().filter('type = ', 'post').filter('tags = ', tag).order('-date').fetch(config.rss_posts)
		else:
			posts = Post.all().filter('type = ', 'post').order('-date').fetch(config.rss_posts)

		if feed_type == 'rss2':
			feed = Rss201rev2Feed(
					title = feed_title,
					link = config.default_host + settings.home_page,
					description= u'latest %d posts of %s' % (min(len(posts), config.rss_posts), config.plog_title),
					subtitle = config.plog_subtitle
					)
		elif feed_type == 'atom1':
			feed = Atom1Feed(
					title = feed_title,
					link = config.default_host + settings.home_page,
					description = u'latest %d posts of %s' % (min(len(posts), config.rss_posts), config.plog_title),
					subtitle = config.plog_subtitle
					)

		for post in posts:
			post_url = '%s%s/post/%d' % (config.default_host, settings.app_root, post.key().id()) # TODO permernent URL

			if feed_type == 'rss2':
				feed.add_item(
						title = post.title,
						author_email = post.author.nickname(),	# in django's implementation of rss2,
																# if author email not set,
																# author will not appear in feed,
																# but we don not want leak author's email.
						link = post_url,
						description = post.content,
						pubdate = post.date,
						unique_id = post_url,
						categories = post.tags
						)
			elif feed_type == 'atom1':
				feed.add_item(
						title = post.title,
						author_name = post.author.nickname(),
						link = post_url,
						description = post.content,
						pubdate = post.date,
						unique_id = post_url,
						categories = post.tags
						)

		self.response.headers['Content-Type'] = 'application/rss+xml; charset=utf-8'
		from StringIO import StringIO
		buffer = StringIO()
		feed.write(buffer, 'utf-8')
		feed_xml = buffer.getvalue()
		buffer.close()
		self.write(feed_xml)

class LogInOut(PlogRequestHandler):
	def get(self):
		if self.request.path == '%s/login' % settings.app_root:
			self.redirect(self.get_login_url(True))

		if self.request.path == '%s/logout' % settings.app_root:
			self.redirect(self.get_logout_url(True))

class Download(PlogRequestHandler):
	def get(self):
		filename = self.request.path[len(settings.app_root) + len('/upload/'):]
		split = filename.rfind('.')
		if split == -1:
			name, ext = filename, ''
		else:
			name = filename[:split]
			ext = filename[split + 1:]

		file = UploadFile.get(db.Key(name))
		if not file:
			self.error_404()
		elif file.ext != ext:
			self.error_404()
		else:
			ext = '.' + ext
			mimetype = 'application/octet-stream'
			if types_map.has_key(ext):
				mimetype = types_map[ext]
			self.response.headers['Content-Type'] = mimetype
			self.response.headers['Content-Disposition'] = 'inline; filename="' + file.orig_name.encode('utf-8') + '"'
			self.write(file.data)

# }}}

# {{{ Admin
class Configure(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			self.current_page = "config"
			config_form = ConfigForm(instance = config)
			self.template_values.update({
				'config_form' : config_form,
				})

			self.render(self.theme.config_page)

	def post(self):
		if self.chk_admin():
			config_form = ConfigForm(data = self.request.POST, instance = config)
			if config_form.is_valid():
				config_form.save(commit=False)
				config.put()

				reconfig()
				regenerate_url_mapping()
				settings.theme = Theme(config.theme)

				memcache.notify_update('config')
				self.redirect(settings.home_page)
			else:
				self.template_values.update({
					'config_form' : config_form,
					})

				self.render(self.theme.config_page)


class Upload(PlogRequestHandler):
	def post(self):
		if self.chk_admin():
			filename = self.param('filename')
			fileext = self.param('fileext')
			data = self.param('upfile')
			UploadFile(orig_name = filename, ext = fileext, data = data).put()
			memcache.notify_update('upload')
			self.redirect('%s/admin/filemanager' % settings.app_root)

class FileManager(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			self.current_page = "upload"
			files = UploadFile.all().order('-date')
			self.template_values.update({
				'files' : files,
				})
			self.render(self.theme.filemanager_page)

	def post(self): # delete files
		if self.chk_admin():
			delids = self.request.POST.getall('del')
			if delids:
				for id in delids:
					file = UploadFile.get_by_id(int(id))
					file.delete()
					memcache.notify_update('upload')
			self.redirect('%s/admin/filemanager' % settings.app_root)

class LinkManager(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			if self.param('tag'):
				links = Link.all().filter('tags = ', self.param('tag')).order('text')
			else:
				links = Link.all().order('text')

			self.template_values.update({
				'links' : links,
				})
			self.render(self.theme.linkmanager_page)

	def post(self):
		if self.chk_admin():
			try:
				action = self.param('action')
				if action == 'new':
					tags = split_tags(self.param('linktags'))
					if not tags:
						tags = [' ']
					link = Link(
							url = self.param('url'), text = self.param('text'),
							description = self.param('description'),
							tags = tags)
					link.put()
				elif action == 'edit':
					link = Link.get_by_id(int(self.param('linkid')))
					link.text = self.param('text')
					link.url = self.param('url')
					link.description = self.param('description')
					link.tags = split_tags(self.param('linktags'))
					link.put()
				elif action == 'delete':
					linkids = self.request.POST.getall('linkid')
					for linkid in linkids:
						link = Link.get_by_id(int(linkid))
						link.delete()

				memcache.notify_update('link')
			except Exception, e:
				raise e

			self.redirect(self.referer)

class ReGeneratePassword(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			password = regenerate_password(self.user.user)
			self.response.headers['Content-Type'] = 'text/plain'
			self.write(password)

class ViewMemcacheStats(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			table_memcache_status = render_dict(memcache.memcache.get_stats())
			table_obj_last_modify = render_dict(memcache.obj_last_modify)
			table_theme_mapping = render_dict(settings.theme.mapping_cache)

			self.write('''
			<h1>Memcache Status</h1>%s
			<h1>Last Modify</h1>%s
			<h1>Theme Mapping</h1>%s
			''' % (table_memcache_status, table_obj_last_modify, table_theme_mapping))

class ViewMemcacheContent(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			content = memcache.memcache.get(self.param('key'))
			self.write('<textarea style="width:100%%;height:100%%">%s</textarea>' % cgi.escape(str(content)))

class CheckDataIntegrity(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			msgs = check_data_integrity()
			if not msgs:
				self.write('Great! Data seems all good!')
			else:
				for msg in msgs:
					self.write(msg + '<br />')
				self.write('<form method="post"><input type="submit" value="fix them all!" /></form>')

	def post(self): # fix
		if self.chk_admin():
			check_data_integrity(True)
			memcache.memcache.flush_all()
			self.redirect('checkdataintegrity')

class FlushMemcache(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			memcache.memcache.flush_all()
			self.redirect(settings.home_page)


# TODO remove this handler
class ImportBlogRoll(PlogRequestHandler):
	class BlogRoll(db.Model):
		text = db.StringProperty()
		url = db.LinkProperty()
		description = db.StringProperty()

	def get(self):
		if self.chk_admin():
			for link in ImportBlogRoll.BlogRoll.all():
				Link(text = link.text, url = link.url, description = link.description, tags = ['Blogroll']).put()
				link.delete()

			self.redirect('linkmanager')

class FixDefaultPageType(PlogRequestHandler):
	def get(self):
		if self.chk_admin():
			for post in Post.all():
				post.put()

			self.redirect(settings.home_page)
#}}}

# {{{ Theme Files
class GetFile(webapp.RequestHandler):
	def get(self):
		cwd = os.getcwd()
		theme_path = os.path.join(cwd, 'themes')
		max_age = 600  #expires in 10 minutes

		request_path = self.request.path[len(settings.app_root) + len('/themes/'):]
		server_path = os.path.normpath(os.path.join(cwd, 'themes', request_path))
		last_config_time = memcache.obj_last_modify['config'].replace(microsecond=0)

		if self.request.if_modified_since and self.request.if_modified_since.replace(tzinfo=None) >= last_config_time:
			self.response.headers['Date'] = format_date(datetime.datetime.utcnow())
			self.response.headers['Last-Modified'] = format_date(last_config_time)
			cache_expires(self.response, max_age)
			self.response.set_status(304)
			self.response.clear()

		elif server_path.startswith(theme_path):
			ext = os.path.splitext(server_path)[1]
			if types_map.has_key(ext):
				mime_type = types_map[ext]
			else:
				mime_type = 'application/octet-stream'
			try:
				self.response.headers['Content-Type'] = mime_type
				self.response.headers['Last-Modified'] = format_date(last_config_time)
				cache_expires(self.response, max_age)
				self.response.out.write(open(server_path, 'rb').read())
			except Exception, e:
				logging.info(e)
				self.error_404()
		else:
			self.error_404()

#}}}

# {{{ API
class CallApi(PlogRequestHandler):
	def get(self):
		self.write('<h1>please use POST to use APIs</h1>')

	def post(self):
		request = self.request.body
		response = dispatcher._marshaled_dispatch(request)
		self.write(response)

#}}}

# {{{ Not Found
class NotFound(PlogRequestHandler):
	def get(self):
		self.error_404()
# }}}

#}}}

# {{{ url mapping

url_mapping = []
url_mapping_admin = []

def regenerate_url_mapping():
	global url_mapping
	global url_mapping_admin

	url_mapping = [
			# plog
			('/', PostList),
			('%s' % settings.app_root, PostList),
			('%s/' % settings.app_root, PostList),
			('%s/page/\\d+' % settings.app_root, PostList),
			('%s/tag/.+/page/\\d+' % settings.app_root, PostListTag),
			('%s/tag/.+' % settings.app_root, PostListTag),
			('%s/post/\\d+' % settings.app_root, ViewPost),
			('%s/newcomment' % settings.app_root, NewComment),
			('%s/deletecomment' % settings.app_root, DeleteComment),
			('%s/feed' % settings.app_root, Feed),
			('%s/login' % settings.app_root, LogInOut),
			('%s/logout' % settings.app_root, LogInOut),
			('%s/upload/.+' % settings.app_root, Download),
			# theme files
			('%s/themes/[\\w\\-]+/templates/.*' % settings.app_root, NotFound),
			('%s/themes/[\\w\\-]+/.+' % settings.app_root, GetFile),
			# api
			('%s/api/xml-rpc' % settings.app_root, CallApi),
			]

	url_mapping_admin = url_mapping[:]
	url_mapping_admin += [
			# admin
			('%s/admin/newpost' % settings.app_root, NewPost),
			('%s/admin/editpost/\\d+' % settings.app_root, EditPost),
			('%s/admin/deletepost' % settings.app_root, DeletePost),
			('%s/admin/regeneratepassword' % settings.app_root, ReGeneratePassword),
			('%s/admin/memcachestats' % settings.app_root, ViewMemcacheStats),
			('%s/admin/memcachecontent' % settings.app_root, ViewMemcacheContent),
			('%s/admin/checkdataintegrity' % settings.app_root, CheckDataIntegrity),
			('%s/admin/flushmemcache' % settings.app_root, FlushMemcache),
			('%s/admin/config' % settings.app_root, Configure),
			('%s/admin/upload' % settings.app_root, Upload),
			('%s/admin/filemanager' % settings.app_root, FileManager),
			('%s/admin/linkmanager' % settings.app_root, LinkManager),
			('%s/admin/addlink' % settings.app_root, LinkManager),
			('%s/admin/dellink' % settings.app_root, LinkManager),
			('%s/admin/importblogroll' % settings.app_root, ImportBlogRoll),
			('%s/admin/FixDefaultPageType' % settings.app_root, FixDefaultPageType),
			]
	url_mapping.append(('.*', NotFound))
	url_mapping_admin.append(('.*', NotFound))
	logging.info('url mapping regenerated')

regenerate_url_mapping()
# }}}

def main():
	if users.is_current_user_admin():
		logging.debug('admin')
		mapping = url_mapping_admin
	else:
		logging.debug('user')
		mapping = url_mapping

	webapp.template.register_template_library('filter')
	application = webapp.WSGIApplication(
			mapping,
			debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()

