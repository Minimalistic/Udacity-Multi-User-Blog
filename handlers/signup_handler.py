from file_helpers import *
from blog_handler import BlogHandler


# SignUpHandler shows a sign up form if user is not logged in
class SignUpHandler(BlogHandler):
    def get(self):
        if(self.isLoggedIn()):
            self.redirect("/")
        else:
            self.render("signup.html",
                        user_error="",
                        pass_error="",
                        pass2_error="",
                        email_error="")

    def post(self):
        user = self.request.get("username")
        pass1 = self.request.get("password")
        pass2 = self.request.get("verify")
        email = self.request.get("email")

        # Checking every field
        user_ok = checkUser(user)
        pass_ok = checkPass(pass1)
        pass2_ok = checkPass2(pass1, pass2)
        email_ok = checkEmail(email)

        # Checking if all fields are ok
        if(user_ok and pass_ok and pass2_ok and email_ok):

            # Checking if the user already exists
            existing_user = db.GqlQuery("""SELECT * FROM User
                                        WHERE username=\'""" +
                                        user + "\'").get()
            if(existing_user):
                user_error = "There already is a user with that name."
                self.render("signup.html",
                            user_error=user_error,
                            email=email)
                return
            else:
                # Signing up
                salt = make_salt()
                password = make_pw_hash(THE_SECRET, pass1, salt)
                if(email):
                    user_to_be_added = User(username=user,
                                            password=password,
                                            email=email)
                else:
                    user_to_be_added = User(username=user,
                                            password=password)
                db.put(user_to_be_added)
                self.login(user)

