from google.appengine.ext import db
from ragendja.auth.google_models import User as BaseUser

class User(BaseUser):
    """Represents a user in the system"""
    pickled_tokens = db.BlobProperty()
    
class Document(db.Model):
    """Represents a Document in the system"""
    user = db.ReferenceProperty(User,required=True)
    link = db.StringProperty(required=True)
    author_email = db.StringProperty(required=True)
    doc_id = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    last_updated = db.DateTimeProperty(required=True)