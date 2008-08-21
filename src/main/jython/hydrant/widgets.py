try:
    set
except NameError:
    from sets import Set as set   # Python 2.3 fallback

from django import forms
from django.forms.util import flatatt
from django.utils.datastructures import MultiValueDict
from django.utils.text import capfirst
from django.utils.translation import ugettext as _
import settings
from itertools import chain
from django.utils.html import escape
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.safestring import mark_safe

class FilteredSelectMultiple(forms.SelectMultiple):
    """
    A SelectMultiple with a JavaScript filter interface.

    Note that the resulting JavaScript assumes that the SelectFilter2.js
    library and its dependencies have been loaded in the HTML page.
    """
    def __init__(self, verbose_name, is_stacked, attrs=None, choices=()):
        self.verbose_name = verbose_name
        self.is_stacked = is_stacked
        super(FilteredSelectMultiple, self).__init__(attrs, choices)

    def render(self, name, value, attrs=None, choices=()):
        output = [super(FilteredSelectMultiple, self).render(name, value, attrs, choices)]
        output.append(u'<script type="text/javascript">addEvent(window, "load", function(e) {')

        id_ = attrs != None and attrs.get('id') or 'id_%s' % name
        output.append(u'SelectFilter.init("%s", "%s", %s, "%s"); });</script>\n' % \
            (id_, self.verbose_name.replace('"', '\\"'), int(self.is_stacked), settings.MEDIA_URL))
        return mark_safe(u''.join(output))
