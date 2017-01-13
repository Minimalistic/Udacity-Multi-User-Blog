from file_helpers import *
from blog_handler import BlogHandler


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