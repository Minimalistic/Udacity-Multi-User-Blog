import webapp2


from file_helpers import *

class BlogHandler(webapp2.RequestHandler):
    """
    BlogHandler class for functions for rendering templates.
    """
    def isLoggedIn(self):
        cookie = self.request.cookies.get('username')
        if cookie and check_secure_val(cookie):
            return cookie.split("|")[0]

    def write(self, *a, **kw):
        """
         Displays respective function, etc.
         """
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        """
        Calls 'render_str' and 'write' to display the jinja template.
        """

    def login(self, user):
        """
        Sets the cookie for login and redirects to welcome page.
        """
        val = make_secure_val(str(user))
        self.response.headers.add_header("Set-Cookie",
                                         r"username=%s; Path=/" % val)
        self.render("/message.html", message="Logged in successfully.")
