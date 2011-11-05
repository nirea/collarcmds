import logging
import datetime
from model import GoogleSLIds
from google.appengine.ext import db

time = datetime.datetime.utcnow()
time += datetime.timedelta(-1)
query = GoogleSLIds.gql("WHERE verifed = :1 AND datetime <= :2", False, time)
logging.info("%s verification tries were removed.", query.count())
db.delete(query.fetch(50))