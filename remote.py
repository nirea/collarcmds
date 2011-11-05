#!/usr/bin/python
#Licensed under the GPLv2 (not later versions)
#see LICENSE.txt for details

import cgi
import os
import re
import lindenip
import time

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache

def QueueString(av):
    cachekey = 'queuestring-%s' % (av)
    cachedata = memcache.get(cachekey)
    query = QueuedCommand2.gql('WHERE av = :1', av)    
    if cachedata is not None:
        #delete data from datastore
        for record in query:
            record.delete()
        #delete data from cache
        memcache.delete(cachekey, 0)
        #return data
        return cachedata
    else:
        #check memcache  for av's queuestring.  if present, return, and delete both cache and db values
        #if not present, do as below
        if query.count() > 0:
            #return the string, capped at 2048
            out = ''
            for record in query:
                add = '%s|%s\n' % (record.str, record.sender)
                if len(out + add) < 2000:#lazy cushion of 48 chars so that 'more' itself isn't past the cap
                    out += add
                    record.delete()
                else:
                    out += 'more'
                    return out
            return out
        else:
            return None

def Enqueue(av, str, sender):
    cachekey = 'queuestring-%s' % (av)
    cachedata = memcache.get(cachekey)
    if cachedata is not None:
        #append
        cachedata += '%s|%s\n' % (str, sender)
        memcache.replace(cachekey, cachedata, 3600, 0)
    else:
        #just set
        memcache.add(cachekey, '%s|%s\n' % (str, sender), 3600)
    cmd = QueuedCommand2(av = av, str = str, sender = sender, ts = time.time())
    cmd.put()

def CleanUp():
    #look up all QueuedCommands older than timeout, and delete
    timeout = 3600.0 #1 hour
    query = QueuedCommand2.gql('WHERE ts < :1', time.time() - timeout)
    for record in query:
        record.delete()
    
class QueuedCommand2(db.Model):
    av = db.StringProperty(required =  True)
    str = db.StringProperty(required = True)
    sender = db.StringProperty(required = True)
    ts = db.FloatProperty(required = True)#unix time showing when the cmd was given            

class MainPage(webapp.RequestHandler):
    def get(self):
        #check linden ip
        if not lindenip.inrange(os.environ['REMOTE_ADDR']):
            self.redirect("/webinterface/", False)
        else:
            av = self.request.headers['X-SecondLife-Owner-Key']        
            out = QueueString(av)
            if out is None:
                #self.error(404)
                self.response.headers['Content-Type'] = 'text/plain'                 
                self.response.out.write(out)
            else:
                self.response.headers['Content-Type'] = 'text/plain'                 
                self.response.out.write(out)
       #get key
      #look up cmds for key
       #return in newline-delimited page, 2048 char limit, "more" if necessary
       
    def put(self):
        #check linden IP
        if not lindenip.inrange(os.environ['REMOTE_ADDR']):
            self.error(403)
        else:        
            #get sender key
            sender = self.request.headers['X-SecondLife-Owner-Key']
            #url should be 'remote/<rcpt>/<num>/<str>        
            av = self.request.path.split("/")[-1]
            cmd = self.request.body
            #need to handle invalid keys somehow... maybe just delete all moldy queuedcommands on each request
            #enqueue command
            CleanUp()            
            Enqueue(av, cmd, sender)
            self.response.headers['Content-Type'] = 'text/plain'                 
            self.response.out.write('enqueued %s=%s' % (self.request.path, cmd))

application = webapp.WSGIApplication(
    [('.*', MainPage)
     ], 
    debug=True) 

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()    