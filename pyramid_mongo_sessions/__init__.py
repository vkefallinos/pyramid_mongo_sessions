from zope.interface import implementer

from pyramid.interfaces import ISession
from pyramid.interfaces import ISessionFactory
from pyramid.session import (
    signed_deserialize,
    signed_serialize,
    )

def includeme(config):
    """
    This function is detected by Pyramid so that you can easily include
    `pyramid_mongo_sessions` in your `main` method like so::

        config.include('pyramid_mongo_sessions')

    Parameters:

    ``config``
    A Pyramid ``config.Configurator``
    """
    settings = config.registry.settings

    # special rule for converting dotted python paths to callables
    for option in ('client_callable', 'serialize', 'deserialize',
                   'id_generator'):
        key = 'mongo.sessions.%s' % option
        if key in settings:
            settings[key] = config.maybe_dotted(settings[key])

    session_factory = session_factory_from_settings(settings)
    config.set_session_factory(session_factory)

def session_factory_from_settings(settings):
    """
    Convenience method to construct a ``MongoSessionFactory`` from Paste config
    settings. Only settings prefixed with "mongo.sessions" will be inspected
    and, if needed, coerced to their appropriate types (for example, casting
    the ``timeout`` value as an `int`).

    Parameters:

    ``settings``
    A dict of Pyramid application settings
    """
    options = _parse_settings(settings)
    return MongoSessionFactory(**options)

from datetime import datetime, timedelta

import mongoengine as ma
from random import getrandbits

from mist.core import config
from mist.core.helpers import get_rand_token
from mist.core.model import User



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
ma.connect(host=congig.MONGO_URI, db="mist2")
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



def MongoSessionFactory(
    cookie_name='session',
    max_age=None,
    path='/',
    domain=None,
    secure=False,
    httponly=False,
    timeout=1200,
    reissue_time=0,
    set_on_exception=True,
    secret="SuperPass"
    ):

    @implementer(ISession)
    class MongoSession(dict):

        # configuration parameters
        _cookie_name = cookie_name
        _cookie_max_age = max_age if max_age is None else int(max_age)
        _cookie_path = path
        _cookie_domain = domain
        _cookie_secure = secure
        _cookie_httponly = httponly
        _cookie_on_exception = set_on_exception
        _timeout = timeout if timeout is None else int(timeout)
        _reissue_time = reissue_time if reissue_time is None else int(reissue_time)
        _secret = secret 

        def __init__(self, request):
            self.request = request

               # attempt to retrieve a session_id from the cookie
            session_id_from_cookie = _get_session_id_from_cookie(
                request=request,
                cookie_name=cookie_name,
                secret=_secret
                )
            try:
                session = SessionToken.objects.get(token=session_id_from_cookie)
                session_cookie_was_valid = session.is_valid()
                self.new = False

            except:
                session = SessionToken()
                session_cookie_was_valid = False
                session_id = session.token
                self.new = True

            self.created = session.created
            self.invalidate = session.revoke
            self.changed = session.save
            self.save = session.save


                

            set_cookie = functools.partial(
                _set_cookie,
                cookie_name=cookie_name,
                cookie_max_age=cookie_max_age,
                cookie_path=cookie_path,
                cookie_domain=cookie_domain,
                cookie_secure=cookie_secure,
                cookie_httponly=cookie_httponly,
                secret=secret,
                )
            delete_cookie = functools.partial(
                _delete_cookie,
                cookie_name=cookie_name,
                cookie_path=cookie_path,
                cookie_domain=cookie_domain,
                )
            cookie_callback = functools.partial(
                _cookie_callback,
                session_cookie_was_valid=session_cookie_was_valid,
                cookie_on_exception=cookie_on_exception,
                set_cookie=set_cookie,
                delete_cookie=delete_cookie,
                )
            request.add_response_callback(cookie_callback)

            # return session






    return MongoSession




def _set_cookie(
    request,
    response,
    cookie_name,
    cookie_max_age,
    cookie_path,
    cookie_domain,
    cookie_secure,
    cookie_httponly,
    secret,
    ):
    cookieval = signed_serialize(request.session.session_id, secret)
    response.set_cookie(
        cookie_name,
        value=cookieval,
        max_age=cookie_max_age,
        path=cookie_path,
        domain=cookie_domain,
        secure=cookie_secure,
        httponly=cookie_httponly,
        )


def _delete_cookie(response, cookie_name, cookie_path, cookie_domain):
    response.delete_cookie(cookie_name, path=cookie_path, domain=cookie_domain)


def _cookie_callback(
    request,
    response,
    session_cookie_was_valid,
    cookie_on_exception,
    set_cookie,
    delete_cookie,
    ):
    """Response callback to set the appropriate Set-Cookie header."""
    session = request.session
    if session._invalidated:
        if session_cookie_was_valid:
            delete_cookie(response=response)
        return
    if session.new:
        if cookie_on_exception is True or request.exception is None:
            set_cookie(request=request, response=response)
        elif session_cookie_was_valid:
            # We don't set a cookie for the new session here (as
            # cookie_on_exception is False and an exception was raised), but we
            # still need to delete the existing cookie for the session that the
            # request started with (as the session has now been invalidated).
            delete_cookie(response=response)




