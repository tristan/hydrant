try:
    set
except NameError:
    from sets import Set as set   # Python 2.3 fallback

from django import newforms as forms
from django.newforms.util import flatatt
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

    def crap_render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        final_attrs = self.build_attrs(attrs, name=name)
        print final_attrs
        id_ = attrs != None and attrs.get('id') or 'id_%s' % name
        output = []
        output.append(u'<div class="selector">')
        output.append(u'<div class="selector-available">')
        output.append(u'<h2>Available %s</h2>' % self.verbose_name)
        output.append(u'<p class="selector-filter">')
        output.append(u'<img src="%simg/kepler/selector-search.gif" alt="Search"/>' % settings.MEDIA_URL)
        output.append(u'<input id="%s" type="text"/>' % id_)
        output.append(u'</p>')
        output.append(u'<select id="%s_from" class="filtered" multiple="multiple">' % (id_,))
        selected_vals = set([force_unicode(v) for v in value])
        for v, l in chain(self.choices, choices):
            v = force_unicode(v)
            output.append(u'<option value="%s"%s>%s</option>' % (escape(v), v in selected_vals and ' selected="selected"' or '', escape(force_unicode(l))))
        output.append(u'</select>')
        output.append(u'<a class="selector-chooseall" href="#">Choose all</a>')
        output.append(u'</div>')
        output.append(u'<ul class="selector-chooser">')
        output.append(u'<li><a class="selector-add" href="javascript: (function() {SelectBox.move("%s_from","%s_to");})()">Add</a></li>' % (id_, id_))
        output.append(u'<li><a class="selector-remove" href="#">Remove</a></li>')
        output.append(u'</ul>')
        output.append(u'<div class="selector-chosen">')
        output.append(u'<h2>Chosen %s</h2>' % self.verbose_name)
        output.append(u'<p class="selector-filter">')
        output.append(u'Select your choice(s) and click')
        output.append(u'<img src="%simg/kepler/selector-add.gif" alt="Add"/>' % settings.MEDIA_URL)
        output.append(u'</p>')
        output.append(u'<select id="%s_to" class="filtered" multiple="multiple"></select>')
        output.append(u'<a class="selector-clearall" href="#">Clear all</a>')
        output.append(u'</div>')
        output.append(u'</div>')
        output.append(u'<script type="text/javascript">')
        output.append(u'SelectBox.init("%s_from");' % id_)
        output.append(u'SelectBox.init("%s_to");' % id_)
        output.append(u'</script>')
        return mark_safe(u'\n'.join(output))
