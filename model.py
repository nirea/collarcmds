from google.appengine.ext import db

class GoogleSLIds(db.Model):
  google_id = db.StringProperty(multiline=False)
  google_email = db.StringProperty(multiline=False)
  sl_key = db.StringProperty(multiline=False)
  sl_name = db.StringProperty(multiline=False)
  verifed = db.BooleanProperty(default=False)
  datetime = db.DateTimeProperty()
  vericode = db.StringProperty()
  sentim = db.BooleanProperty(default=False)
  
class Lookup(db.Model):
  av = db.StringProperty(multiline=False)
  product = db.StringProperty(multiline=False)
  ownurl = db.StringProperty(multiline=False, indexed=False)
  securl = db.StringProperty(multiline=False, indexed=False)
  puburl = db.StringProperty(multiline=False, indexed=False)