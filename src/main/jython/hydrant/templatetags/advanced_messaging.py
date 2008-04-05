from django import template
from django.template import Library

register = Library()

def do_advanced_messaging(parser, token):
    return AdvancedMessaging()
register.tag('setup_advanced_messaging', do_advanced_messaging)

class AdvancedMessaging(template.Node):
    def __init__(self):
        pass
    def render(self, context):
        om = context['messages']
        nm = []
        for msg in om:
            try:
                d = eval(msg)
                if isinstance(d, dict):
                    nm.append(d)
                else:
                    raise SyntaxError
            except (NameError, SyntaxError):
                nm.append({'message': msg, 'type':'MESSAGE'})
        context['messages'] = nm
        return ''
