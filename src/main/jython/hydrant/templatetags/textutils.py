from django.template import Library

register = Library()

def replace_spaces(text, replacement='_____'):
    return text.replace(' ', replacement)
register.filter('replace_spaces', replace_spaces)

def split(str,splitter):
    return str.split(splitter)
register.filter('split', split)

def truncate_to_len(text, length):
    result = ''
    for i in text.split(' '):
        if len(result) + len(i) > length:
            return result + ' ...'
        result += ' ' + i
    return result
register.filter('truncate_to_len', truncate_to_len)

def px_to_em(px, fontsize=12.8):
    return float(px)/float(fontsize)
register.filter('px_to_em', px_to_em)

import time
import datetime

def timesince_with_secs(dt):
    try:
        return _timesince(dt)
    except:
        return u'unknown'
register.filter('timesince_with_secs', timesince_with_secs)

def timeuntil_with_secs(dt):
    try:
        return _timeuntil(dt)
    except:
        return u'unknown'
register.filter('timeuntil_with_secs', timeuntil_with_secs)


# taken from django.utils.timesince
# modified to return seconds as well
from django.utils.tzinfo import LocalTimezone
from django.utils.translation import ungettext, ugettext

def _timesince(d, now=None):
    """
    Takes two datetime objects and returns the time between d and now
    as a nicely formatted string, e.g. "10 minutes".  If d occurs after now,
    then "0 minutes" is returned.

    Units used are years, months, weeks, days, hours, and minutes.
    Seconds and microseconds are ignored.  Up to two adjacent units will be
    displayed.  For example, "2 weeks, 3 days" and "1 year, 3 months" are
    possible outputs, but "2 weeks, 3 hours" and "1 year, 5 days" are not.

    Adapted from http://blog.natbat.co.uk/archive/2003/Jun/14/time_since
    """
    chunks = (
      (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
      (60 * 60 * 24 * 7, lambda n : ungettext('week', 'weeks', n)),
      (60 * 60 * 24, lambda n : ungettext('day', 'days', n)),
      (60 * 60, lambda n: ungettext('hour', 'hours', n)),
      (60, lambda n: ungettext('minute', 'minutes', n)),
      (1, lambda n: ungettext('second', 'seconds', n))
    )
    # Convert datetime.date to datetime.datetime for comparison
    if d.__class__ is not datetime.datetime:
        d = datetime.datetime(d.year, d.month, d.day)
    if now:
        t = now.timetuple()
    else:
        t = time.localtime()
    if d.tzinfo:
        tz = LocalTimezone(d)
    else:
        tz = None
    now = datetime.datetime(t[0], t[1], t[2], t[3], t[4], t[5], tzinfo=tz)

    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u'0 ' + ugettext('minutes')
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    s = ugettext('%(number)d %(type)s') % {'number': count, 'type': name(count)}
    if i + 1 < len(chunks):
        # Now get the second item
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            s += ugettext(', %(number)d %(type)s') % {'number': count2, 'type': name2(count2)}
    return s

def _timeuntil(d, now=None):
    """
    Like timesince, but returns a string measuring the time until
    the given time.
    """
    if now == None:
        now = datetime.datetime.now()
    return _timesince(now, d)
