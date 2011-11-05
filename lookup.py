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
from model import Lookup
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class Pacific_tzinfo(datetime.tzinfo):
 """Implementation of the Pacific timezone."""
 def utcoffset(self, dt):
   return datetime.timedelta(hours=-8) + self.dst(dt)

 def _FirstSunday(self, dt):
   """First Sunday on or after dt."""
   return dt + datetime.timedelta(days=(6-dt.weekday()))

 def dst(self, dt):
   # 2 am on the second Sunday in March
   dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 8, 2))
   # 1 am on the first Sunday in November
   dst_end = self._FirstSunday(datetime.datetime(dt.year, 11, 1, 1))

   if dst_start <= dt.replace(tzinfo=None) < dst_end:
     return datetime.timedelta(hours=1)
   else:
     return datetime.timedelta(hours=0)

 def tzname(self, dt):
   if self.dst(dt) == datetime.timedelta(hours=0):
     return "PST"
   else:
     return "PDT"


class AvTPs(db.Model):
    av = db.StringProperty(multiline=False)
    tps = db.ListProperty(str, indexed=False)


def updateTPs(av, tp):
    record = AvTPs.get_by_key_name("TP:"+av)
    if record is None:
        querya = AvTPs.gql("WHERE av =  :1", av)
        query = querya.get()    
        if querya.count() == 0:
            record = AvTPs(key_name="TP:"+av, av = av, tps = [tp])
            record.put()
            return
        else:
            record = AvTPs(key_name="TP:"+av, av = av, tps = query.tps)
            query.delete()
            logging.info('changing to use key name')
    if len(record.tps)>9 :
        logging.info('more than 9 items')
        record.tps[0:1]=[]
        record.tps += [tp]
        record.put()
    else:
        record.tps += [tp]
        record.put()
        
 
class MainPage(webapp.RequestHandler):
  def put(self):
    #check linden ip
    if not lindenip.inrange(os.environ['REMOTE_ADDR']):
        self.error(403)
    else:
          # This is for a internal logging system... Not for real use...
          logging.debug('R:%s LP:%s ON:%s OK:%s N:%s' % (self.request.headers['X-SecondLife-Region'], self.request.headers['X-SecondLife-Local-Position'], self.request.headers['X-SecondLife-Object-Name'], self.request.headers['X-SecondLife-Object-Key'], self.request.headers['X-SecondLife-Owner-Name']))
          av = self.request.headers['X-SecondLife-Owner-Key']
          avname = self.request.headers['X-SecondLife-Owner-Name']
          if avname != "(Loading...)":
              relations.update_av(av, avname)
          param2=av #the Name the service will be known by         
          bodyparams = self.request.body.split("|")
          param3=bodyparams[0]# the URL for the web service
          try:
              ownparam = bodyparams[1]
              secparam = bodyparams[2]
          except(IndexError):
              pathparms = self.request.path.split("/")
              ownparam = pathparms[-2]
              secparam = pathparms[-1]
          try:
              pubparam = bodyparams[3]
              webmap = bodyparams[4]
          except(IndexError):
              pubparam = "disabled"
              webmap = "0"
          ownurl = param3+'/'+ownparam
          securl = param3+'/'+secparam
          puburl = param3+'/'+pubparam
          logging.info('%s created their url %s' % (param2, param3))
          if webmap == "1":
              time=datetime.datetime.now(Pacific_tzinfo())
              param4=self.request.headers['X-SecondLife-Region']+"|"+self.request.headers['X-SecondLife-Local-Position']+"|"+time.strftime("%Y/%m/%d at %I:%M:%S %p")
              updateTPs(param2, param4)
          if param2=="" or param3=="" :
              self.error(400)
          else:
              newrec=Lookup(key_name="URL:"+param2,av=param2,ownurl=ownurl,securl=securl,puburl=puburl)
              newrec.put()
              self.response.out.write('Added')

  def delete(self):
    #check linden ip
    if not lindenip.inrange(os.environ['REMOTE_ADDR']):
        self.error(403)
    else:
          param2=self.request.headers['X-SecondLife-Owner-Key'] # the name the service is known by
          # This is for a internal logging system... Not for real use...
          logging.debug('R:%s LP:%s ON:%s OK:%s N:%s' % (self.request.headers['X-SecondLife-Region'], self.request.headers['X-SecondLife-Local-Position'], self.request.headers['X-SecondLife-Object-Name'], self.request.headers['X-SecondLife-Object-Key'], self.request.headers['X-SecondLife-Owner-Name']))

          logging.info('%s deleted their url' % (param2))
          record = Lookup.get_by_key_name("URL:"+param2)

          if record is None:
            self.response.set_status(204)
          else:
            record.delete() # remove them all (just in case some how, some way, there is more than one service with the same name 
            self.response.out.write('Removed')

  def get(self):
    #check linden ip
    if not lindenip.inrange(os.environ['REMOTE_ADDR']):
        self.error(403)
    else:
          # This is for a internal logging system... Not for real use...
          logging.debug('R:%s LP:%s ON:%s OK:%s N:%s' % (self.request.headers['X-SecondLife-Region'], self.request.headers['X-SecondLife-Local-Position'], self.request.headers['X-SecondLife-Object-Name'], self.request.headers['X-SecondLife-Object-Key'], self.request.headers['X-SecondLife-Owner-Name']))

          try:
              product = self.request.get('product')
              key = self.request.get('key')
          except(AttributeError):
              product = self.request.path.split("/")[-2]
              key = self.request.path.split("/")[-1]
          if key == "":
              product = self.request.path.split("/")[-2]
              key = self.request.path.split("/")[-1]
          owner = self.request.headers['X-SecondLife-Owner-Key']

          query = relations.getby_subj_obj_type(owner, key, "owns")
          if not query.count() == 0:
              q = Lookup.get_by_key_name("URL:"+key)
              if q is None:
                    logging.warning('%s an owner is retrieving the url for %s and product %s but it doesnt exist' % (owner, key, product))
                    self.error(404)
              else:
                    logging.info('%s an owner is retrieving the url for %s for product %s' % (owner, key, product))
                    self.response.out.write(q.ownurl) #print the URL
          else:
              query2 = relations.getby_subj_obj_type(owner, key, "secowns")
              if not query2.count() == 0:
                  q = Lookup.get_by_key_name("URL:"+key)
                  if q is None:
                        logging.warning('%s a secowner is retrieving the url for %s and product %s but it doesnt exist' % (owner, key, product))
                        self.error(404)
                  else:
                        logging.info('%s a secowner is retrieving the url for %s for product %s' % (owner, key, product))
                        self.response.out.write(q.securl) #print the URL
              else:
                  logging.error('%s is retrieving the url for %s for product %s but was not authorized to do so' % (owner, key, product))
                  self.error(403)
  def post(self):
        if (self.request.get("p", default_value=False)!=False):
            self.put()
        elif (self.request.get("d", default_value=False)!=False):
            self.delete()
            
application = webapp.WSGIApplication(
    [('.*', MainPage)
     ], 
    debug=True) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()