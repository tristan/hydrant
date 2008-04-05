from django.template import Library

register = Library()

def first_half_of_list(l):
    return l[:len(l)/2]
register.filter('first_half_of_list', first_half_of_list)

def last_half_of_list(l):
    return l[len(l)/2:]
register.filter('last_half_of_list', last_half_of_list)

def split_list(l):
    yield first_half_of_list(l)
    yield last_half_of_list(l)
register.filter('split_list', split_list)
