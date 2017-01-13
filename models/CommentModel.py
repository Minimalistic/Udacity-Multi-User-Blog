from google.appengine.ext import db

# Create a database for comment information


class Comment(db.Model):
    """
    Instantiates a class to store comments data in the datastore.
    """
    article_id = db.IntegerProperty(required=True)
    user = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
