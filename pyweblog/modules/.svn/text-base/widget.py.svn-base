import sys
import logging
import traceback
from models import *
from config import *
import memcache
from google.appengine.ext.webapp import template
from google.appengine.ext import db

class WidgetGenerator:
	def __init__(self, gen_func_name, handler):
		self.gen_func_name = gen_func_name
		self.gen_func = eval(gen_func_name)
		self.handler = handler
		self.params = {}

	def __str__(self):
		try:
			memcache_key = '%s:widget:%s:%s' % (self.handler.auth, self.gen_func_name, self.params)
			html = memcache.get(memcache_key)

			if html == None:
				html = self.gen_func(self.handler.template_values, self.params)
				if html == None:
					html = ''
				memcache.set(memcache_key, html)

			return html
		except Exception, e:
			return str(e)

	def set_params(self, params):
		params_dict = eval(params)
		self.params.update(params_dict)

class Widget:
	def __init__(self, handler):
		self.handler = handler

	def __getitem__(self, name):
		return WidgetGenerator(name.lower(), self.handler)

def render_s(template, values):
	from django.template import Context, Template
	t = Template(template.encode('utf-8'))
	c = Context(values)
	return t.render(c)

theme = settings.theme

# {{{ Widget HTML generator
# {{{
def renderpart(values, params):
	value = getattr(config, 'custom_' + params['part'])
	if value:
		return render_s(value, values)

def renderpart_header(values, params):
	value = config.custom_header
	if value:
		return render_s(value, values)

def renderpart_sidebar1(values, params):
	value = config.custom_sidebar1
	if value:
		return render_s(value, values)

def renderpart_sidebar2(values, params):
	value = config.custom_sidebar2
	if value:
		return render_s(value, values)

def renderpart_footer(values, params):
	value = config.custom_footer
	if value:
		return render_s(value, values)
# }}}

def recentcomments(values, params):
	p = {
			'n' : 10,
			}

	p.update(params)

	recent_comments = Comment.all().order('-date').fetch(p['n'])
	values.update({
		'recent_comments' : recent_comments,
		})
	return template.render(theme.recentcomments_widget, values)

def recentposts(values, params):
	p = {
			'n' : 10,
			}

	p.update(params)

	recent_posts = Post.all().filter('type = ', 'post').order('-date').fetch(p['n'])
	values.update({
		'recent_posts' : recent_posts,
		})
	return template.render(theme.recentposts_widget, values)

def links(values, params):
	p = {
			'tag' : '',
			'title' : '',
			}

	p.update(params)

	if not p['title'] : p['title'] = p['tag']
	if not p['tag'] : p['tag'] = ' '

	links = Link.all().filter('tags = ', p['tag']).order('text')
	values.update({
		'widget_links' : links,
		})
	values.update(p)

	return template.render(theme.links_widget, values)

def tags(values, params):
	p = {
			'n' : 999,
			}

	p.update(params)

	tags = Tag.all().order('-count').fetch(limit = p['n'] + 1)
	values.update({
		'tags' :tags,
		})
	return template.render(theme.tags_widget, values)
# }}}

