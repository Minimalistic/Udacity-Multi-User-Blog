import webapp2

from file_helpers import *
from handlers.blog_handler import BlogHandler
from handlers.post_handler import PostHandler
from handlers.mainpage_handler import MainPage
from handlers.comment_handler import CommentHandler
from handlers.editcomment_handler import EditCommentHandler

from models import *

# Import google app engine datastore lib
from google.appengine.ext import db


# SignUpHandler shows a sign up form if user is not logged in
class SignUpHandler(BlogHandler):
    def get(self):
        if(self.isLoggedIn()):
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


# Log in handler, shows a form if the user is not logged in
class LoginHandler(BlogHandler):
    def get(self):
        if(self.isLoggedIn()):
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
        if self.isLoggedIn():
            self.response.headers.add_header("Set-Cookie",
                                             "username=; Path=/")
            self.render("message.html",
                        message="Logged out successfully.")
        else:
            self.redirect("/login")


class WelcomeHandler(BlogHandler):
    def get(self):
        isLoggedIn = self.isLoggedIn()
        if isLoggedIn:
            self.render("message.html",
                        message="Logged in successfully.",
                        isLoggedIn=isLoggedIn)
        else:
            self.redirect("/login")


class NewPostHandler(BlogHandler):
    """
    This handler is for posting new blog articles to the blog.
    """
    def get(self):
        """
        Uses a 'get' request to render the newpost.html by caling render
        from 'BlogHandler'
        """
        isLoggedIn = self.isLoggedIn()
        if self.isLoggedIn():
            self.render("newpost.html",
                        isLoggedIn=isLoggedIn)
        else:
            self.redirect("/login")

    def post(self):
        """
        Handles the 'post' request that originates from newpost.html
        """
        title = self.request.get('subject')
        content = self.request.get('content')
        username = self.isLoggedIn()

        if username:
            if title and content:
                a = Article(title=title,
                            content=content,
                            user=username)
                a.put()
                # Once article has been stored, redirects user to the post.
                self.redirect("/posts/" + str(a.key().id()))

            else:
                isLoggedIn = self.isLoggedIn()
                error = "Subject and content, please!"
                self.render("newpost.html",
                            isLoggedIn=isLoggedIn,
                            title=title,
                            content=content,
                            error=error)
        else:
            self.redirect("/login")


class EditPostHandler(BlogHandler):
    def get(self, id):
        title = self.request.get("title")
        article = Article.get_by_id(int(id))
        isLoggedIn = self.isLoggedIn()

        if article is None:
            self.redirect('/')
        else:
            if article.user == isLoggedIn:
                self.render("editpost.html",
                            isLoggedIn=isLoggedIn,
                            title=title,
                            article=article,
                            id=id)
            else:
                self.redirect("/login")

    def post(self, id):
        title = self.request.get("title")
        content = self.request.get('content')
        isLoggedIn = self.isLoggedIn()
        article = Article.get_by_id(int(id))

        if article is None:
            self.redirect('/')
        else:
            if article.user == isLoggedIn:
                if title and content:
                    article.title = title
                    article.content = content
                    article.put()
                    self.render("message.html",
                                message="Post edited successfully.")

                else:  # In case user tries to submit an empty edit form
                    error = "There must be a title and content."
                    self.render("editpost.html",
                                isLoggedIn=isLoggedIn,
                                article=article,
                                title=title,
                                content=content,
                                id=id,
                                error=error)
            else:
                self.redirect("/login")


class DeletePostHandler(BlogHandler):
    def post(self, id):
        article = Article.get_by_id(int(id))
        isLoggedIn = self.isLoggedIn()

        if article is None:
            self.redirect('/')
        else:
            if isLoggedIn:
                if (isLoggedIn and article.user == isLoggedIn):
                    article.delete()
                    self.render('message.html',
                                message="Post deletion successful.",
                                isLoggedIn=isLoggedIn)
                else:
                    self.render("message.html",
                                error="That's not permitted")
            else:
                self.redirect("/login")


class LikePostHandler(BlogHandler):
    def get(self, id):
        username = self.isLoggedIn()
        article = Article.get_by_id(int(id))

        if article is None:
            self.redirect('/')
        else:
            if username:
                if not article.user == username:
                    like = db.GqlQuery("SELECT * FROM Like WHERE article_id="
                            + str(id) + " AND user=\'" + username + "\'")
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
                self.redirect("/login")

    def post(self, id):
        title = self.request.get("subject")
        content = self.request.get("content")
        username = self.isLoggedIn()
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
                self.redirect("/login")
        else:
            error = "We need both a title and some content!"
            self.render("editpost.html",
                        title=title,
                        content=content,
                        error=error)


class AddCommentHandler(BlogHandler):
    """
    Handler class for displaying a new comment form to an article post.
    """
    def get(self, id):
        article = Article.get_by_id(int(id))
        isLoggedIn = self.isLoggedIn()
        if article is None:
            self.redirect('/')
        else:
            if self.isLoggedIn():
                self.render("addcomment.html",
                            isLoggedIn=isLoggedIn,
                            article=article)
            else:
                self.redirect("/login")

    def post(self, id):
        """
        Handles the 'post' request that comes from 'addcomment.html'
        """
        content = self.request.get("content")
        username = self.isLoggedIn()
        article = Article.get_by_id(int(id))
        if article is None:
            self.redirect('/')
        else:
            if self.isLoggedIn():
                if content:
                    comment = Comment(content=content,
                                      user=username,
                                      article_id=int(id))
                    comment.put()
                    self.render("message.html",
                                message="Your comment has been posted!")
                else:
                    isLoggedIn = self.isLoggedIn()
                    error = "You need to write something."
                    self.render("addcomment.html",
                                isLoggedIn=isLoggedIn,
                                content=content,
                                error=error)
            else:
                self.redirect("/login")


class DeleteCommentHandler(BlogHandler):
    """
    Handles the deletion of comments.
    """
    def post(self, com_id):
        isLoggedIn = self.isLoggedIn()
        comment = Comment.get_by_id(int(com_id))
        if comment is None:
            self.redirect('/')
        else:
            if isLoggedIn == comment.user:
                comment.delete()
                self.render('message.html',
                            message="Comment deleted successfully.",
                            isLoggedIn=isLoggedIn)
            else:
                self.redirect("/login")


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
