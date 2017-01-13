import webapp2

from file_helpers import *

from handlers.blog_handler import BlogHandler
from handlers.mainpage_handler import MainPage
from handlers.post_handler import PostHandler
from handlers.comment_handler import CommentHandler
from handlers.editcomment_handler import EditCommentHandler
from handlers.signup_handler import SignUpHandler
from handlers.deletecomment_handler import DeleteCommentHandler
from handlers.newpost_handler import NewPostHandler
from handlers.addcomment_handler import AddCommentHandler
from handlers.login_handler import LoginHandler
from handlers.logout_handler import LogoutHandler
from handlers.editpost_handler import EditPostHandler
from handlers.deletepost_handler import DeletePostHandler

from models import *

# Import google app engine datastore lib
from google.appengine.ext import db


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


# GoogleAppEngine app variable
# This sets the attributes of individual HTML files that will be served
# using Google App Engine.


app = webapp2.WSGIApplication([('/', MainPage),
                               ("/signup", SignUpHandler),
                               ("/login", LoginHandler),
                               ("/logout", LogoutHandler),
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
