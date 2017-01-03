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
user_err_string = "Not a valid username."
pass_err_string = "Not a valid password."
pass2_err_string = "Passwords do not match."
email_err_string = "Not a valid email."


def blog_key(name='default'):
    """
    This is the key that defines a single blog and facilitiate multiple
    blogs on the same site.
    """
    return db.Key.from_path('blogs', name)


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


def make_pw_hash(name, pw, salt=make_salt()):
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)


def valid_pw(name, pw, h):
    # This compares input password with the input confirmation password
    split = h.split(",")
    hash = split[0]
    salt = split[1]

    logging.warning("h =" + h)
    logging.warning("make = " + make_pw_hash(name, pw, salt))
    return h == make_pw_hash(name, pw, salt)


# DATABASES ##################################################################

# Create a database for user information


class User(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

# Create a database for blog post information


class Article(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    edited = db.DateTimeProperty(auto_now=True)
    user = db.StringProperty(required=True)
    likes = db.IntegerProperty(default=0)

# Create a database for comment information


class Comment(db.Model):
    article_id = db.IntegerProperty(required=True)
    user = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


# HANDLERS ###################################################################


class BlogHandler(webapp2.RequestHandler):
    # Checks if the user is logged in
    def isLogged(self):
        cookie = self.request.cookies.get('username')
        if cookie and check_secure_val(cookie):
            return cookie.split("|")[0]

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    # Sets the cookie for login and redirects to welcome page
    def login(self, user):
        val = make_secure_val(str(user))
        self.response.headers.add_header("Set-Cookie",
                                         r"username=%s; Path=/" % val)
        self.redirect("/welcome")


class MainPage(BlogHandler):
    def get(self):
        articles = db.GqlQuery("SELECT * "
                               "FROM Article "
                               "ORDER BY created "
                               "DESC LIMIT 10")
        isLogged = self.isLogged()
        self.render("blog.html",        # takes the articles db query and
                    isLogged=isLogged,  # renders results
                    articles=articles)


# Sign up page handler, shows a sign up form if user is not logged in
class SignUpHandler(BlogHandler):
    def get(self):
        if(self.isLogged()):
            self.redirect("/")
        else:
            self.render("signup.html",
                        user_error="",
                        pass_error="",
                        pass2_error="",
                        email_error="")

    def post(self):
        user = self.request.get("username")
        pass1 = self.request.get("password")
        pass2 = self.request.get("verify")
        email = self.request.get("email")

        # Checking every field
        user_ok = checkUser(user)
        pass_ok = checkPass(pass1)
        pass2_ok = checkPass2(pass1, pass2)
        email_ok = checkEmail(email)

        # Checking if all fields are ok
        if(user_ok and pass_ok and pass2_ok and email_ok):

            # Checking if the user already exists
            existing_user = db.GqlQuery("""SELECT * FROM User
                                        WHERE username=\'""" +
                                        user + "\'").get()
            if(existing_user):
                user_error = "There already is a user with that name."
                self.render("signup.html",
                            user_error=user_error,
                            email=email)
                return
            else:
                # Signing up
                salt = make_salt()
                password = make_pw_hash(THE_SECRET, pass1, salt)
                if(email):
                    user_to_be_added = User(username=user,
                                            password=password,
                                            email=email)
                else:
                    user_to_be_added = User(username=user,
                                            password=password)
                db.put(user_to_be_added)
                self.login(user)

        # Initialising / setting error messages
        if user_ok:
            user_error = ""
        else:
            user_error = user_err_string
            user = ""

        if pass_ok:
            if pass2_ok:
                pass2_error = ""
            else:
                pass2_error = pass2_err_string
            pass_error = ""
        else:
            pass_error = pass_err_string
            pass2_error = ""

        if email_ok:
            email_error = ""
        else:
            email_error = email_err_string
            email = ""

        self.render("signup.html",
                    user_error=user_error,
                    pass_error=pass_error,
                    pass2_error=pass2_error,
                    email_error=email_error,
                    user=user,
                    email=email)


# Log in handler, shows a form if the user is not logged in
class LoginHandler(BlogHandler):
    def get(self):
        if(self.isLogged()):
            self.render("error.html",
                        error="You are already logged in!")
        else:
            self.render("login.html")

    def post(self):
        user = self.request.get("username")
        password = self.request.get("password")

        # Checking if both fields are not empty
        if user and password:

            # Checking if the username and password match
            db_users = db.GqlQuery("SELECT * FROM User WHERE username=\'" + user + "\'")
            if(db_users.get()):
                db_user = db_users[0]
                if valid_pw(THE_SECRET, password, db_user.password):
                    self.login(user)
                else:
                    self.render("login.html",
                                user=user,
                                error="Username and password do not match.")
            else:  # If the user does not exist.
                self.render("login.html",
                            user=user,
                            error="Username and password do not match.")
        else:
            self.render("login.html",
                        user=user,
                        error="A username and password are required.")


class WelcomeHandler(BlogHandler):
    def get(self):
        username = self.isLogged()
        if username:
            self.render("welcome.html",
                        isLogged=True,
                        username=username)
        else:
            self.redirect("/signup")


class PostHandler(BlogHandler):
    def get(self, id):
        article = Article.get_by_id(int(id))
        comments = db.GqlQuery("SELECT * FROM Comment WHERE article_id=" +
                               str(int(id)) + " ORDER BY created DESC")
        self.render("post.html",
                    isLogged=self.isLogged(),
                    article=article,
                    comments=comments)


class EditPost(BlogHandler):
    def get(self, id):
        key = db.Key.from_path('Article',
                               int(id),
                               parent=blog_key())
        post_tool = db.get(key)
        self.render("editpost.html",
                    post_tool=post_tool,
                    subject=post_tool.subject,
                    content=post_tool.content,
                    id=id)

    def post(self, id):
        key = db.Key.from_path('Article',
                               int(id),
                               parent=blog_key())
        post_tool = db.get(key)

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            key = db.Key.from_path('Article',
                                   int(id),
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
                        id=id,
                        error=error)


class Delete(BlogHandler):
    def post(self, id):
        key = db.Key.from_path('Article',
                               int(id),
                               parent=blog_key())
        db.delete(key)
        self.redirect('/success')


class Success(BlogHandler):
    def get(self):
        self.render('success.html')


class NewPost(BlogHandler):
    def get(self):
        isLogged = self.isLogged()
        if self.isLogged():
            self.render("newpost.html",
                        isLogged=isLogged)
        else:
            self.redirect("/signup")

    def post(self):
        title = self.request.get('subject')
        content = self.request.get('content')
        username = self.isLogged()

        if title and content:
            if username:
                a = Article(title=title,
                            content=content,
                            user=username)
                a.put()
                self.redirect("/posts/" + str(a.key().id()))
            else:
                self.redirect("/signup")

        else:
            error = "subject and content, please!"
            self.render("newpost.html",
                        isLogged=True,
                        title=title,
                        content=content,
                        error=error)


class LikePost(BlogHandler):
    def post(self, id):
        key = db.Key.from_path('Article',
                               int(id),
                               parent=blog_key())
        post_tool = db.get(key)
        post_tool.likes += 1
        post_tool.put()
        time.sleep(.1)
        self.redirect('/')


class AddCommentHandler(BlogHandler):

    def get(self, id):
        self.render("addcomment.html")

    def post(self, id):
        comment_content = self.request.get('comment_content')

        key = db.Key.from_path('Article',
                               int(id),
                               parent=blog_key())

        c = Comment(parent=key,
                    comment_content=comment_content)
        c.put()

        self.redirect('/' + id)


class DeleteCommentHandler(BlogHandler):
    def post(self, id):
        postKey = db.Key.from_path('Article',
                                   int(id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        comment = db.get(key)
        comment.delete()

        self.redirect('/' + id)


class EditCommentHandler(BlogHandler):
    def get(self, id):
        postKey = db.Key.from_path('Article',
                                   int(id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        post_tool = db.get(key)

        self.render("editcomment.html",
                    post_tool=post_tool,
                    comment_content=post_tool.comment_content,
                    id=id)

    def post(self, id):
        comment_content = self.request.get('comment_content')
        postKey = db.Key.from_path('Article',
                                   int(id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        post_tool = db.get(key)
        post_tool.comment_content = comment_content

        post_tool.put()

        self.redirect('/' + id)


app = webapp2.WSGIApplication([('/', MainPage),
                               ("/signup", SignUpHandler),
                               ("/login", LoginHandler),
                               ("/welcome", WelcomeHandler),
                               ('/posts/([0-9]+)', PostHandler),
                               ('/newpost', NewPost),
                               ('/editpost/([0-9]+)', EditPost),
                               ('/delete/([0-9]+)', Delete),
                               ('/like/([0-9]+)', LikePost),
                               ('/success', Success),
                               ('/([0-9]+)/addcomment/([0-9]+)',
                                AddCommentHandler),
                               ('/comment/delete/([0-9]+)/([0-9]+)',
                                DeleteCommentHandler),
                               ('/comment/edit/([0-9]+)/([0-9]+)',
                                EditCommentHandler),
                               ],
                              debug=True)
