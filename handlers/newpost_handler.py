from file_helpers import *
from blog_handler import BlogHandler


class NewPostHandler(BlogHandler):
    """
    This handler is for posting new blog articles to the blog.
    """
    def get(self):
        """
        Uses a 'get' request to render the newpost.html by caling render
        from 'BlogHandler'
        """
        isLoggedIn = self.isLoggedIn()
        if self.isLoggedIn():
            self.render("newpost.html",
                        isLoggedIn=isLoggedIn)
        else:
            self.redirect("/login")

    def post(self):
        """
        Handles the 'post' request that originates from newpost.html
        """
        title = self.request.get('subject')
        content = self.request.get('content')
        username = self.isLoggedIn()

        if username:
            if title and content:
                a = Article(title=title,
                            content=content,
                            user=username)
                a.put()
                # Once article has been stored, redirects user to the post.
                self.redirect("/posts/" + str(a.key().id()))

            else:
                isLoggedIn = self.isLoggedIn()
                error = "Subject and content, please!"
                self.render("newpost.html",
                            isLoggedIn=isLoggedIn,
                            title=title,
                            content=content,
                            error=error)
        else:
            self.redirect("/login")