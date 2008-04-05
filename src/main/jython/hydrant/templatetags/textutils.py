from django.template import Library

register = Library()

def replace_spaces(text, replacement='_____'):
    return text.replace(' ', replacement)
register.filter('replace_spaces', replace_spaces)

def split(str,splitter):
    return str.split(splitter)
register.filter('split', split)
