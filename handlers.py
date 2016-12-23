import webapp2
import time


from models import *
from userAuth import *


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

    def render_post(response, post_tool):
        response.out.write('<b>' + post_tool.subject + '</b><br>')
        response.out.write(post_tool.content)


def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class MainPage(BlogHandler):  # This renders the base.html if user goes to
    def get(self):            # the root address
        self.render('base.html')


class BlogFront(BlogHandler):
    def get(self):
        allposts = db.GqlQuery \
            ("SELECT * FROM PostDatabase ORDER BY created DESC LIMIT 10")
        self.render('blog.html',        # takes the allposts db query and
                    allposts=allposts)  # renders results


class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)

        comments = db.GqlQuery ("SELECT * FROM Comment WHERE ancestor is :1 order by created desc limit 3", key)

        if not post_tool:
            self.error(404)
            return

        self.render("permalink.html",
                    post_tool=post_tool, comments=comments)


class EditPost(BlogHandler):
    def get(self, post_id):
        if self.user:
            key = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
            post_tool = db.get(key)
            # Check to see if the logged in user is the post's author
            if post_tool.user_id == self.user.key().id():
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

        if self.user:
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
        if self.user:
            key = db.Key.from_path('PostDatabase',
                                   int(post_id),
                                   parent=blog_key())
            db.delete(key)
            self.redirect('/success')

        else:
            self.redirect('/blog')


class Success(BlogHandler):
    def get(self):
        self.render('success.html', username=self.user.name)


class NewPost(BlogHandler):
    def get(self):
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        if not self.user:
            self.write("You must be logged in to make a new post.")

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post_tool = PostDatabase(parent=blog_key(),
                                     user_id=self.user.key().id(),
                                     subject=subject,
                                     content=content,
                                     likes=0,
                                     liked_by=[])
            post_tool.put()
            self.redirect('/blog/%s' % str(post_tool.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html",
                        subject=subject,
                        content=content,
                        error=error)


class LikePost(BlogHandler):
    def get(self, post_id):
        if not self.user:
            self.redirect("/signup")

    def post(self, post_id):
        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())
        post_tool = db.get(key)
        user_id = post_tool.user_id
        logged_user = self.user.key().id()
        if logged_user in post_tool.liked_by:
            post_tool.likes += -1
            post_tool.liked_by.remove(logged_user)
            post_tool.put()
            time.sleep(.1)
            self.redirect('/blog')
        elif user_id != logged_user:
            post_tool.likes += 1
            post_tool.liked_by.append(logged_user)
            post_tool.put()
            time.sleep(.1)
            self.redirect('/blog')
        else:
            self.write("Can't like your own post.")

class SignUp(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')

        params = dict(username=self.username,
                      email=self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True

        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()

    def done(self, *a, **kw):
        raise NotImplementedError


class Register(SignUp):
    def done(self):
        # Make sure the user doesn't already exist
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()

            self.login(u)
            self.redirect('/welcome')


class Login(BlogHandler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/welcome')
        else:
            msg = 'Invalid login'
            self.render('login-form.html', error=msg)


class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect('/blog')


class WelcomeUser(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username=self.user.name)
        else:
            self.redirect('/signup')


class AddCommentHandler(BlogHandler):

    def get(self, post_id, user_id):
        if not self.user:
            self.render('/login')
        else:
            self.render("addcomment.html")

    def post(self, post_id, user_id):
        if not self.user:
            return
        comment_owner_text = self.user.name
        comment_content = self.request.get('comment_content')

        key = db.Key.from_path('PostDatabase',
                               int(post_id),
                               parent=blog_key())

        c = Comment(parent=key,
                    comment_owner=self.user.key().id(),
                    comment_content=comment_content,
                    comment_owner_text=comment_owner_text)
        c.put()

        self.redirect('/blog/' + post_id)


class EditCommentHandler(BlogHandler):

    def get(self, post_id, post_user_id, comment_id):
        if self.user and self.user.key().id() == int(post_user_id):
            postKey = db.Key.from_path('Post', int(post_id), parent=blog_key())
            key = db.Key.from_path('Comment', int(comment_id), parent=postKey)
            comment = db.get(key)

            self.render('editcomment.html', content=comment.content)

        elif not self.user:
            self.redirect('/login')

        else:
            self.write("You don't have permission to edit this comment.")

    def post(self, post_id, post_user_id, comment_id):
        if not self.user:
            return

        if self.user and self.user.key().id() == int(post_user_id):
            content = self.request.get('content')

            postKey = db.Key.from_path('Post', int(post_id), parent=blog_key())
            key = db.Key.from_path('Comment', int(comment_id), parent=postKey)
            comment = db.get(key)

            comment.content = content
            comment.put()

            self.redirect('/' + post_id)

        else:
            self.write("You don't have permission to edit this comment.")


class DeleteCommentHandler(BlogHandler):

    def get(self, post_id, post_user_id, comment_id):

        if self.user and self.user.key().id() == int(post_user_id):
            postKey = db.Key.from_path('Post', int(post_id), parent=blog_key())
            key = db.Key.from_path('Comment', int(comment_id), parent=postKey)
            comment = db.get(key)
            comment.delete()

            self.redirect('/' + post_id)

        elif not self.user:
            self.redirect('/login')

        else:
            self.write("You don't have permission to delete this comment.")