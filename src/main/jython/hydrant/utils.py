import xmlrpclib
import settings
from django.core.urlresolvers import reverse

def submit_ticket(workflow, user, message):
    subject = 'Problem with workflow %s (%s)' % (
        workflow.name,
        workflow.pk,
        )
    text = """There is a problem with workflow [%s %s].[[br]]Reporter: [%s %s][[br]]User message:[[br]]%s""" % (
        'http://quiver.jcu.edu.au:8001%s' % reverse('workflow', args=(workflow.pk,)),
        workflow.name,
        'http://quiver.jcu.edu.au:8001%s' % reverse('profile', args=(user.username,)),
        user.username,
        message,
        )

    trac_url = getattr(settings, 'TRAC_URL', None)
    trac_user = getattr(settings, 'TRAC_USER', None)
    trac_pass = getattr(settings, 'TRAC_PASSWORD', None)
    java_truststore = getattr(settings, 'JAVA_TRUSTSTORE', None)

    if trac_url == None:
        raise 'TRAC_URL is not set'
    if not trac_url.startswith('http'):
        raise 'TRAC_URL should start with http:// or https://'

    creds = ''
    if trac_user != None:
        creds = '%s%s@' % (
            trac_user,
            trac_pass != None and ':%s' % trac_pass or '',
            )

    end = trac_url[trac_url.index("://")+3:]
    url = trac_url[:trac_url.index("://")+3]

    url += creds
    url += end
    url += creds != '' and 'login/xmlrpc' or 'xmlrpc'

    if java_truststore:
        import java.lang.System
        java.lang.System.setProperty("javax.net.ssl.trustStore", java_truststore)

    server = xmlrpclib.ServerProxy(url)
    server.ticket.create(subject,
                         text,
                         {'sprint':'',
                          'milestone':'',
                          'component':'hydrant',
                          'cc':'jc124742',
                          }
                         )
