import os
import re
import random
import webapp2
import jinja2
import hashlib
import string
import hmac
import logging

# Import google app engine datastore lib
from google.appengine.ext import db

# Sets the location of the templates folder that are contained in the home
# directory of this app.
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Envokes jinja2 environment, points it to the templates folder with the
# user input markup automatically escaped.
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


# Signups check
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
    """
    Instantiates a class to store user data in the datastore
    made up of user attributes.
    """
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)

# Create a database for blog post information


class Article(db.Model):
    """
    Instantiates a class to store articles/post data in the datastore
    made up of post attributes.
    """
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    edited = db.DateTimeProperty(auto_now=True)
    user = db.StringProperty(required=True)
    likes = db.IntegerProperty(default=0)

# Create a database for comment information


class Comment(db.Model):
    """
    Instantiates a class to store comments data in the datastore.
    """
    article_id = db.IntegerProperty(required=True)
    user = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)


class Like(db.Model):
    """
    Manages the likes for individual posts.
    """
    article_id = db.IntegerProperty(required=True)
    user = db.StringProperty(required=True)


# HANDLERS ###################################################################


class BlogHandler(webapp2.RequestHandler):
    """
    BlogHandler class for functions for rendering templates.
    """
    def isLogged(self):
        cookie = self.request.cookies.get('username')
        if cookie and check_secure_val(cookie):
            return cookie.split("|")[0]

    def write(self, *a, **kw):
        """
         Displays respective function, etc.
         """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        """
        Calls 'render_str' and 'write' to display the jinja template.
        """

    def login(self, user):
        """
        Sets the cookie for login and redirects to welcome page.
        """
        val = make_secure_val(str(user))
        self.response.headers.add_header("Set-Cookie",
                                         r"username=%s; Path=/" % val)
        self.render("/message.html", message="Logged in successfully.")


class MainPage(BlogHandler):
    """
    Handler for the main page of the blog
    """
    def get(self):
        """
        Queries the articles database for the 10 most recent blog posts
        and then orders them descending.
        """
        articles = db.GqlQuery("SELECT * "
                               "FROM Article "
                               "ORDER BY created "
                               "DESC LIMIT 10")
        isLogged = self.isLogged()
        self.render("blog.html",        # takes the articles db query and
                    isLogged=isLogged,  # renders results
                    articles=articles)


# SignUpHandler shows a sign up form if user is not logged in
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
            self.render("message.html",
                        error="You are already logged in!")
        else:
            self.render("login.html")

    def post(self):
        user = self.request.get("username")
        password = self.request.get("password")

        # Checking if both fields are not empty
        if user and password:

            # Checking if the username and password match
            db_users = db.GqlQuery("SELECT * FROM User WHERE username=\'" +
                                   user + "\'")
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


class LogoutHandler(BlogHandler):
    def get(self):
        if self.isLogged():
            self.response.headers.add_header("Set-Cookie", "username=; Path=/")
            self.render("message.html", message="Logged out successfully.")
        else:
            self.render("message.html",
                        error="Can't logout when not logged in.")


class WelcomeHandler(BlogHandler):
    def get(self):
        isLogged = self.isLogged()
        if isLogged:
            self.render("message.html.html",
                        message="Logged in successfully.",
                        isLogged=isLogged)
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


class NewPostHandler(BlogHandler):
    """
    This handler is for posting new blog articles to the blog.
    """
    def get(self):
        """
        Uses a 'get' request to render the newpost.html by caling render
        from 'BlogHandler'
        """
        isLogged = self.isLogged()
        if self.isLogged():
            self.render("newpost.html",
                        isLogged=isLogged)
        else:
            self.redirect("/signup")

    def post(self):
        """
        Handles the 'post' request that originates from newpost.html
        """
        title = self.request.get('subject')
        content = self.request.get('content')
        username = self.isLogged()

        if title and content:
            if username:
                a = Article(title=title,
                            content=content,
                            user=username)
                a.put()
                # Once article has been stored, redirects user to the post.
                self.redirect("/posts/" + str(a.key().id()))
            else:
                self.redirect("/signup")

        else:
            isLogged = self.isLogged()
            error = "Subject and content, please!"
            self.render("newpost.html",
                        isLogged=isLogged,
                        title=title,
                        content=content,
                        error=error)


class EditPostHandler(BlogHandler):
    def get(self, id):
        title = self.request.get("title")
        article = Article.get_by_id(int(id))
        isLogged = self.isLogged()
        if article.user == isLogged:
            self.render("editpost.html",
                        isLogged=isLogged,
                        title=title,
                        article=article,
                        id=id)
        else:
            self.write("You do not have authorization to edit this post.")

    def post(self, id):
        title = self.request.get("title")
        content = self.request.get('content')
        isLogged = self.isLogged()
        article = Article.get_by_id(int(id))

        if title and content:
            article.title = title
            article.content = content
            article.put()
            self.render("message.html", message="Post edited successfully.")

        else:  # In case user tries to submit an empty edit form
            error = "There must be a title and content."
            self.render("editpost.html",
                        isLogged=isLogged,
                        article=article,
                        title=title,
                        content=content,
                        id=id,
                        error=error)


