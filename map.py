# Code was released into the public domain by Darien Caldwell
# http://forums.secondlife.com/showthread.php?t=323981

import cgi
import urllib
import logging
import os
import relations
from math import log, ceil
from decimal import *
from model import GoogleSLIds
from operator import itemgetter
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class AvTPs(db.Expando):
    av = db.StringProperty(multiline=False)
    tps = db.ListProperty(str)

def getsubs(userid):
    subs = memcache.get(userid+"subs")
    if subs is not None:
        return subs
    else:
        logging.warning('Unable to get subs from memcache for userid: %s' % (userid))

def getownsubs(userid):
    subs = memcache.get(userid+"ownsubs")
    if subs is not None:
        return subs
    else:
        logging.warning('Unable to get ownsubs from memcache for userid: %s' % (userid))

def getsecownsubs(userid):
    subs = memcache.get(userid+"secownsubs")
    if subs is not None:
        return subs
    else:
        logging.warning('Unable to get secownsubs from memcache for userid: %s' % (userid))

def getownerlist(userid):
    ownerlist = memcache.get(userid+"ownerlist")
    if ownerlist is not None:
        sublist = memcache.get(userid+"subs").keys()
        checksubs = memcache.get_multi(sublist)
        for sub in checksubs:
            if checksubs[sub] is not None:
                memcache.delete_multi(sublist)
                ownerlist = getownerlist(userid)
                break
        return ownerlist
    else:
        q1 = GoogleSLIds.all().filter("google_id =", userid)
        q2 = GoogleSLIds.all().filter("google_id =", userid)
        q3 = GoogleSLIds.all().filter("google_id =", userid)
        if not q1.count() == 0:
              q1.filter("verifed =", True)
              if not q1.count() == 0:
                  ownerlist = 'Verifed names:<br /><table border="1">'
                  subdict = {}
                  subdictown = {}
                  subdictsecown = {}
                  for x in q1:
                      ownerlist += '<tr><td colspan="2">'+x.sl_name+"</td></tr>"
                      av = x.sl_key
                      subdictownloc = {}
                      subdictsecownloc = {}
                      ownersubs = relations.getby_subj_type(av, 'owns')
                      for sub in ownersubs:
                          id = sub.obj_id
                          if id not in subdictownloc:
                              subdictownloc[id] = relations.key2name(id)
                          else:
                              #delete duplicates
                              sub.delete()
                          
                      secownersubs = relations.getby_subj_type(av, 'secowns')
                      for sub in secownersubs:
                          id = sub.obj_id
                          if id not in (subdictownloc or subdictsecownloc):#since you can be both an owner and a secowner, ignore those here already in the owner list
                              subdictsecownloc[id] = relations.key2name(id)
                              
                      out = ''
                      subdictown.update(subdictownloc)
                      subdictsecown.update(subdictsecownloc)
                      subsortedown = sorted(subdictownloc.items(), key=itemgetter(1))
                      subsortedsecown = sorted(subdictsecownloc.items(), key=itemgetter(1)) 
                      for sub in subsortedown:
                          out += '<tr><td><a href="/map/?key=%s">%s</a></td><td>Owner</td></tr>' % (sub[0], sub[1])
                      for sub in subsortedsecown:
                          out += '<tr><td><a href="/map/?key=%s">%s</a></td><td>Sec. Owner</td></tr>' % (sub[0], sub[1])
                      ownerlist += out
                  ownerlist +='</table>'
                  q2.filter("verifed =", False)
                  if not q2.count() == 0:
                      ownerlist += "You have the following names waiting to be verifed: <br />"
                      for x in q2:
                          ownerlist += x.sl_name+"<br />"
                  ownerlist += form
                  subdict.update(subdictown)
                  subdict.update(subdictsecown)
                  memcache.set(userid+"ownerlist", ownerlist, 600)
                  memcache.set(userid+"subs", subdict, 600)
                  memcache.set(userid+"ownsubs", subdictown, 600)
                  memcache.set(userid+"secownsubs", subdictsecown, 600)
                  return ownerlist
              else:
                  logging.warning('%s is trying to get %s page but does not have any verified users' % (useremail, param2))
                  return "error"
        else:
            logging.warning('%s is trying to get %s page but does not have any verified or unvierified users' % (useremail, param2))
            return "error"
                  

form = '''

'''

userid = ""
useremail = ""
param2 = ""

