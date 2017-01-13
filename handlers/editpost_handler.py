from file_helpers import *
from blog_handler import BlogHandler


class EditPostHandler(BlogHandler):
    def get(self, id):
        title = self.request.get("title")
        article = Article.get_by_id(int(id))
        isLoggedIn = self.isLoggedIn()

        if article is None:
            self.redirect('/')
        else:
            if article.user == isLoggedIn:
                self.render("editpost.html",
                            isLoggedIn=isLoggedIn,
                            title=title,
                            article=article,
                            id=id)
            else:
                self.redirect("/login")

    def post(self, id):
        title = self.request.get("title")
        content = self.request.get('content')
        isLoggedIn = self.isLoggedIn()
        article = Article.get_by_id(int(id))

        if article is None:
            self.redirect('/')
        else:
            if article.user == isLoggedIn:
                if title and content:
                    article.title = title
                    article.content = content
                    article.put()
                    self.render("message.html",
                                message="Post edited successfully.")

                else:  # In case user tries to submit an empty edit form
                    error = "There must be a title and content."
                    self.render("editpost.html",
                                isLoggedIn=isLoggedIn,
                                article=article,
                                title=title,
                                content=content,
                                id=id,
                                error=error)
            else:
                self.redirect("/login")