import webapp2

from models import *
from handlers import *

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostLinkHandler),
                               ('/blog/newpost', NewPost),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               ('/blog/delete/([0-9]+)', Delete),
                               ('/blog/like/([0-9]+)', LikePost),
                               ('/success', Success),
                               ('/blog/([0-9]+)/addcomment/([0-9]+)', AddCommentHandler),
                               ('/comment/delete/([0-9]+)/([0-9]+)', DeleteCommentHandler),
                               ('/comment/edit/([0-9]+)/([0-9]+)', EditCommentHandler),
                               ],
                              debug=True)
