
import os
import jinja2

import webapp2
import time


from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

# FILE LEVEL FUNCTIONS


def blog_key(name='default'):
    """
    This is the key that defines a single blog and facilitiate multiple
    blogs on the same site.
    """
    return db.Key.from_path('blogs', name)


class PostDatabase(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    likes = db.IntegerProperty(required=False)

    def render(self):  # renderpost is used to render jinja templates
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", renderpost=self)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class Comment(db.Model):
    comment_content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def render_post(response, post_tool):
        response.out.write('<b>' + post_tool.subject + '</b><br>')
        response.out.write(post_tool.content)


class MainPage(BlogHandler):  # This renders the base.html if user goes to
    def get(self):            # the root address
        self.render('base.html')


class BlogFront(BlogHandler):
    def get(self):
        allposts = db.GqlQuery("SELECT * "
                               "FROM PostDatabase "
                               "ORDER BY created "
                               "DESC LIMIT 10")
        self.render('blog.html',        # takes the allposts db query and
                    allposts=allposts)  # renders results


class PostLinkHandler(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)

        comments = db.GqlQuery ("SELECT * "
                                "FROM Comment WHERE "
                                "ancestor is :1 "
                                "order by created "
                                "desc limit 3", key)

        if not post_tool:
            self.error(404)
            return

        self.render("permalink.html",
                    post_tool=post_tool, comments=comments)


class EditPost(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)
        self.render("editpost.html",
                    post_tool=post_tool,
                    subject=post_tool.subject,
                    content=post_tool.content,
                    post_id=post_id)

    def post(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            key = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
            post_tool = db.get(key)
            post_tool.subject = subject
            post_tool.content = content

            post_tool.put()

            self.redirect('/blog/%s' % str(post_tool.key().id()))

        else:  # In case user tries to submit an empty edit form
            error = "There must be a subject and content."
            self.render("editpost.html",
                        post_tool=post_tool,
                        subject=post_tool.subject,
                        content=post_tool.content,
                        post_id=post_id,
                        error=error)


class Delete(BlogHandler):
    def post(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        db.delete(key)
        self.redirect('/success')


class Success(BlogHandler):
    def get(self):
        self.render('success.html')


class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post_tool = PostDatabase(parent=blog_key(),
                                     subject=subject,
                                     content=content,
                                     likes=0)
            post_tool.put()
            self.redirect('/blog/%s' % str(post_tool.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html",
                        subject=subject,
                        content=content,
                        error=error)


class LikePost(BlogHandler):
    def post(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)
        post_tool.likes += 1
        post_tool.put()
        time.sleep(.1)
        self.redirect('/blog')


class AddCommentHandler(BlogHandler):

    def get(self, post_id):
        self.render("addcomment.html")

    def post(self, post_id):
        comment_content = self.request.get('comment_content')

        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())

        c = Comment(parent=key,
                    comment_content=comment_content)
        c.put()

        self.redirect('/blog/' + post_id)


class DeleteCommentHandler(BlogHandler):
    def post(self, post_id):
        postKey = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        comment = db.get(key)
        comment.delete()

        self.redirect('/blog/' + post_id)


class EditCommentHandler(BlogHandler):
    def get(self, post_id):
        postKey = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        post_tool = db.get(key)

        self.render("editcomment.html",
                    post_tool=post_tool,
                    comment_content=post_tool.comment_content,
                    post_id=post_id)
        
    def post(self, post_id):
        comment_content = self.request.get('comment_content')
        postKey = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
        key = db.Key.from_path('Comment',
                               parent=postKey)
        post_tool = db.get(key)
        post_tool.comment_content = comment_content

        post_tool.put()

        self.redirect('/blog/' + post_id)
