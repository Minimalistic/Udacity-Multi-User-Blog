from file_helpers import *
from blog_handler import BlogHandler

class MainPage(BlogHandler):
    """
    Handler for the main page of the blog
    """
    def get(self):
        """
        Queries the articles database for the 10 most recent blog posts
        and then orders them descending.
        """
        articles = db.GqlQuery("SELECT * "
                               "FROM Article "
                               "ORDER BY created "
                               "DESC LIMIT 10")
        isLoggedIn = self.isLoggedIn()
        self.render("blog.html",        # takes the articles db query and
                    isLoggedIn=isLoggedIn,  # renders results
                    articles=articles)
