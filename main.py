import os
import re
import random
import webapp2
import time
import jinja2
import hashlib
import string
import hmac
import logging

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

# FILE LEVEL FUNCTIONS #######################################################

# Strings
THE_SECRET = "TheSecretIs42"
user_error_str = "Not a valid username."
password_error_str = "Not a valid password."
passwordconfirm_error_str = "Passwords do not match."
email_error_str = "Not a valid email."


def blog_key(name='default'):
    """
    This is the key that defines a single blog and facilitiate multiple
    blogs on the same site.
    """
    return db.Key.from_path('blogs', name)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

# Checks for signup


def checkUser(user):
    user2 = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return user2.match(user)


def checkPass(pass1):
    pass2 = re.compile(r"^.{3,20}$")
    return pass2.match(pass1)


def checkPass2(pass1, pass2):
    return pass2 == pass1


def checkEmail(email):
    email2 = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    return email2.match(email) or email == ""

# Cookie related


def hash_str(s):
    return hmac.new(THE_SECRET, s).hexdigest()


def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

# Password related


def make_salt():
    return "".join(random.choice(string.letters) for x in xrange(5))


def make_password_hash(name, password, salt=make_salt()):
    h = hashlib.sha256(name + password + salt).hexdigest()
    return '%s|%s' % (h, salt)


def valid_password(name, password, h):
    # This compares input password with the input confirmation password
    split = h.split(",")
    hash = split[0]
    salt = split[1]

    logging.warning("h =" + h)
    logging.warning("make = " + make_password_hash(name, password, salt))
    return h == make_password_hash(name, password, salt)

# DATABASES ##################################################################

# Create a database for user information


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty(required=False)

# Create a database for blog post information


class PostDatabase(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)
    user = db.StringProperty(required=True)
    # likes = db.StringDatabase(required=True)

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", renderpost=self)

# Create a database for comment information


class Comment(db.Model):
    article_id = db.IntegerProperty(required=True)
    user = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

# HANDLERS ###################################################################


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def isLogged(self):
                cookie = self.request.cookies.get('username')
                if cookie and check_secure_val(cookie):
                                                return cookie.split("|")[0]

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def login(self, user):
            val = make_secure_val(str(user))
            self.response.headers.add_header("Set-Cookie", r"username=%s; Path=/" %val)
            self.redirect("/welcome")


class MainPage(BlogHandler):
    def get(self):
        articles = db.GqlQuery("SELECT * "
                               "FROM PostDatabase "
                               "ORDER BY created "
                               "DESC LIMIT 10")
        isLogged = self.isLogged()
        self.render('blog.html',        # takes the articles db query and
                    isLogged=isLogged,  # renders results
                    articles=articles)


class PostLinkHandler(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)

        comments = db.GqlQuery("SELECT * "
                               "FROM Comment WHERE "
                               "ancestor is :1 "
                               "order by created "
                               "desc limit 3", key)

        if not post_tool:
            self.error(404)
            return

        self.render("permalink.html",
                    post_tool=post_tool, comments=comments)


class EditPost(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)
        self.render("editpost.html",
                    post_tool=post_tool,
                    subject=post_tool.subject,
                    content=post_tool.content,
                    post_id=post_id)

    def post(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            key = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
            post_tool = db.get(key)
            post_tool.subject = subject
            post_tool.content = content

            post_tool.put()

            self.redirect('/%s' % str(post_tool.key().id()))

        else:  # In case user tries to submit an empty edit form
            error = "There must be a subject and content."
            self.render("editpost.html",
                        post_tool=post_tool,
                        subject=post_tool.subject,
                        content=post_tool.content,
                        post_id=post_id,
                        error=error)


class Delete(BlogHandler):
    def post(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        db.delete(key)
        self.redirect('/success')


class Success(BlogHandler):
    def get(self):
        self.render('success.html')


class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post_tool = PostDatabase(parent=blog_key(),
                                     subject=subject,
                                     content=content,
                                     likes=0)
            post_tool.put()
            self.redirect('/%s' % str(post_tool.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html",
                        subject=subject,
                        content=content,
                        error=error)


class LikePost(BlogHandler):
    def post(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)
        post_tool.likes += 1
        post_tool.put()
        time.sleep(.1)
        self.redirect('/')


class AddCommentHandler(BlogHandler):

    def get(self, post_id):
        self.render("addcomment.html")

    def post(self, post_id):
        comment_content = self.request.get('comment_content')

        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())

        c = Comment(parent=key,
                    comment_content=comment_content)
        c.put()

        self.redirect('/' + post_id)


class DeleteCommentHandler(BlogHandler):
    def post(self, post_id):
        postKey = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        comment = db.get(key)
        comment.delete()

        self.redirect('/' + post_id)


class EditCommentHandler(BlogHandler):
    def get(self, post_id):
        postKey = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        post_tool = db.get(key)

        self.render("editcomment.html",
                    post_tool=post_tool,
                    comment_content=post_tool.comment_content,
                    post_id=post_id)

    def post(self, post_id):
        comment_content = self.request.get('comment_content')
        postKey = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        post_tool = db.get(key)
        post_tool.comment_content = comment_content

        post_tool.put()

        self.redirect('/' + post_id)


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/([0-9]+)', PostLinkHandler),
                               ('/newpost', NewPost),
                               ('/editpost/([0-9]+)', EditPost),
                               ('/delete/([0-9]+)', Delete),
                               ('/like/([0-9]+)', LikePost),
                               ('/success', Success),
                               ('/([0-9]+)/addcomment/([0-9]+)', AddCommentHandler),
                               ('/comment/delete/([0-9]+)/([0-9]+)', DeleteCommentHandler),
                               ('/comment/edit/([0-9]+)/([0-9]+)', EditCommentHandler),
                               ],
                              debug=True)
