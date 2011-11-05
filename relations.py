import logging
import time
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache

relationtypes = ['owns', 'secowns']#valid relation types.  For the sake of consistency
                                    #let's keep only active verbs in this list
class Av(db.Model):
    id = db.StringProperty()
    name = db.StringProperty()

class Relation(db.Model):
    subj_id = db.StringProperty()
    type = db.StringProperty()
    obj_id = db.StringProperty()

class AppSettings(db.Model):
  #token = db.StringProperty(multiline=False)
  value = db.StringProperty(multiline=False)


sharedpass = AppSettings.get_or_insert("sharedpass", value="sharedpassword").value
dataurl = AppSettings.get_or_insert("dataurl", value="http://yourcmdapp.appspot.com").value

def key2name(key):
    """given an av uuid, returns av name.  Returns None if av not found"""
    av = Av.get_by_key_name("Av:"+key)
    if av is None:
        av = Av.gql("WHERE id = :1", key).get()
        if av:
            Av(key_name="Av:"+av.id,id = av.id, name = av.name).put()
            av.delete()
    if av:
        return av.name
    else:
        logging.info("Fetching name from data server for: %s (Start time: %f)" % (key, time.time()))

        fetchanswer = urlfetch.fetch(dataurl + '/avsync/getname?key=%s' % key, method="GET", headers={'sharedpass': sharedpass})
        if fetchanswer.status_code == 200 and fetchanswer.content != "":
            logging.info("Answer received: %s (End time %f)" % (fetchanswer.content, time.time()))
            Av(key_name="Av:" + key,id = key, name = fetchanswer.content).put()
            return fetchanswer.content
        else:
            logging.warning("Could not be resolved or answer took too long! Error %d; Time: %f, Content:\n%s" % (fetchanswer.status_code, time.time(), fetchanswer.content))
            return "~Old Sub"

def name2key(name):
    """given an av name, returns av uuid.  Returns None if av not found"""
    av = Av.gql("WHERE name = :1", name).get()
    if av:
        return av.id
    else:
        return None

def update_av(id, name):
    """update's av's name if key found, else creates entity.  only use request header data.  POST and PUT data are not trustworthy."""
    av = Av.get_by_key_name("Av:"+id)
    if av is None:
        Av(key_name="Av:"+id,id = id, name = name).put()


def getby_subj_type(subj, type):
    """returns all relation entities with given subj, type"""
    return Relation.gql("WHERE subj_id = :1 AND type = :2", subj, type)

def getby_obj_type(obj, type):
    """returns all relation entities with given obj, type"""
    return Relation.gql("WHERE obj_id = :1 AND type = :2", obj, type)

def getby_subj_obj(subj, obj):
    """returns all relation entities with given subj_id and obj_id"""
    return Relation.gql("WHERE subj_id = :1 AND obj_id = :2", subj, obj)

def getby_subj_obj_type(subj, obj, type):
    return Relation.gql("WHERE subj_id =  :1 AND type = :2 and obj_id = :3", subj, type, obj)

def create_unique(subj, type, obj):
    """creates relation with given subj_id, type, and obj_id, if not already present"""
    query = Relation.gql("WHERE subj_id =  :1 AND type = :2 and obj_id = :3", subj, type, obj)
    if query.count() == 0:
        record = Relation(subj_id = subj, type = type, obj_id = obj)
        record.put()

def delete(subj, type, obj):
    """deletes any and all entities with given subj_id, type, and obj_id"""
    memcache.set(obj, "changed")
    query = Relation.gql("WHERE subj_id =  :1 AND type = :2 and obj_id = :3", subj, type, obj)
    for record in query:
        record.delete()

def del_by_obj(obj):
    """deletes any and all entities with given obj_id"""
    memcache.set(obj, "changed")
    query = Relation.gql("WHERE obj_id = :1", obj)
    for record in query:
        record.delete()

def del_by_obj_type(obj, type):
    """deletes any and all entities with given obj_id and type"""
    memcache.set(obj, "changed")
    query = Relation.gql("WHERE obj_id = :1 AND type = :2", obj, type)
    for record in query:
        record.delete()

def del_by_obj_subj(obj, subj):
    """deletes any and all entities with given subj_id, type, and obj_id"""
    memcache.set(obj, "changed")
    result = 0
    query = Relation.gql("WHERE subj_id = :1 AND obj_id = :2", subj, obj)
    for record in query:
        if record.type=="owns":
            result=result|1
        if record.type=="secowns":
            result=result|2
        record.delete()
    return '%d' % result
