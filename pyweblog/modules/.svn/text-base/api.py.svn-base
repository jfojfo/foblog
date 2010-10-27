import xmlrpclib
import sys
import cgi
import logging

from datetime import datetime
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

from base import *
from models import *

__all__ = ['dispatcher']

def blogger_getUsersBlogs(discard, username, password):
	if not check_api_user_pass(username, password):
		raise Exception, 'access denied'

	return [{'url' : config.default_host + '{{ settings.home_page }}', 'blogid' : 'plog_001', 'blogName' : config.plog_title}]

def metaWeblog_newPost(blogid, username, password, content, publish):
	user = check_api_user_pass(username, password)
	if not user:
		raise Exception, 'access denied'

	if publish:
		if content.has_key('categories'):
			tags = content['categories']
		else:
			tags = []
		postid = new_article(title = content['title'], content = content['description'], author = user, tags = tags)
		return str(postid)
	else:
		return 'notpublished'

def metaWeblog_editPost(postid, username, password, content, publish):
	user = check_api_user_pass(username, password)
	if not user:
		raise Exception, 'access denied'

	if publish:
		edit_article(postid = postid, title = content['title'], content = content['description'], author = user, tags = content['categories'], date = datetime.datetime.utcnow())
		return True
	else:
		return True

def metaWeblog_getCategories(blogid, username, password):
	user = check_api_user_pass(username, password)
	if not user:
		raise Exception, 'access denied'

	categories = []
	all_tags = Tag.all()
	for tag in all_tags:
		categories.append({'description' : tag.name, 'title' : tag.name})

	return categories

def metaWeblog_getPost(postid, username, password):
	user = check_api_user_pass(username, password)
	if not user:
		raise Exception, 'access denied'

	post = Post.get_by_id(int(postid))

	return {
			'postid' : postid,
			'dateCreated' : post.date,
			'title' : post.title,
			'description' : unicode(post.content),
			'categories' : post.tags,
			'publish' : True,
			}

def metaWeblog_getRecentPosts(blogid, username, password, numberOfPosts):
	posts = Post.all().order('-date').fetch(min(numberOfPosts, 20))
	result = []
	for post in posts:
		result.append({
			'postid' : str(post.key().id()),
			'dateCreated' : post.date,
			'title' : post.title,
			'description' : unicode(post.content),
			'categories' : post.tags,
			'publish' : True,
			})

	return result


def blogger_deletePost(appkey, postid, username, password, publish):
	user = check_api_user_pass(username, password)
	if not user:
		raise Exception, 'access denied'

	delete_post(postid)
	return True

class PlogXMLRPCDispatcher(SimpleXMLRPCDispatcher):
	def __init__(self, funcs):
		SimpleXMLRPCDispatcher.__init__(self, True, 'utf-8')
		self.funcs = funcs

dispatcher = PlogXMLRPCDispatcher({
	'blogger.getUsersBlogs' : blogger_getUsersBlogs,
	'blogger.deletePost' : blogger_deletePost,
	'metaWeblog.newPost' : metaWeblog_newPost,
	'metaWeblog.editPost' : metaWeblog_editPost,
	'metaWeblog.getCategories' : metaWeblog_getCategories,
	'metaWeblog.getPost' : metaWeblog_getPost,
	'metaWeblog.getRecentPosts' : metaWeblog_getRecentPosts,
	})

