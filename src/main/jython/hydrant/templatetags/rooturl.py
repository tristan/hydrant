from django.template import Library

register = Library()

def root_url():
    """
    Returns the string contained in the setting ROOT_URL property.
    """
    try:
        from django.conf import settings
    except ImportError:
        return ''
    return settings.ROOT_URL
root_url = register.simple_tag(root_url)
