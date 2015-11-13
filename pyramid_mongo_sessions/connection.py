

from datetime import datetime, timedelta

import mongoengine as ma
from random import getrandbits

# from mist.core import config
# from mist.core.helpers import get_rand_token
# from mist.core.model import User



def datetime_to_str(dt):
    if isinstance(dt, datetime):
        return dt.strftime('%Y/%m/%d %H:%m')
    return 'Never'

def get_rand_token(bits=256):
    """Generate a random number of specified length and return its hex string.

    Default is to generate 256 bits = 32 bytes, resulting in a 64 characters
    token to be generated (since a byte needs 2 hex chars).

    """
    return hex(getrandbits(bits))[2:-1]

class AuthToken(ma.Document):
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
    token = ma.StringField(required=True, min_length=64, max_length=64,
                        default=get_rand_token)

    user_id = ma.StringField()

    created = ma.DateTimeField(default= datetime.now)
    ttl = ma.IntField(min_value=0, default=0)

    last_accessed = ma.DateTimeField()
    timeout = ma.IntField(min_value=0, default=0)

    revoked = ma.BooleanField(default=False)

    ip_address = ma.StringField()
    user_agent = ma.StringField()

    meta = {'allow_inheritance': True}


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

    name = ma.StringField(required=True)


class SessionToken(AuthToken):

    context = ma.DictField()


def get_default_connection(request,
                           url=None,
                           **mongo_options):
    """
    Default Mongo connection handler. Once a connection is established it is
    saved in `request.registry`.

    Parameters:

    ``request``
    The current pyramid request object

    ``url``
    An optional connection string that will be passed straight to
    `StrictMongo.from_url`. The connection string should be in the form:
        mongo://username:password@localhost:6379/0

    ``settings``
    A dict of keyword args to be passed straight to `StrictMongo`

    Returns:

    An instance of `StrictMongo`
    """
    # attempt to get an existing connection from the registry
    # mongo = getattr(request.registry, '_mongo_sessions', None)

    # # if we found an active connection, return it
    # if mongo is not None:
    #     return mongo
    # else:
    # 	mongo = auth_token.SessionToken
 
    # otherwise create a new connection
    # if url is not None:
        # remove defaults to avoid duplicating settings in the `url`
    mongo_options.pop('password', None)
    mongo_options.pop('host', None)
    mongo_options.pop('port', None)
    mongo_options.pop('db', None)
    # the StrictMongo.from_url option no longer takes a socket
    # argument. instead, sockets should be encoded in the URL if
    # used. example:
    #     unix://[:password]@/path/to/socket.sock?db=0
    mongo_options.pop('unix_socket_path', None)
    # connection pools are also no longer a valid option for
    # loading via URL
    mongo_options.pop('connection_pool', None)
    # client = MongoClient('localhost:27017')
    connect(**mongo_options)
        # mongo = mongo_client.from_url(url, **mongo_options)
    # else:
    #     mongo = mongo_client(**mongo_options)

    # save the new connection in the registry
    # setattr(request.registry, '_mongo_sessions', mongo)
    
    return SessionToken
