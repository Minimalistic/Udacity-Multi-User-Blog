from google.appengine.ext import db
from bloghandler import BlogHandler

class BlogFront(BlogHandler):
    def get(self):
        allposts = db.GqlQuery  \
        ("SELECT * FROM PostDatabase ORDER BY created DESC LIMIT 10")
        self.render('blog.html',    # takes the allposts db query and
                    allposts = allposts) # renders results
