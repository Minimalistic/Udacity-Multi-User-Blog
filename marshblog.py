import os
import re
import random
import hashlib
import hmac
from string import letters

import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'TheMostSecretOfSecrets'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

def render_post(response, post_tool):
    response.out.write('<b>' + post_tool.subject + '</b><br>')
    response.out.write(post_tool.content)

class MainPage(BlogHandler): # This renders the base.html if user goes to 
    def get(self):           # the root address
        self.render('base.html')

##### user stuff
def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


##### blog stuff

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

class PostDatabase(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    author = db.StringProperty()

    def render(self): # renderpost is used to render jinja templates
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", renderpost = self)

class BlogFront(BlogHandler):
    def get(self):
        allposts = db.GqlQuery  \
        ("SELECT * FROM PostDatabase ORDER BY created DESC LIMIT 10")
        self.render('blog.html',    # takes the allposts db query and
                    allposts = allposts) # renders results

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('PostDatabase', int(post_id), parent=blog_key())
        post_tool = db.get(key)

        if not post_tool:
            self.error(404)
            return

        self.render("permalink.html", post_tool = post_tool)

class EditPost(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('PostDatabase', int(post_id), parent=blog_key())
        post_tool = db.get(key)

        if self.user:
            self.render("editpost.html",
                        post_tool = post_tool,
                        subject = post_tool.subject,
                        content = post_tool.content,
                        post_id = post_id)

        else:
            self.redirect("/login")

    def post(self, post_id):
        key = db.Key.from_path('PostDatabase', int(post_id), parent=blog_key())
        post_tool = db.get(key)

        if not self.user:
            self.redirect('/blog')

        if self.user:
            subject = self.request.get('subject')
            content = self.request.get('content')

            if subject and content:
                key = db.Key.from_path('PostDatabase', int(post_id), parent=blog_key())
                post_tool = db.get(key)

                post_tool.subject = subject
                post_tool.content = content

                post_tool.put()
                
                self.redirect('/blog/%s' % str(post_tool.key().id()))
            else:
                error = "subject and content, please!"
                self.render("editpost.html", subject=subject, content=content, error=error)

class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.redirect('/blog')

        subject = self.request.get('subject')
        content = self.request.get('content')
        author = self.user.name

        if subject and content:
            post_tool = PostDatabase(parent = blog_key(),
                                            subject = subject,
                                            content = content,
                                            author = author)
            post_tool.put()
            self.redirect('/blog/%s' % str(post_tool.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html",
                        subject = subject,
                        content = content,
                        error = error)

class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username = self.username,
                      email = self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
            
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError

class Unit2Signup(Signup):
    def done(self):
        self.redirect('/unit2/welcome?username=' + self.username)

class Register(Signup):
    def done(self):
        #make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username = msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/blog')

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')

class Unit3Welcome(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')

class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/unit2/signup')

class Delete(BlogHandler):
    
    def post(self,post_id):
        if self.user:
            key = db.Key.from_path('PostDatabase', int(post_id), parent=blog_key())
            post = db.get(key)
            db.delete(key)
            self.redirect('/blog')

        else:
            self.redirect('/blog')

class Comment(db.Model):
    comment = db.StringProperty(required=True)
    post = db.ReferenceProperty(PostDatabase)
    user = db.ReferenceProperty(User)


class NewComment(BlogHandler):

    def get(self,post_id):

        if not self.user:
            return self.redirect("/login")
        key = db.Key.from_path("PostDatabase", int(post_id), parent=blog_key())
        post = db.get(key)
        
        subject = post.subject
        content = post.content
        self.render(
            "newcomment.html",
            subject=subject,
            content=content,
            post=post.key(),
            user=self.user.key(),
            )

    def post(self,post_id):
        if self.user:
            key = db.Key.from_path("PostDatabase", int(post_id), parent=blog_key())
            post = db.get(key)
            if not post:
                self.error(404)
                return
            if not self.user:
                return self.redirect("login")
            comment = self.request.get("comment")

            if comment:
                # check how author was defined
            
                c = Comment(comment=comment,user = self.user.key(),post=post.key())
                c.put()
                self.redirect("/blog/%s" % str(post.key().id()))

            else:
                error = "please comment"
                self.render(
                        "permalink.html",
                    post=post,
                    content=content,
                    error=error)
        else:
            self.redirect("/login")

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/unit2/signup', Unit2Signup),
                               ('/unit2/welcome', Welcome),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               ('/blog/delete/([0-9]+)', Delete),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/unit3/welcome', Unit3Welcome),
                               ('/blog/newcomment/([0-9]+)', NewComment),
                               ],
                              debug=True)
