import re
from models import *

import webapp2

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
        if self.user:
            key = db.Key.from_path('PostDatabase', int(post_id), parent=blog_key())
            post_tool = db.get(key)
            # Check to see if the logged in user is the post's author
            if post_tool.user_id == self.user.key().id(): 
                self.render("editpost.html",
                            post_tool = post_tool,
                            subject = post_tool.subject,
                            content = post_tool.content,
                            post_id = post_id)
            else:
                self.write("not self.user")
        else: # Isn't a user, told they need to be one and offers signup
            self.write("Must be a registered user.")

    def post(self, post_id):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            self.write("IS SUBJECT AND CONTENT")
        else: # In case user tries to submit an empty edit form
            self.write("ELSE")

class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.write("NOT SELF.USER")

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post_tool = PostDatabase(parent = blog_key(),
                                            user_id = self.user.key().id(),
                                            subject = subject,
                                            content = content)
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
            self.redirect('/welcome')

class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error = msg)

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')

class WelcomeUser(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username = self.user.name)
        else:
            self.redirect('/signup')

class Delete(BlogHandler):
    
    def post(self,post_id):
        if self.user:
            key = db.Key.from_path('PostDatabase', int(post_id), parent=blog_key())
            post_tool = db.get(key)
            db.delete(key)
            self.redirect('/blog')

        else:
            self.redirect('/blog')

class NewComment(BlogHandler):

    def get(self,post_id):

        if not self.user:
            return self.redirect("/login")
        key = db.Key.from_path("PostDatabase", int(post_id), parent=blog_key())
        post_tool = db.get(key)
        
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
            post_tool = db.get(key)
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
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               ('/blog/delete/([0-9]+)', Delete),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/welcome', WelcomeUser),
                               ('/blog/newcomment/([0-9]+)', NewComment),
                               ],
                              debug=True)
