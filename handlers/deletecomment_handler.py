from file_helpers import *
from blog_handler import BlogHandler


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
