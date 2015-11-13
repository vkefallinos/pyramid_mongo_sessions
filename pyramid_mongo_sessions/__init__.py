import functools

from pyramid.session import (
    signed_deserialize,
    signed_serialize,
    )

from compat import cPickle
from connection import get_default_connection
from session import MongoSession
from util import (
    _generate_session_id,
    _parse_settings,
    get_unique_session_id,
    )


from connection import get_rand_token



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

def MongoSessionFactory(
    secret,
    timeout=1200,
    cookie_name='session',
    cookie_max_age=None,
    cookie_path='/',
    cookie_domain=None,
    cookie_secure=False,
    cookie_httponly=True,
    cookie_on_exception=True,
    url=None,
    host='localhost',
    port=27017,
    db="sessions",
    password=None,
    socket_timeout=None,
    connection_pool=None,
    charset='utf-8',
    errors='strict',
    unix_socket_path=None,
    client_callable=None,
    serialize=cPickle.dumps,
    deserialize=cPickle.loads,
    id_generator=_generate_session_id,
    ):

    def factory(request, new_session_id=get_unique_session_id):
        mongo_options = dict(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=socket_timeout,
            connection_pool=connection_pool,
            charset=charset,
            errors=errors,
            unix_socket_path=unix_socket_path,
            )

        # an explicit client callable gets priority over the default
        mongo_session = client_callable(request, **mongo_options) \
            if client_callable is not None \
            else get_default_connection(request, url=url, **mongo_options)

        # attempt to retrieve a session_id from the cookie
        session_id_from_cookie = _get_session_id_from_cookie(
            request=request,
            cookie_name=cookie_name,
            secret=secret,
            )

        new_session = functools.partial(
            new_session_id,
            mongo_session=mongo_session,
            timeout=timeout,
            serialize=serialize,
            generator=id_generator,
            )

        if session_id_from_cookie and mongo.exists(session_id_from_cookie):
            session_id = session_id_from_cookie
            session_cookie_was_valid = True
        else:
            session_id = new_session()
            session_cookie_was_valid = False

        session = MongoSession(
            mongo_session=mongo_session,
            session_id=session_id,
            new=not session_cookie_was_valid,
            new_session=new_session,
            serialize=serialize,
            deserialize=deserialize,
            )

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

        return session

    return factory
