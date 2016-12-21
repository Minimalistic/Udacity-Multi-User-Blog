import webapp2
import time

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
                               ('/blog/newcomment/([0-9]+)', NewComment)
                               ],
                              debug=True)
