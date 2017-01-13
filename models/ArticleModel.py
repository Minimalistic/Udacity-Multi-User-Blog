from google.appengine.ext import db

# Create a database for blog post information


class Article(db.Model):
    """
    Instantiates a class to store articles/post data in the datastore
    made up of post attributes.
    """
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    edited = db.DateTimeProperty(auto_now=True)
    user = db.StringProperty(required=True)
    likes = db.IntegerProperty(default=0)
