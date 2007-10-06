
def print_request_info(request):
    print '-------------------GET--------------------'
    print request.GET
    print '-------------------POST-------------------'
    print request.POST
    print '------------------COOKIE------------------'
    print request.COOKIES
    print '------------------------------------------'
