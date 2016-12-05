import os
import webapp2
import re

import jinja2

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

class SteveHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))


class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.out.write(form)

class Base(SteveHandler):
	def get(self):
		self.render("base.html")

class Blog(SteveHandler):
	def get(self):
		self.render("blog.html")

class SignUp(SteveHandler):
	def get(self):
		self.render("signup.html")

class NewPost(SteveHandler):
	def get(self):
		self.render("newpost.html")

app = webapp2.WSGIApplication([('/', Base),
								('/blog', Blog),
								('/blog/signup', SignUp),
								('/blog/newpost', NewPost)], debug=True)