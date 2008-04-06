from django.template import Library
import md5, traceback
from django.contrib.auth.models import User
register = Library()

def gravatar_url(user, size=64, secure=True):
    """
    Returns the url to retrieve a users gravatar
    """
    if secure:
        u = 'https://secure.gravatar.com/avatar/'
    else:
        u = 'http://www.gravatar.com/avatar/'
    try:
        if isinstance(user, (str, unicode)):
            u += md5.md5(user).hexdigest()
        elif isinstance(user, User):
            u += md5.md5(user.email).hexdigest()
    except:
        # if we have an error just ignore it. (may want to log it)
        pass
    u += '?s=%s' % size
    return u
gravatar_url = register.simple_tag(gravatar_url)
