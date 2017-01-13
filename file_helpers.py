import os
import jinja2
import hmac
import logging
import hashlib
import re

import random
import string


# Sets the location of the templates folder that are contained in the home
# directory of this app.
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
# Envokes jinja2 environment, points it to the templates folder with the
# user input markup automatically escaped.
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

# Strings
THE_SECRET = "TheSecretIs42"
user_err_string = "Not a valid username."
pass_err_string = "Not a valid password."
pass2_err_string = "Passwords do not match."
email_err_string = "Not a valid email."


def blog_key(name='default'):
    """
    This is the key that defines a single blog and facilitiate multiple
    blogs on the same site.
    """
    return db.Key.from_path('blogs', name)


# Signups check
def checkUser(user):
    user2 = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return user2.match(user)


def checkPass(pass1):
    pass2 = re.compile(r"^.{3,20}$")
    return pass2.match(pass1)


def checkPass2(pass1, pass2):
    return pass2 == pass1


def checkEmail(email):
    email2 = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    return email2.match(email) or email == ""


# Cookie related
def hash_str(s):
    return hmac.new(THE_SECRET, s).hexdigest()


def make_secure_val(s):
    return "%s|%s" % (s, hash_str(s))


def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val

# Password related


def make_salt():
    return "".join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(name, pw, salt=make_salt()):
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)


def valid_pw(name, pw, h):
    # This compares input password with the input confirmation password
    split = h.split(",")
    hash = split[0]
    salt = split[1]

    logging.warning("h =" + h)
    logging.warning("make = " + make_pw_hash(name, pw, salt))
    return h == make_pw_hash(name, pw, salt)
