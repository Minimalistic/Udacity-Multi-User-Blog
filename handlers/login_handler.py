from file_helpers import *
from blog_handler import BlogHandler

# Log in handler, shows a form if the user is not logged in


class LoginHandler(BlogHandler):
    """
    Handler that manages users logging in.
    """
    def get(self):
        if(self.isLoggedIn()):
            self.render("message.html",
                        error="You are already logged in!")
        else:
            self.render("login.html")

    def post(self):
        user = self.request.get("username")
        password = self.request.get("password")

        # Checking if both fields are not empty
        if user and password:

            # Checking if the username and password match
            db_users = db.GqlQuery("SELECT * FROM User WHERE username=\'" +
                                   user + "\'")
            if(db_users.get()):
                db_user = db_users[0]
                if valid_pw(THE_SECRET, password, db_user.password):
                    self.login(user)
                else:
                    self.render("login.html",
                                user=user,
                                error="Username and password do not match.")
            else:  # If the user does not exist.
                self.render("login.html",
                            user=user,
                            error="Username and password do not match.")
        else:
            self.render("login.html",
                        user=user,
                        error="A username and password are required.")

