from file_helpers import *
from blog_handler import BlogHandler

from decorators import post_exists


class PostHandler(BlogHandler):
    """
    Handler that manages existing posts.
    """
    @post_exists
    def get(self, id):
        comments = db.GqlQuery("SELECT * FROM Comment WHERE article_id=" +
                               str(int(id)) + " ORDER BY created DESC")
        if article is None:
            self.redirect('/')
        else:
            self.render("post.html",
                        isLoggedIn=self.isLoggedIn(),
                        article=article,
                        comments=comments)
