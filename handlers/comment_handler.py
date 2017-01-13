from file_helpers import *
from blog_handler import BlogHandler


class CommentHandler(BlogHandler):
    """
    Handler that handles existing comments.
    """
    def get(self, id, com_id):
        isLoggedIn = self.isLoggedIn()
        article = Article.get_by_id(int(id))
        comment = Comment.get_by_id(int(com_id))
        if comment is None:
            self.redirect('/')
        else:
            self.render("comment.html",
                        isLoggedIn=isLoggedIn,
                        article=article,
                        comment=comment)
