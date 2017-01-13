from file_helpers import *
from blog_handler import BlogHandler

class EditCommentHandler(BlogHandler):
    """
    Handles the editing of existing comments.
    """
    def get(self, com_id):
        isLoggedIn = self.isLoggedIn()
        comment = Comment.get_by_id(int(com_id))
        if comment is None:
            self.redirect('/')
        else:
            self.render("editcomment.html",
                        isLoggedIn=isLoggedIn,
                        comment=comment)

    def post(self, com_id):
        isLoggedIn = self.isLoggedIn()
        content = self.request.get("content")
        comment = Comment.get_by_id(int(com_id))
        comment.content = content
        if comment is None:
            self.redirect('/')
        else:
            if isLoggedIn == comment.user:
                comment.put()
                self.render('message.html',
                            message="Comment edited successfully.",
                            isLoggedIn=isLoggedIn)
            else:
                self.redirect("/login")

