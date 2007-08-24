from django import template
from django.template import resolve_variable
from django.template.defaultfilters import linebreaks, escape

register = template.Library()

@register.tag(name="debug_table")
def do_debug_table(parser, token):
    try:
        tag_name, debugdict = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]
    return DebugTableNode(debugdict)

TABLE_STYLE="border-width: 1px; border-style: outset; border-spacing: 0px;"

class DebugTableNode(template.Node):
    def __init__(self, debugdict):
        self.debugdict = debugdict
    def render(self, context):
        dd = resolve_variable(self.debugdict, context)
        return self.maketable(dd)
    def maketable(self, dd):
        try:
            if isinstance(dd, type([])):
                ret = '[ '
                for d in dd:
                    print d
                    ret = '%s, %s' % (ret, self.maketable(d))
                return '%s ]' % ret
            elif isinstance(dd, type(())) and (len(dd) is not 2):
                ret = '( '
                for d in dd:
                    ret = '%s, %s' % (ret, self.maketable(d))
                return '%s )' % ret
            elif isinstance(dd, type(())):
                key = dd[0]
                value = dd[1]
                ret = '<table style="%s">\n' % TABLE_STYLE
                ret = '%s<tr style="%s"><td style="%s">\n%s\n</td><td style="%s">' % (ret, TABLE_STYLE, TABLE_STYLE, key, TABLE_STYLE)
                ret = '\n%s%s\n' % (ret, self.maketable(value))
                ret = '%s</td></tr>\n' % ret
                return '%s</table>\n' % ret
            elif isinstance(dd, type({})):
                ret = '<table style="%s">\n' % TABLE_STYLE
                for key in dd.keys():
                    ret = '%s<tr style="%s"><td style="%s">\n%s\n</td><td style="%s">' % (ret, TABLE_STYLE, TABLE_STYLE, key, TABLE_STYLE)
                    ret = '\n%s%s\n' % (ret, self.maketable(dd.get(key)))
                    ret = '%s</td></tr>\n' % ret
                return '%s</table>\n' % ret
            else:
                return ('%s' % dd).replace('\n', '<br/>')
        except Exception, e:
            return '<p>ERROR.</p><p>%s</p><p>%s</p>' % (e, dd)