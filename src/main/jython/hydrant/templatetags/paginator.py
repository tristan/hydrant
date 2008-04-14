from django.template import Library

register = Library()

def paginate(page):
    pages = range(1, page.paginator.num_pages+1)
    pages_left = pages[:page.number][-3:]
    pages_right = pages[page.number:(page.number+2+(3-len(pages_left)))]
    if len(pages_right) < 3:
        pages_left = pages[:page.number][-(3+(2-len(pages_right))):]
    pages_left.extend(pages_right)
    return pages_left
register.filter('paginate', paginate)
