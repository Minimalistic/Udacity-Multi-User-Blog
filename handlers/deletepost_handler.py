from file_helpers import *
from blog_handler import BlogHandler


class DeletePostHandler(BlogHandler):
    def post(self, id):
        article = Article.get_by_id(int(id))
        isLoggedIn = self.isLoggedIn()

        if article is None:
            self.redirect('/')
        else:
            if isLoggedIn:
                if (isLoggedIn and article.user == isLoggedIn):
                    article.delete()
                    self.render('message.html',
                                message="Post deletion successful.",
                                isLoggedIn=isLoggedIn)
                else:
                    self.render("message.html",
                                error="That's not permitted")
            else:
                self.redirect("/login")
