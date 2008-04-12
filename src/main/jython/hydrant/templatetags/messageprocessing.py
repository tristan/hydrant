from django.template import Library
from django.contrib.auth.models import User
from textutils import truncate_to_len

register = Library()

def _parse(touser, fromuser, user, text, link=False):
    text = text.replace(
        '{{ fromuser }}',
        fromuser == user and 'you' or (
        '%s%s%s' % (link and '<a href="#">' or '',
                    fromuser.username,
                    link and '</a>' or ''
                    ))
        )
    text = text.replace(
        '{{ touser }}',
        touser == user and 'you' or (
        '%s%s%s' % (link and '<a href="#">' or '',
                    touser.username,
                    link and '</a>' or ''
                    ))
        )
    text = text.replace(
        '{{ fromuser|plural }}',
        fromuser == user and 'your' or (
        '%s%s\'s%s' % (link and '<a href="#">' or '',
                    fromuser.username,
                    link and '</a>' or ''
                    ))
        )
    text = text.replace(
        '{{ touser|plural }}',
        touser == user and 'your' or (
        '%s%s\'s%s' % (link and '<a href="#">' or '',
                    touser.username,
                    link and '</a>' or ''
                    ))
        )
    return text

def msgverb(user, msg):
    """
    Returns the url to retrieve a users gravatar
    """
    return _parse(msg.touser, msg.fromuser, user, msg.verb, True)
#register.filter('px_to_em', px_to_em)
msgverb = register.simple_tag(msgverb)


def msgtext(user, msg, truncate=0):
    """
    Returns the url to retrieve a users gravatar
    """
    text = _parse(msg.touser, msg.fromuser, user, msg.text, True)
    if truncate > 0:
        return truncate_to_len(text, truncate)
    else:
        return text
#register.filter('px_to_em', px_to_em)
msgtext = register.simple_tag(msgtext)
