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
from random import choice
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db



head = '''
<html>
<head>
<title>webinterface</title>
<style>
body {
    background-color: #000000;
    color: #FF0000;
}
input {
    background-color: #000000;
    color: #FF0000;
    outline-color: #000000;
    border-color: #FF0000;
}
</style>
</head>
<body>
'''
end = '''
</body>
</html>
'''
form = '''
<form name="username" action="/webinterface/" method="post">
Verify an account you own. Enter your user name:
<input type="text" name="username" />
<input type="submit" value="Submit" />
</form>
'''

def GenVeriCode(length=4, chars=string.letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])

class MainPage(webapp.RequestHandler):

    def get(self):
        user = users.get_current_user()
        userid = user.user_id()
        q1 = GoogleSLIds.all().filter("google_id =", userid)
        q2 = GoogleSLIds.all().filter("google_id =", userid)
        q3 = GoogleSLIds.all().filter("google_id =", userid)
        if q1.count() == 0:
            message = '''
    You do not have any SL names linked to this acount. Enter a SL username to be verified. You will get an IM to complte the verifcation.
    <br />
    '''+form
            self.response.out.write(head+message+end)#promt to add name to list
        else:
            q1.filter("verifed =", True)
            if not q1.count() == 0:
                message = "Verifed names:<br />"
                for x in q1:
                    message += x.sl_name+"<br />"
                    av = x.sl_key
                    subdictown = {}
                    subdictsecown = {}
                    ownersubs = relations.getby_subj_type(av, 'owns')
                    for sub in ownersubs:
                        id = sub.obj_id
                        if id not in subdictown:
                            subdictown[id] = relations.key2name(id)
                        else:
                            #delete duplicates
                            sub.delete()
                        
                    secownersubs = relations.getby_subj_type(av, 'secowns')
                    for sub in secownersubs:
                        id = sub.obj_id
                        if id not in (subdictown or subdictsecown):#since you can be both an owner and a secowner, ignore those here already in the owner list
                            subdictsecown[id] = relations.key2name(id)
                            
                    out = ''
                    for sub in subdictown:
                        out += '<a href="/map/?key=%s">%s</a> own <br />' % (sub, subdictown[sub])
                    for sub in subdictsecown:
                        out += '<a href="/map/?key=%s">%s</a> secown <br />' % (sub, subdictsecown[sub])
                    message += out
                q2.filter("verifed =", False)
                if not q2.count() == 0:
                    message += "You have the following names waiting to be verifed: <br />"
                    for x in q2:
                        message += x.sl_name+"<br />"
                message += form
                #at least one acount verifed
                self.response.out.write(head+message+end)
            else:
                message = "You have the following names waiting to be verifed: <br />"
                results = q2.fetch(10) 
                for x in results:
                    message += x.sl_name+"<br />"
                message += form
                self.response.out.write(head+message+end)#show the acocounts not verifed and promt or more

    def post(self):
        user = users.get_current_user()
        a = GoogleSLIds().gql("WHERE google_id = :1 AND sl_name = :2", user.user_id(), self.request.get("username")).get()
        if (a is None):
            a = GoogleSLIds()
        if not (a.verifed):
            a.google_id = user.user_id()
            a.google_email = user.email()
            a.sl_name = self.request.get("username")
            a.sl_key = relations.name2key(a.sl_name)
            a.datetime = datetime.datetime.utcnow()
            a.vericode = GenVeriCode()
            if not a.sl_key == None:
                #notify in world object
                a.sentim = False
                logging.info('%s asked to be linked to %s and was found in the database' % (a.google_email, a.sl_name))
            else:
                a.sentim = True #cannot send an IM so mark as sent.
                logging.info('%s asked to be linked to %s but was not found in the database.' % (a.google_email, a.sl_name))
            a.put()
            message = '''
If we have records of '''+a.sl_name+''' then a IM has been sent. 
<br />
Enter a SL username to be verified. You will get an IM to complete the verification.
<br />
'''+form
        else:
            message = '''
You have already verified '''+a.sl_name+'''. 
<br />
Enter a SL username to be verified. You will get an IM to complete the verification.
<br />
'''+form
        self.response.out.write(head+message+end)

application = webapp.WSGIApplication(
    [('.*', MainPage)
     ], 
    debug=True) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()