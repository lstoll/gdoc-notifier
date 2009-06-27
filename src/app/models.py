from google.appengine.ext import db
from ragendja.auth.google_models import User as BaseUser

class User(BaseUser):
    """Represents a user in the system"""
    pickled_tokens = db.BlobProperty()