class MainPage(webapp.RequestHandler):
  def get(self):
      if self.request.host.split(".")[-2] == "mycollar":
          googleMapKey = "ABQIAAAAllmRirwxU-abqO4akMFFPhTmk8oiZWNMDVJqQZiH754NOJiLQhQs9kkQl_27ijrhPqU2i-yBRH-X7A"
      elif self.request.host.split(".")[-2] == "appspot":
          googleMapKey = "ABQIAAAAllmRirwxU-abqO4akMFFPhRlOb26qSyU154aZeLwOrF4C7-DphS23YsdNRnYYJkSxtcIV2PDrFFQuw"
      user = users.get_current_user()
      userid = user.user_id()
      useremail = user.email()
      param2 = self.request.get('key')
      ownerlist = getownerlist(userid)
      if (ownerlist == "error"):
          self.redirect("/webinterface/")
          return ""
      ownsubs = getownsubs(userid)
      secownsubs = getsecownsubs(userid)
      subs = getsubs(userid)
      if param2 in ownsubs or param2 in secownsubs or users.is_current_user_admin():
          subname = subs[param2]
          q = db.GqlQuery("SELECT * FROM AvTPs WHERE av = :kk",kk=param2)
          count=q.count(2)
          if count==0 :
                logging.warning('%s is retrieving the url for %s but tps doesnt exist' % (useremail, param2))
                tpstmp=[u'not having web maps enabled so you see The Temple of the Collar, Keraxic(462336, 305920)|(55, 210, 23)|2010/01/01 at 00:00:00 AM']
          else:
                logging.info('%s is retrieving the url for %s' % (useremail, param2))
                record=q.get()
                tpstmp = record.tps
          if True:
                tps = ''
                links = ''
                xlist = []
                ylist = []
                
                for a in tpstmp:
                    b = a.split("|")
                    globcor=b[0].split("(")[-1]
                    loccor=b[1].split(",")
                    xloc=loccor[0].strip("(")
                    yloc=loccor[1]
                    zloc=loccor[2].strip(")")
                    x=str(float(globcor.split(",")[0])/256+float(xloc)/256)
                    y=str(float(globcor.split(",")[1].strip(")"))/256+float(yloc)/256)
                    mapcor=x+", "+y+")"
                    xlist += [Decimal(x)]
                    ylist += [Decimal(y)]
                    tps += 'mapWindow = new MapWindow("'+subname+' was at '+b[0].split("(")[0]+' ('+str(int(float(xloc)))+', '+str(int(float(yloc)))+', '+str(int(float(zloc)))+') on '+b[2]+'");\n'
                    tps += 'marker = new Marker(all_images, new XYPoint('+mapcor+');\n'
                    tps += 'mapInstance.addMarker(marker, mapWindow);\n'
                    links += '<p><a href="javascript: mapInstance.panOrRecenterToSLCoord(new XYPoint('+mapcor+', true);"> '+subname+' was at '+b[0].split("(")[0]+' ('+str(int(float(xloc)))+', '+str(int(float(yloc)))+', '+str(int(float(zloc)))+') on '+b[2]+'</a></p>\n'
                xcenter = str((max(xlist)-min(xlist))/2+min(xlist))
                ycenter = str((max(ylist)-min(ylist))/2+min(ylist))
                xdiff=max(xlist)-min(xlist)
                ydiff=max(ylist)-min(ylist)
                if ydiff == 0 and xdiff == 0:
                    scale='2'
                elif xdiff>ydiff :
                    scale=str(ceil(log(xdiff,2)))
                else:
                    scale=str(ceil(log(ydiff,2)))
                if scale>8:
                    xcenter = str(sum(xlist)/len(xlist))
                    ycenter = str(sum(ylist)/len(ylist))
                if param2 in ownsubs:
                  q = db.GqlQuery("SELECT * FROM Lookup WHERE av = :kk",kk=param2)
                  count=q.count(2)
                  if count==0 :
                        cmdurl=''
                  else:
                        record=q.get()
                        cmdurl = record.ownurl
                elif param2 in secownsubs:
                  q = db.GqlQuery("SELECT * FROM Lookup WHERE av = :kk",kk=param2)
                  count=q.count(2)
                  if count==0 :
                        cmdurl=''
                  else:
                        record=q.get()
                        cmdurl = record.securl
                header = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
