from django.db import models
from django.db import models
from django.core.cache import cache

import libxml2, string, re, dircache
from kepler.backend import storage

def maketuple(s):
    """ converts a string location to a tuple """
    
    return tuple(s[1:-1].replace(' ','').split(','))

def loctodict(s):
    """ converts location string from kepler workflows into a {'x':x, 'y':y} dict """
    t = tuple(s[1:-1].replace(' ','').split(',')) #maketuple
    return {'x':t[0], 'y':t[1]}

def getEntity(context):
    """ get the basic structure of an entity     
    """
    
  
    floatcolortohex = lambda s: ('%2x%2x%2x' % ( int(255 * float(s[0])), int(255 * float(s[1])), int(255 * float(s[2])) )).replace(' ', '0')
    loctotuple = lambda s: maketuple(s)
    actorfromport = lambda s: s.split('.')[0]
    cameltowide = lambda s: ' '.join(re.compile('[A-Z]+[a-z]+').findall(s))
    
    entity = {}
    
    # get the name of the workflow
    entity['name'] = context.prop('name')
    
    # first get the director
    d = context.xpathEval("""property[contains(@name,'Director')]""")
    if len(d) > 0:
        director = {}
        director['name'] = d[0].prop('name')
        director['location'] = loctodict(d[0].xpathEval("""property[@name='_location']""")[0].prop('value'))
        entity['director'] = director
     
    annotations = []
    for a in context.xpathEval("""property[@class='ptolemy.vergil.kernel.attributes.TextAttribute']"""):
        annotation = {}
        annotation['location'] = loctodict(a.xpathEval("""property[@name='_location']""")[0].prop('value'))
        annotation['text_size'] = a.xpathEval("""property[@name='textSize']""")[0].prop('value')
        annotation['text_color'] = floatcolortohex(maketuple(a.xpathEval("""property[@name='textColor']""")[0].prop('value')))
        annotation['font_family'] = cameltowide(a.xpathEval("""property[@name='fontFamily']""")[0].prop('value'))
        annotation['bold'] = a.xpathEval("""property[@name='bold']""")[0].prop('value')
        annotation['italic'] = a.xpathEval("""property[@name='italic']""")[0].prop('value')
        annotation['text'] = a.xpathEval("""property[@name='text']""")[0].prop('value')
        annotations.append(annotation)
    entity['annotations'] = annotations
    
    actors = []
    compositeactors = []
    for e in context.xpathEval("""entity"""):
        actor = {}
        actor['name'] = e.prop('name')
        actor['location'] = loctodict(e.xpathEval("""property[@name='_location']""")[0].prop('value'))
        actor['ports'] = []
        try:
            e.prop('class').index('CompositeActor')
            compositeactors.append(actor)
        except ValueError:        
            actors.append(actor)
    entity['actors'] = actors
    entity['compositeactors'] = compositeactors
    
    relations = []
    vertices = []
    for r in context.xpathEval("""relation"""):
        relation = {}
        relation['name'] = r.prop('name')
        localvertices = []
        for v in r.xpathEval("""vertex"""):
            vertex = {}
            vertex['name'] =relation['name'] + '.' + v.prop('name')
            vertex['location'] = loctodict(v.prop('value'))
            vertices.append(vertex)
            localvertices.append(vertex)
        relation['vertices'] = localvertices
        relations.append(relation)
    entity['vertices'] = vertices
    #entity['relations'] = relations

    links = []
    for l in context.xpathEval("""link"""):
        link = {}
        if l.prop('port') == None:
            link['relation1'] = l.prop('relation1')
            link['relation2'] = l.prop('relation2')
        else:
            link['port'] = l.prop('port')
            link['relation'] = l.prop('relation')
        links.append(link)
    #entity['links'] = links

    connections = []
    # modify the links list
    links = [[l, False] for l in links]
    for l in links:
        link = l[0]
        if l[1] is False:
            connection = {}
            try:
#                actor = actorfromport(link['port'])
#                i = [i for i in range(0, len(entity['actors'])) if entity['actors'][i]['name'] == actor]
#                if i:
#                    i = i[0]
#                    entity['actors'][i]['ports'].append(link['port'])
#                    portname = link['port']
#                else:
#                    portname = actor
#                
#                connection['start'] = portname
                connection['start'] = actorfromport(link['port'])
                for r in relations:
                    if r['name'] == link['relation']:
                        if len(r['vertices']) > 0:
                            connection['end'] = r['vertices'][0]['name']
                            # TODO: what if there is more than one vertex in a relation?
                        else:
                            for l2 in links:
                                link2 = l2[0]
                                if link2 != link and link2['relation'] == r['name']:
                                    connection['end'] = actorfromport(link2['port'])
                                    l2[1] = True
                                    break
                            # TODO: should we check to make sure a relation was found?
                        break
            except KeyError:
                for r in relations:
                    if r['name'] == link['relation1']:
                        if len(r['vertices']) > 0:
                            connection['start'] = r['vertices'][0]['name']
                    elif r['name'] == link['relation2']:
                        if len(r['vertices']) > 0:
                            connection['end'] = r['vertices'][0]['name']
            l[1] = True
            connections.append(connection)
    entity['connections'] = connections
    
    ports = []
    for p in context.xpathEval("""port"""):
        port = {}
        port['name'] = p.prop('name')
        port['location'] = loctodict(p.xpathEval("""property[@name='_location']""")[0].prop('value'))
        ports.append(port)
    entity['ports'] = ports
#    relations = {}
#    vertices = []
#    for r in context.xpathEval("""relation"""):
#        relations[r.prop('name')] = []
#        for v in r.xpathEval("""vertex"""):
#            vertex = {}
#            vertex['name'] = v.prop('name')
#            vertex['location'] = loctodict(v.prop('value'))
#            vertices.append(vertex)
#    
#    connections = []
#    for l in links:
#        connection = {}
#        connection['start'] = l['port'].split('.')[0]
#        relation = l['relation']
#        relations
#        connection['end'] = 
    
    return entity

# Create your models here.
def getWorkflow(workflow_id):
    """ get the basic structure of a workflow """

    return getCompositeActor(workflow_id)

def getCompositeActor(workflow_id, path=''):
    #/home/jc124742/workspace/JAINISWorkflow/workflows/jainis-JCU-tester.xml
    
    # the return dict
    entity = {}
    
    context = _getWorkflowContext(workflow_id)
    sections = path.split('/')
    xpath = '/'.join(['entity' for i in range(0, len(sections)-1)])
    
    # get the composite actor structure
    actor = path and context.xpathEval("""%s[@name="%s"]""" % (xpath, sections[-1]))[0] or context
    entity = getEntity(actor)

    # get all the workflow parameters
    workflow_properties = _getProperties(actor)
    # add the canvas size to the return dict
    entity['canvas'] = loctodict([i for i in workflow_properties['hidden'] if i['name']=='_vergilSize'][0]['value'])

    if (path != ''):
        # set the base_workflow parameter
        entity['base_workflow'] = context.prop('name')
        # build the crumbs
        crumbs = []
        for i in range(2, len(sections)):
            crumbs.append({'name':sections[i-1], 'path': '/'.join(sections[:i])})
        entity['crumbs'] = crumbs
                   
    return entity

def _getWorkflowContext(workflow_id):
    return libxml2.parseDoc(storage.readWorkflow(workflow_id)).xpathNewContext().xpathEval('/entity')[0]

def _getProperties(context):
    properties = {'visible': [], 'hidden': []}
    for p in context.xpathEval("""property[not(starts-with(@name,'_'))]"""):
        if p.prop('value') != None and p.prop('name') != None:
            property = {'name': p.prop('name'), 'value': p.prop('value')}
            properties['visible'].append(property)
    for p in context.xpathEval("""property[starts-with(@name,'_')]"""):
        if p.prop('value') != None and p.prop('name') != None:
            property = {'name': p.prop('name'), 'value': p.prop('value')}
            properties['hidden'].append(property)
    return properties

def getProperties(workflow, path, type='actor'):
    context = _getWorkflowContext(workflow)
    sections = path.split('/')
    try:
        xpath = '/'.join(['entity' for i in range(0, len(sections))])
        actorxpath = context.xpathEval("""%s[@name="%s"]""" % (xpath, sections[-1]))[0]
    except:
        # assume that we're being asked for the properties of a director
        tmp = ['entity' for i in range(0, len(sections)-1)]
        tmp.extend(['property'])
        xpath = '/'.join(tmp)
        actorxpath = context.xpathEval("""%s[@name="%s"]""" % (xpath, sections[-1]))[0]
        
    namespace = context.prop('name') + '.' + path.replace('/', '.')
    
    return {'name':sections[-1], 'properties': _getProperties(actorxpath)['visible'], 'namespace': namespace}