class DeletePostHandler(BlogHandler):
    def post(self, id):
        article = Article.get_by_id(int(id))
        isLogged = self.isLogged()
        if (isLogged and article.user == isLogged):
            article.delete()
            self.render('message.html',
                        message="Post deletion successful.",
                        isLogged=isLogged)
        else:
            self.render("message.html",
                        error="That's not permitted")


class LikePostHandler(BlogHandler):
    def get(self, id):
        username = self.isLogged()
        article = Article.get_by_id(int(id))
        if username:
            if not article.user == username:
                like = db.GqlQuery("SELECT * FROM Like WHERE article_id=" +
                                   str(id) + " AND user=\'" + username + "\'")
                if(like.get()):
                    like[0].delete()
                    article.likes = article.likes - 1
                    article.put()
                    self.redirect("/posts/" + id)
                else:
                    like = Like(article_id=int(id),
                                user=username)
                    like.put()
                    article.likes = article.likes + 1
                    article.put()
                    self.redirect("/posts/" + id)
            else:
                self.render("message.html",
                            error="Can't like your own posts.")
        else:
            self.redirect("/signup")

    def post(self, id):
        title = self.request.get("subject")
        content = self.request.get("content")
        username = self.isLogged()
        article = Article.get_by_id(int(id))
        if title and content:
            if username:
                if article.user == username:
                    article.title = title
                    article.content = content
                    article.put()
                    self.redirect("/posts/" + id)
                else:
                    self.render("message.html",
                                error="You do not have acces to this action!")
            else:
                self.redirect("/signup")
        else:
            error = "We need both a title and some content!"
            self.render("editpost.html",
                        title=title,
                        content=content,
                        error=error)


class CommentHandler(BlogHandler):
    def get(self, id, com_id):
        isLogged = self.isLogged()
        article = Article.get_by_id(int(id))
        comment = Comment.get_by_id(int(com_id))

        self.render("comment.html",
                    isLogged=isLogged,
                    article=article,
                    comment=comment)


class AddCommentHandler(BlogHandler):
    """
    Handler class for displaying a new comment form to an article post.
    """
    def get(self, id):
        article = Article.get_by_id(int(id))
        isLogged = self.isLogged()
        if self.isLogged():
            self.render("addcomment.html",
                        isLogged=isLogged,
                        article=article)

    def post(self, id):
        """
        Handles the 'post' request that comes from 'addcomment.html'
        """
        content = self.request.get("content")
        username = self.isLogged()
        if content:
            if self.isLogged():
                comment = Comment(content=content,
                                  user=username,
                                  article_id=int(id))
                comment.put()
                self.render("message.html",
                            message="Your comment has been posted!")
        else:
            isLogged = self.isLogged()
            error = "You need to write something."
            self.render("addcomment.html",
                        isLogged=isLogged,
                        content=content,
                        error=error)


class DeleteCommentHandler(BlogHandler):
    """
    Handles the deletion of comments.
    """
    def post(self, com_id):
        isLogged = self.isLogged()
        comment = Comment.get_by_id(int(com_id))
        if isLogged == comment.user:
            comment.delete()
            self.render('message.html',
                        message="Comment deleted successfully.",
                        isLogged=isLogged)


class EditCommentHandler(BlogHandler):
    """
    Handles the editing of existing comments.
    """
    def get(self, com_id):
        isLogged = self.isLogged()
        comment = Comment.get_by_id(int(com_id))
        self.render("editcomment.html",
                    isLogged=isLogged,
                    comment=comment)

    def post(self, com_id):
        isLogged = self.isLogged()
        content = self.request.get("content")
        comment = Comment.get_by_id(int(com_id))
        comment.content = content
        if isLogged == comment.user:
            comment.put()
            self.render('message.html',
                        message="Comment edited successfully.",
                        isLogged=isLogged)


# GoogleAppEngine app variable
# This sets the attributes of individual HTML files that will be served
# using Google App Engine.


app = webapp2.WSGIApplication([('/', MainPage),
                               ("/signup", SignUpHandler),
                               ("/login", LoginHandler),
                               ("/logout", LogoutHandler),
                               ("/welcome", WelcomeHandler),
                               ('/posts/([0-9]+)', PostHandler),
                               ('/newpost', NewPostHandler),
                               ('/editpost/([0-9]+)', EditPostHandler),
                               ('/delete/([0-9]+)', DeletePostHandler),
                               ('/like/([0-9]+)', LikePostHandler),
                               ('/comment/([0-9]+)/([0-9]+)', CommentHandler),
                               ('/posts/([0-9]+)/addcomment',
                                AddCommentHandler),
                               ('/comment/delete/([0-9]+)',
                                DeleteCommentHandler),
                               ('/comment/edit/([0-9]+)',
                                EditCommentHandler),
                               ],
                              debug=True)
