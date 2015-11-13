from random import getrandbits
from pyramid.exceptions import ConfigurationError
from pyramid.settings import asbool

def _generate_session_id(bits=256):
    """
    Produces a random 64 character hex-encoded string. The implementation of
    `os.urandom` varies by system, but you can always supply your own function
    in your ini file with:

        redis.sessions.id_generator = my_random_id_generator
    """
    return hex(getrandbits(bits))[2:-1]


def _parse_settings(settings):
    """
    Convenience function to collect settings prefixed by 'redis.sessions' and
    coerce settings to ``int``, ``float``, and ``bool`` as needed.
    """
    keys = [s for s in settings if s.startswith('redis.sessions.')]

    options = {}

    for k in keys:
        param = k.split('.')[-1]
        value = settings[k]
        options[param] = value

    # only required setting
    if 'secret' not in options:
        raise ConfigurationError('redis.sessions.secret is a required setting')

    # coerce bools
    for b in ('cookie_secure', 'cookie_httponly', 'cookie_on_exception'):
        if b in options:
            options[b] = asbool(options[b])

    # coerce ints
    for i in ('timeout', 'port', 'db', 'cookie_max_age'):
        if i in options:
            options[i] = int(options[i])

    # coerce float
    if 'socket_timeout' in options:
        options['socket_timeout'] = float(options['socket_timeout'])

    # check for settings conflict
    if 'prefix' in options and 'id_generator' in options:
        err = 'cannot specify custom id_generator and a key prefix'
        raise ConfigurationError(err)

    # convenience setting for overriding key prefixes
    if 'prefix' in options:
        prefix = options.pop('prefix')
        options['id_generator'] = partial(prefixed_id, prefix=prefix)

    return options



def get_unique_session_id(
    session,
    timeout,
    serialize,
    generator=_generate_session_id,
    ):
    """
    Returns a unique session id after inserting it successfully in Redis.
    """

    return session(timeout=timeout, token= generator())

