from file_helpers import *
from blog_handler import BlogHandler


class LogoutHandler(BlogHandler):
    def get(self):
        if self.isLoggedIn():
            self.response.headers.add_header("Set-Cookie",
                                             "username=; Path=/")
            self.render("message.html",
                        message="Logged out successfully.")
        else:
            self.redirect("/login")
