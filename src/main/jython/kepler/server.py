import dircache, sys, re
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import views

urls = (
    {'name':'list', 're': re.compile(r'^/list/$'), 'args':()}, 
    #{'name':'getWorkflow', 're': re.compile(r'^/workflow/([\.\w_-]+)/$'), 'args': ('id',)},
    {'name':'properties', 're': re.compile(r'^/properties/([\.\w_-]+)/([\w\ /-]+)/$'), 'args': ('id','path')},
    {'name':'structure', 're': re.compile(r'^/structure/([\.\w_-]+)/([\w/-]+)/$'), 'args': ('id','path')},
    {'name':'structure', 're': re.compile(r'^/structure/([\.\w_-]+)/$'), 'args': ('id',)},
    #{'name':'getCompositeActor', 're': re.compile(r'^/workflow/([\w_-]+)/composite([\w/-]+)/$'), 'args': ('id','actor')},
    {'name':'executeWorkflow', 're': re.compile(r'^/exec/([\.\w_-]+)/$'), 'args': ('id',)},
    {'name':'open', 're': re.compile(r'^/open/([\.\w_-]+)/$'), 'args': ('id',)},
    #{'name':'getActors', 're': re.compile(r'^/workflow/([\.\w_-]+)/actors/$'), 'args': ('id',)},
    #{'name':'getPorts', 're': re.compile(r'^/workflow/([\.\w_-]+)/actor/([\.\w\ /_-]+)/ports/$'), 'args': ('workflowId','actorpath')},
)

class MyHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        try:
            request_url = self.raw_requestline.split(' ')[1]
            request_url = (request_url[-1] == '/') and request_url or '%s/' % request_url
            request_url = request_url.replace('%20', ' ')
            
            for d in urls:
                if d['re'].match(request_url):
                    args = d['re'].split(request_url)[1:-1]
                    
                    # check if the number of args match
                    if len(d['args']) != len(args):
                        self.send_error(500, 'invalid number of args. expected %s got %s' % (len(d['args']), len(args)));
                        return

                    result = getattr(views, d['name'])(*tuple(args))
                    # make result json compatible
                    result = str(result).replace('\'', '"')
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write('%s' % result)
                    return
            self.send_error(404, 'no matching regexp')
            return
        except IOError:
            self.send_error(404, 'file not found')
        except IndexError, e:
            print e
            self.send_error(500, 'invalid requestline')
        
    def do_POST(self):
        try:
            self.send_response(301)
            self.wfile.write('<html><body><h1>POST!</h1></body></html>')
        except:
            pass

def runserver():
    try:
        server = HTTPServer(('0.0.0.0', 8001), MyHandler)
        print 'started server: %s' % server
        server.serve_forever()
    except KeyboardInterrupt:
        print 'shutting down'
        server.socket.close()