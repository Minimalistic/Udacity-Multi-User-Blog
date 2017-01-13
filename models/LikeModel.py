from google.appengine.ext import db

class Like(db.Model):
    """
    Manages the likes for individual posts.
    """
    article_id = db.IntegerProperty(required=True)
    user = db.StringProperty(required=True)
