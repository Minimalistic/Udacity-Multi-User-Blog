from blog_handler import BlogHandler


class LogoutHandler(BlogHandler):
    """
    Handler that manaages users logging out.
    """
    def get(self):
        if self.isLoggedIn():
            self.response.headers.add_header("Set-Cookie",
                                             "username=; Path=/")
            self.render("message.html",
                        message="Logged out successfully.")
        else:
            self.redirect("/login")
