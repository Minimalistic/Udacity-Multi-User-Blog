import jinja2

from helpyHelper import *
from userModel import User
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class PostDatabase(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    last_modified = db.DateTimeProperty(auto_now = True)
    user_id = db.IntegerProperty(required = True)

    def fetchUserName(self):
        user = User.by_id(self.user_id)
        return user.name

    def render(self): # renderpost is used to render jinja templates
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", renderpost = self)

class Comment(db.Model):
    comment = db.StringProperty(required=True)
    post = db.ReferenceProperty(PostDatabase)
    user = db.ReferenceProperty(User)
