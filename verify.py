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


head = '''
<html>
<head>
<title>webinterface</title>
</head>
<body>
'''
end = '''
</body>
</html>
'''

class MainPage(webapp.RequestHandler):

    def get(self):
        key = self.request.path.split("/")[-1].split("?")[0]
        verify = GoogleSLIds.get(key)
        verify.verifed = True
        verify.put()
        logging.info('%s vefifed that %s can access their info' % (verify.sl_name, verify.google_email))
        message = '''
You have verifed that %s is owned by %s.
<br />
<a href="/webinterface/">click here to use the webinterface.</a>
''' % (verify.sl_name, verify.google_email)
        self.response.out.write(head+message+end)

application = webapp.WSGIApplication(
    [('.*', MainPage)
     ], 
    debug=True) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()