<title>OpenCollar webinterface for '''+subname+'''</title>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
<script src="http://maps.google.com/maps?file=api&v=2&key='''+ googleMapKey +'''"  type="text/javascript"></script>
<script src="http://slurl.com/_scripts/slmapapi.js" type="text/javascript"></script>
<link rel="stylesheet" type="text/css" href="http://slurl.com/_styles/MAIN.css" />
<style>
div#map-container {
      width: 500px;
      height: 500px;
      float:left;
      margin: 5px;
      font-size: 11px;
      border-style:solid;
      border-width:0px 1px;
}
div#form {
      position: fixed;
      bottom: 0px;
      background-color: #000000;
      width: 100%;
      border-style:solid;
      border-width:1px 0px 0px;
}
div#cmdstore {
      display:none;
}
div#ownerlist {
      float:left;
}
div#title {
      width: 99%;
      position:absolute;
}
div#logo {
      left: 0px;
      position:absolute;
}
div#top {
      width: 100%;
      height:128px;
      border-style:solid;
      border-width:0px 0px 1px;
}
div#tplist {
    min-height:500px;
    font-size: 11px;
}
table {
    border-color: #FF0000;
    borderCollapse: collapse;
    border-spacing: 0px;
    border-width: 0px 1px 1px 0px;
}
td {
    border-color: #FF0000;
    border-width: 1px 0px 0px 1px;
}
body {
    background-color: #000000;
    color: #FF0000;
    overflow: auto;
    font-size: medium;
    border-color: #FF0000;
}
html {
    background-color: #000000
}
input {
    background-color: #000000;
    color: #FF0000;
    outline-color: #000000;
    border-color: #FF0000;
}
.center {
    text-align: center;
}
</style>
<script id="external_script" type="text/JavaScript"></script>
<script type="text/javascript">
var count=0;
function submit()
{
count = count + 1;
 var cmd=document.getElementById("cmd").value;
 document.getElementById("cmd").disabled=true
 document.getElementById('cmdstore').innerHTML=count;
 setTimeout("checkcmd(count)",3000);
   var old = document.getElementById('uploadScript');
   if (old != null) {
     old.parentNode.removeChild(old);
     delete old;
   }
   var body = document.getElementsByTagName("body")[0];
   var script = document.createElement('script');
   script.id = 'uploadScript';
   script.type = 'text/javascript';
   script.src = '''+"'"+cmdurl+"/00000000-0000-0000-0000-000000000000/cmdreceived?'"+'''+cmd;
   body.appendChild(script);
}
function cmdreceived(cmd)
{
 if (cmd == 'pong')
 {
     collarworking();
 }
 else
 {
     //alert("it worked");
 }
 document.getElementById("cmd").value='';
 document.getElementById('cmdstore').innerHTML='0';
 document.getElementById("cmd").disabled=false;
}
function checkcmd(sentcount)
{
    if (document.getElementById('cmdstore').innerHTML==sentcount)
    {
        alert("error");
    }
}
function javascriptworking()
{
    document.getElementById("form").innerHTML='The wear is not online or httpin is disabled.';
    var body = document.getElementsByTagName("body")[0];
    var script = document.createElement('script');
    script.id = 'uploadScript';
    script.type = 'text/javascript';
    script.src = '''+"'"+cmdurl+"/00000000-0000-0000-0000-000000000000/cmdreceived?'"+'''+'ping';
    body.appendChild(script);
}
function collarworking()
{
    document.getElementById("form").innerHTML='<form action="javascript:submit();">Cmd <input type="text" id="cmd" size="100" maxlength="255"><input type="submit" /></form>';
}
</script>


<script>
// mapInstance and marker is set as a glabal, so that the removeMarker function can access them
var mapInstance, marker, mapWindow;
function loadmap() {
  // creates the map
  javascriptworking();//for OC to check if the collar is up.
  mapInstance = new SLMap(document.getElementById('map-container'));
  mapInstance.centerAndZoomAtSLCoord(new XYPoint('''+xcenter+', '+ycenter+'), '+scale+''');
  
  // creates the icons
  var yellow_dot_image = new Img("http://slurl.com/examples/b_map_yellow.gif", 9, 9);
  var yellow_icon = new Icon(yellow_dot_image);
  var all_images = [yellow_icon, yellow_icon, yellow_icon, yellow_icon, yellow_icon, yellow_icon];
'''
                mid = '''
}
</script>
</head>
<body onload="loadmap()" onunload="GUnload()">
<div id="top" class="center">
<div id="logo"><img src="/static/OpenCollarLogo128.png" /></div>
<div id="title">
<h1><a href="/webinterface/">Web Interface</a> for '''+subname+'''</h1>
<h2>OpenCollar</h2>
</div>
</div>
<div id="ownerlist">
<br />
'''+ownerlist+'<br /><br /></div><div id="map-container"></div><div id="tplist">'
                end = '''
</div>
<div id="form">
JavaScript does not seem to be enabled.
</div>
<div id="cmdstore">
</div>
</body>
'''

                self.response.out.write(header+tps+mid+links+end) #print the map

      else:
        logging.warning('%s is not owned by userid: %s' % (parm2,userid))
        self.redirect("/webinterface/")


application = webapp.WSGIApplication(
    [('.*', MainPage)
     ], 
    debug=True) 

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()