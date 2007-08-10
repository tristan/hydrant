from django.db import models
from django.core.cache import cache

import libxml2

def getEntity(context):
    """ get the basic structure of an entity 
        returns a dictionary containing 4 lists:
            director: the workflow director 

            actors: a dictionary of actors 

            relations: a dictionary of relations

            links: a dictionary of links
                
    """
        
    """ converts a string location to a tuple """
    loctotuple = lambda s: tuple(s[1:-1].replace(' ','').split(','))
    loctodict = lambda s: {'x':loctotuple(s)[0],'y':loctotuple(s)[1]}
    actorfromport = lambda s: s.split('.')[0]
    
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
    
    actors = []
    compositeactors = []
    for e in context.xpathEval("""entity"""):
        actor = {}
        actor['name'] = e.prop('name')
        actor['location'] = loctodict(e.xpathEval("""property[@name='_location']""")[0].prop('value'))
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
        print 'port: %s' % (l.prop('port') == None)
        print 'rel1: %s' % (l.prop('relation1') == None)
        if l.prop('port') == None:
            link['relation1'] = l.prop('relation1')
            link['relation2'] = l.prop('relation2')
            print 'rels'
        else:
            link['port'] = l.prop('port')
            link['relation'] = l.prop('relation')
            print 'port'
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
def getWorkflow(workflow):
    """ get the basic structure of a workflow """
# /home/jc124742/workspace/ActorCommons/workflows/plottest.xml
# ctx.xpathEval("""/entity/property[contains(@name,'Director')]/property[@name="_location"]""")
    doc = libxml2.parseFile(workflow)
    context = doc.xpathNewContext()
    # get main workflow entity
    try:
        entity = context.xpathEval("/entity")[0]
        return getEntity(entity)
    except IndexError:
        return {}
    # '/media/workflows/plottest.xml'

import sys

def getCompositeActor(workflow, path):
    #/home/jc124742/workspace/JAINISWorkflow/workflows/jainis-JCU-tester.xml
    doc = libxml2.parseFile(workflow)
    context = doc.xpathNewContext()
    sections = path.split('/')
    xpath = '/entity' * (len(sections)-1)
    entity = {}
   # try:
    actor = context.xpathEval("""%s[@name="%s"]""" % (xpath, sections[-1]))[0]
    entity = getEntity(actor)
    #except Exception:
    #    print sys.exc_info()[0]
    if len(sections) > 3:
        entity['parent'] = "/" + "/".join(sections[1:-1])
    entity['base_workflow'] = sections[1]
    return entity