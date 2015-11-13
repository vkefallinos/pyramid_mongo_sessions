import binascii
import os

from pyramid.compat import text_
# from pyramid.decorator import reify
from pyramid.interfaces import ISession
from zope.interface import implementer
# from mongo_session.compat import cPic
from compat import cPickle


@implementer(ISession)
class MongoSession(object):
    """docstring for MongoSession"""
    def __init__(self,
        session,
        new,
        serialize=cPickle.dumps,
        deserialize=cPickle.loads):
        super(MongoSession, self).__init__()

        self.new = new
        self.created = session.created
        self.invalidate = session.revoke
        self.changed = session.save
        self.save = session.save
        self.session = session


    # def __delitem__(self,key):
    #     self.session[key] = None

    # def __setitem__(self,key,value):
    #     self.session[key] =   value
    # def __