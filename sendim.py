# Code was released into the public domain by Darien Caldwell
# http://forums.secondlife.com/showthread.php?t=323981

import cgi
import urllib
import logging
import lindenip
import os
import relations
import time
import datetime
import string
from model import GoogleSLIds
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db


class MainPage(webapp.RequestHandler):

    def get(self):
        logging.debug('R:%s LP:%s ON:%s OK:%s N:%s' % (self.request.headers['X-SecondLife-Region'], self.request.headers['X-SecondLife-Local-Position'], self.request.headers['X-SecondLife-Object-Name'], self.request.headers['X-SecondLife-Object-Key'], self.request.headers['X-SecondLife-Owner-Name']))
        query = GoogleSLIds.gql("WHERE sentim = False LIMIT 1")
        if query.count() == 0:
            message = "No IMs to send"
            self.response.out.write(message)
        else:
            q = query.get()
            logging.info('sent info for verifying %s owns %s' % (q.google_email, q.sl_name))
            message = '%s|%s|%s|%s' % (q.google_email, q.sl_key, q.key(), q.vericode)
            self.response.out.write(message)
            

    def put(self):
        key = self.request.path.split("/")[-1]
        sent = GoogleSLIds.get(key)
        sent.sentim = True
        sent.put()
        logging.info('IM was sent for email:%s SLname:%s key:%s' % (sent.google_email, sent.sl_name, key))
        query = GoogleSLIds.gql("WHERE sentim = False LIMIT 1")
        if query.count() == 0:
            message = "No IMs to send"
            self.response.out.write(message)
        else:
            q = query.get()
            logging.info('sent info for verifying %s owns %s' % (q.google_email, q.sl_name))
            message = '%s|%s|%s|%s' % (q.google_email, q.sl_key, q.key(), q.vericode)
            self.response.out.write(message)

application = webapp.WSGIApplication(
    [('.*', MainPage)
     ], 
    debug=True) 

def real_main():
  run_wsgi_app(application)
  
def profile_main():
 # This is the main function for profiling 
 # We've renamed our original main() above to real_main()
 import cProfile, pstats, StringIO
 prof = cProfile.Profile()
 prof = prof.runctx("real_main()", globals(), locals())
 stream = StringIO.StringIO()
 stats = pstats.Stats(prof, stream=stream)
 stats.sort_stats("time")  # Or cumulative
 stats.print_stats(80)  # 80 = how many to print
 # The rest is optional.
 # stats.print_callees()
 # stats.print_callers()
 logging.info("Profile data:\n%s", stream.getvalue())

if __name__ == "__main__":
  profile_main()