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
