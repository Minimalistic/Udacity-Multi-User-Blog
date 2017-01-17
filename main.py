import webapp2

from handlers.mainpage_handler import MainPage

from handlers.signup_handler import SignUpHandler
from handlers.login_handler import LoginHandler
from handlers.logout_handler import LogoutHandler

from handlers.post_handler import PostHandler
from handlers.newpost_handler import NewPostHandler
from handlers.editpost_handler import EditPostHandler
from handlers.deletepost_handler import DeletePostHandler

from handlers.comment_handler import CommentHandler
from handlers.addcomment_handler import AddCommentHandler
from handlers.editcomment_handler import EditCommentHandler
from handlers.deletecomment_handler import DeleteCommentHandler

from handlers.likepost_handler import LikePostHandler

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
