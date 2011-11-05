#!/usr/bin/python
#Licensed under the GPLv2 (not later versions)
#see LICENSE.txt for details

from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import logging
import relations

class AppSettings(db.Model):
  #token = db.StringProperty(multiline=False)
  value = db.StringProperty(multiline=False)

sharedpass = AppSettings.get_or_insert("sharedpass", value="sharedpassword").value

class MainPage(webapp.RequestHandler):
    def put(self):
        if (self.request.headers['sharedpass'] == sharedpass):
            queryparams = self.request.query_string.split("/")
            try:
                subj = queryparams[2]
                obj = queryparams[1]
                type = queryparams[0]
            except(IndexError):
                subj = self.request.body
                obj = self.request.path.split("/")[-1]
                type = self.request.path.split("/")[-2]
                logging.info('Using old method')
            logging.debug('PUT TYPE:%s OBJ:%s SUBJ:%s' % (type, obj, subj))
            relations.create_unique(subj, type, obj)
            memcache.set(obj, "changed")
            self.error(202)
        else:
            self.error(403)
            logging.error('wrong shared password expecting %s received %s ip address' % (sharedpass,self.request.headers['sharedpass'],os.environ['REMOTE_ADDR']))

    def delete(self):
        if (self.request.headers['sharedpass'] == sharedpass):
            queryparams = self.request.query_string.split("/")
            logging.debug('query:%s' % (self.request.query_string))
            try:
                type = queryparams[0]
                obj = queryparams[1]
                subj = queryparams[2]
                mode = self.request.path.split("/")[-1]
            except(IndexError):
                type = self.request.path.split("/")[-1]
                obj = self.request.path.split("/")[-2]
                subj = self.request.path.split("/")[-3]
                mode = self.request.path.split("/")[-4]
                logging.info('Using old method')
            logging.debug('DELETE MODE:%s OBJ:%s SUBJ:%s TYPE:%s' % (mode, obj, subj, type))
            if mode == "type":
                relations.del_by_obj_type(obj, type)
            elif mode == "obj":
                relations.del_by_obj(obj)
            elif mode == "all":
                relations.delete(subj, type, obj)
            elif type == "safety":
                logging.debug('TRYING SAFETY DELETE')
                result = relations.del_by_obj_subj(obj, subj)
                self.response.out.write(result)
            self.response.set_status(202)
        else:
            self.error(403)
            logging.error('wrong shared password expecting %s received %s ip address' % (sharedpass,self.request.headers['sharedpass'],os.environ['REMOTE_ADDR']))

application = webapp.WSGIApplication(
    [('.*', MainPage)
     ],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()