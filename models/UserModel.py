# Create a database for user information
from google.appengine.ext import db


class User(db.Model):
    """
    Instantiates a class to store user data in the datastore
    made up of user attributes.
    """
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)
