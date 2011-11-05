
#!/usr/bin/python
#Licensed under the GPLv2 (not later versions)
#see LICENSE.txt for details

import cgi
import os
import re
import lindenip
import logging
import relations
import time
from model import Lookup
from operator import itemgetter
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache


class GetSubs(webapp.RequestHandler):
    def get(self):
        #check that we're coming from an LL ip
        if not lindenip.inrange(os.environ['REMOTE_ADDR']):
            self.error(403)
        else:
            av = self.request.headers['X-SecondLife-Owner-Key']
            avname = self.request.headers['X-SecondLife-Owner-Name']
            if avname != "(Loading...)":
                relations.update_av(av, avname)
            #get all relations for which av is owner or secowner
            subdict = {}
            suburldict = {}
            ownersubs = relations.getby_subj_type(av, 'owns')
            for sub in ownersubs:
                id = sub.obj_id
                if id not in subdict:
                    subdict[id] = relations.key2name(id)
                    q = Lookup.get_by_key_name("URL:"+id)
                    if q is None :
                        suburldict[id] = 'None'
                    else:
                        suburldict[id] = q.ownurl
                else:
                    #delete duplicates
                    sub.delete()

            secownersubs = relations.getby_subj_type(av, 'secowns')
            for sub in secownersubs:
                id = sub.obj_id
                if id not in subdict:#since you can be both an owner and a secowner, ignore those here already in the owner list
                    subdict[id] = relations.key2name(id)
                    q = Lookup.get_by_key_name("URL:"+id)
                    if q is None :
                        suburldict[id] = 'None'
                    else:
                        suburldict[id] = q.securl
            currenttime = time.time()
            out = ''
            subsorted = sorted(subdict.items(), key=itemgetter(1))
            for sub in subsorted:
#                out += '%s,%s,%s,%s,' % (sub[0], sub[1], suburldict[sub[0]], currenttime)
# fix for sub restriction we dont send actual urls but only send them on demand
                out += '%s,%s,%s,%s,' % (sub[0], sub[1], "None", 0)
            memcache.set("Subs:"+av, out)
            self.response.out.write(out.rstrip(','))


class GetSubsPages(webapp.RequestHandler):
    def get(self):
        #check that we're coming from an LL ip
        if not lindenip.inrange(os.environ['REMOTE_ADDR']):
            self.error(403)
        else:
            av = self.request.headers['X-SecondLife-Owner-Key']
            avname = self.request.headers['X-SecondLife-Owner-Name']
            if avname != "(Loading...)":
                relations.update_av(av, avname)
            page = int(self.request.get("page", default_value=0))
            if (page == 0):
                #get all relations for which av is owner or secowner
                subdict = {}
                suburldict = {}
                ownersubs = relations.getby_subj_type(av, 'owns')
                for sub in ownersubs:
                    id = sub.obj_id
                    if id not in subdict:
                        subdict[id] = relations.key2name(id)
                        q = Lookup.get_by_key_name("URL:"+id)
                        if q is None :
                            suburldict[id] = 'None'
                        else:
                            suburldict[id] = q.ownurl
                    else:
                        #delete duplicates
                        sub.delete()
    
                secownersubs = relations.getby_subj_type(av, 'secowns')
                for sub in secownersubs:
                    id = sub.obj_id
                    if id not in subdict:#since you can be both an owner and a secowner, ignore those here already in the owner list
                        subdict[id] = relations.key2name(id)
                        q = Lookup.get_by_key_name("URL:"+id)
                        if q is None :
                            suburldict[id] = 'None'
                        else:
                            suburldict[id] = q.securl
                currenttime = time.time()
                out = ''
                subsorted = sorted(subdict.items(), key=itemgetter(1))
                for sub in subsorted:
    #                out += '%s,%s,%s,%s,' % (sub[0], sub[1], suburldict[sub[0]], currenttime)
    # fix for sub restriction we dont send actual urls but only send them on demand
                    out += '%s,%s,%s,%s,' % (sub[0], sub[1], "None", 0)
                outlist = out.rstrip(',').split(",")
                memcache.set("Subs:" + av, outlist)
                if len(outlist) > 80:
                    self.response.out.write(",".join(outlist[0:79]+["more", "1"]))
                else:
                    self.response.out.write(out.rstrip(','))
            else:
                cachedlist = memcache.get("Subs:" + av)
                if cachedlist is None:
                    #get all relations for which av is owner or secowner
                    subdict = {}
                    suburldict = {}
                    ownersubs = relations.getby_subj_type(av, 'owns')
                    for sub in ownersubs:
                        id = sub.obj_id
                        if id not in subdict:
                            subdict[id] = relations.key2name(id)
                            q = Lookup.get_by_key_name("URL:"+id)
                            if q is None :
                                suburldict[id] = 'None'
                            else:
                                suburldict[id] = q.ownurl
                        else:
                            #delete duplicates
                            sub.delete()
        
                    secownersubs = relations.getby_subj_type(av, 'secowns')
                    for sub in secownersubs:
                        id = sub.obj_id
                        if id not in subdict:#since you can be both an owner and a secowner, ignore those here already in the owner list
                            subdict[id] = relations.key2name(id)
                            q = Lookup.get_by_key_name("URL:"+id)
                            if q is None :
                                suburldict[id] = 'None'
                            else:
                                suburldict[id] = q.securl
                    currenttime = time.time()
                    out = ''
                    subsorted = sorted(subdict.items(), key=itemgetter(1))
                    for sub in subsorted:
        #                out += '%s,%s,%s,%s,' % (sub[0], sub[1], suburldict[sub[0]], currenttime)
        # fix for sub restriction we dont send actual urls but only send them on demand
                        out += '%s,%s,%s,%s,' % (sub[0], sub[1], "None", 0)
                    outlist = out.rstrip(',').split(",")
                    memcache.set("Subs:" + av, outlist)
                    cachedlist = outlist
                if (len(cachedlist) > 80*(page+1)):
                    self.response.out.write(",".join(cachedlist[80*page:(80*(page+1)-1)]+["more", str(page+1)]))
                else:
                    self.response.out.write(",".join(cachedlist[80*page:-1]))
                

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('hello world')

application = webapp.WSGIApplication(
    [
     (r'/.*?/getsubs',GetSubs),
     (r'/.*?/getsubspages',GetSubsPages),
     ('/.*', MainPage)
     ],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()