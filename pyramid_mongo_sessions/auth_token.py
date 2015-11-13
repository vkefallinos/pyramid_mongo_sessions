from datetime import datetime, timedelta

from mongoengine import *

from mist.core import config
from mist.core.helpers import get_rand_token
from mist.core.model import User


connect(db='mist2', host='localhost:27017')


def datetime_to_str(dt):
    if isinstance(dt, datetime):
        return dt.strftime('%Y/%m/%d %H:%m')
    return 'Never'


class AuthToken(Document):
    # def __init__(self, *args, **kwargs):
    #     Document.__init__(self, *args, **kwargs)
    #     # Ensure token is unique
    #     if not self.token:
    #         while 1:
    #             token = get_rand_token()
    #             try:
    #                 self.objects.get(token=token)
    #                 print "new token"
    #             except:
    #                 self.token = token
    #                 break
    #         self.created_at = datetime.now()
    #         self.last_accessed = datetime.now()
    #     else:
    #         print "accessed"
    #         self.last_accessed = datetime.now()
    #     if self.timeout:
    #         print "will timeout"
    #         print self.created_at
    #         # self.meta = {
    #         #         'allow_inheritance': True,
    #         #         'indexes': [
    #         #             {'fields': ['created_at'], 'expireAfterSeconds': 10}
    #         #         ]
    #         #     }
    #     self.save()
    token = StringField(required=True, min_length=64, max_length=64,
                        default=get_rand_token)

    user_id = StringField()

    created = DateTimeField(default= int(datetime.now().strftime("%s")) * 1000)
    ttl = IntField(min_value=0, default=0)

    last_accessed = DateTimeField()
    timeout = IntField(min_value=0, default=0)

    revoked = BooleanField(default=False)

    ip_address = StringField()
    user_agent = StringField()

    meta = {'allow_inheritance': True}
    def changed(self):
        self.session.Session.save()

    def expires(self):
        if self.ttl:
            return self.created_at + timedelta(seconds=self.ttl)

    def is_expired(self):
        return self.ttl and self.expires() < datetime.now()

    def timesout(self):
        if self.timeout:
            return self.accessed_at + timedelta(seconds=self.timeout)

    def is_timedout(self):
        return self.timeout and self.timesout() < datetime.now()

    def is_valid(self):
        return not (self.revoked or self.is_expired() or self.is_timedout())

    def invalidate(self):
        self.revoked = True

    def touch(self):
        self.last_accessed = datetime.now()
    def accessed(self):
        if self.last_accessed:
            return True
        else:
            return False


    def get_user(self):
        if self.user_id:
            user = User()
            user.get_from_id(self.user_id)
            return user

    def __str__(self):
        msg = "Valid" if self.is_valid() else "Invalid"
        msg += " %s '%si...'" % (self.__class__.__name__, self.token[:6])
        user = self.get_user()
        userid = "Anonymous" if user is None else user.email
        msg += " for %s - " % userid
        msg += "Expired:" if self.is_expired() else "Expires:"
        msg += " %s - " % datetime_to_str(self.expires())
        msg += "Timed out:" if self.is_timedout() else "Times out:"
        msg += " %s - " % datetime_to_str(self.timesout())
        msg += "Revoked: %s" % self.revoked
        return msg


class ApiToken(AuthToken):

    name = StringField(required=True)


class SessionToken(AuthToken):

    context = DictField()
