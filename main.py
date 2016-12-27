import webapp2

from models import *
from handlers import *

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               ('/blog/delete/([0-9]+)', Delete),
                               ('/success', Success),
                               ('/signup', Register),
                               ('/login', Login),
                               ('/logout', Logout),
                               ('/blog/like/([0-9]+)', LikePost),
                               ('/welcome', WelcomeUser),
                               ('/blog/([0-9]+)/addcomment/([0-9]+)', AddCommentHandler),
                               ('/blog/editcomment/([0-9]+)', EditCommentHandler),
                               ('/blog/deletecomment/([0-9]+)/([0-9]+)', DeleteCommentHandler)
                               ],
                              debug=True)
