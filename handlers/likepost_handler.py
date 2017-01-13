from file_helpers import *
from blog_handler import BlogHandler


class LikePostHandler(BlogHandler):
    """
    Handler class for liking a post.
    """
    def get(self, id):
        username = self.isLoggedIn()
        article = Article.get_by_id(int(id))

        if article is None:
            self.redirect('/')
        else:
            if username:
                if not article.user == username:
                    like = db.GqlQuery("SELECT * FROM Like WHERE article_id="
                            + str(id) + " AND user=\'" + username + "\'")
                    if(like.get()):
                        like[0].delete()
                        article.likes = article.likes - 1
                        article.put()
                        self.redirect("/posts/" + id)
                    else:
                        like = Like(article_id=int(id),
                                    user=username)
                        like.put()
                        article.likes = article.likes + 1
                        article.put()
                        self.redirect("/posts/" + id)
                else:
                    self.render("message.html",
                                error="Can't like your own posts.")
            else:
                self.redirect("/login")

    def post(self, id):
        title = self.request.get("subject")
        content = self.request.get("content")
        username = self.isLoggedIn()
        article = Article.get_by_id(int(id))
        if title and content:
            if username:
                if article.user == username:
                    article.title = title
                    article.content = content
                    article.put()
                    self.redirect("/posts/" + id)
                else:
                    self.render("message.html",
                                error="You do not have acces to this action!")
            else:
                self.redirect("/login")
        else:
            error = "We need both a title and some content!"
            self.render("editpost.html",
                        title=title,
                        content=content,
                        error=error)
