import sys
import storage
from StringIO import StringIO

import utils
from utils import KeplerEngine, WorkflowCache

from java.lang import System
from java.io import ByteArrayOutputStream, PrintStream

import ptolemy
from ptolemy.actor import Manager, CompositeActor, Actor, Director
from ptolemy.moml import MoMLParser, Vertex
from ptolemy.moml.filter import RemoveGraphicalClasses
from ptolemy.kernel import Relation, Port
from ptolemy.vergil.kernel.attributes import TextAttribute
from ptolemy.vergil.basic import KeplerDocumentationAttribute
from ptolemy.actor.gui import SizeAttribute
from org.kepler.sms import SemanticType
from org.kepler.moml import NamedObjId

def list():
    return {'workflows':storage.listWorkflows()}

def getWorkflow(id):
    print 'geting workflow id: %s' % id
    return {'moml': storage.getWorkflowMoML(id)}

def getCompositeActor(id, actor):
    return {'id': id, 'actor': actor}

def init():
    #MoMLParser.addMoMLFilter(RemoveGraphicalClasses())
    pass

def openWorkflow(id):
    print 'opeining workflow id: %s' % id
    return WorkflowCache().getModel(id)
    

def getVisualStructure(id, path=''):
    """
    NOTE: i am assuming that everything has a unique name, if this is untrue it will cause problems
                add: vertices are only unique per relations, so add the relation name to each vertex
     """
    model = WorkflowCache().getModel(id)
    rdic = {'actors':[], 'vertices':[], 'links':[], 'annotations':[], 'ports':[]}
    if path:
        crumbs = []
        path = path.split('/')
        tp = ''
        for p in path:
            if p != '':
                crumbs.append({'name':p, 'path':'%s/%s' % (tp, p)})
                tp = crumbs[-1]['path']
                for i in model.containedObjectsIterator():
                    if i.getName() == p:
                        model = i
        rdic['crumbs'] = crumbs[:-1]
        print crumbs
    rdic['name'] = model.getName()
    if model.getName() != id:
        rdic['base_workflow'] = id
    iterator = model.containedObjectsIterator()
    for i in iterator:
        if isinstance(i, SizeAttribute):
            print i.getToken().toString()
            rdic['canvas'] = utils.locationToDict(i.getToken().toString())
        elif isinstance(i, Actor):
            a = {}
            a['name'] = i.getName()
            a['location'] = utils.locationToDict(i.getAttribute('_location').getValueAsString())
            a['inputports'] = [utils.uniqueNameForPort(p) for p in i.inputPortList()]
            a['outputports'] = [utils.uniqueNameForPort(p) for p in i.outputPortList()]
            if isinstance(i, CompositeActor):
                a['composite'] = True
            rdic['actors'].append(a)
        elif isinstance(i, Director):
            rdic['director'] = {'name':i.getName(), 'location':utils.locationToDict(i.getAttribute('_location').getValueAsString()) }
        elif isinstance(i, Relation):
            # get the vertices of this relation, if any
            vertex = utils.getVertexFromRelation(i)
            if vertex:
                utils.addToListIfNotAlreadyThere(rdic['vertices'], vertex)
            ports = []
            relations = []
            for o in i.linkedObjectsList():
                if isinstance(o, Port):
                    ports.append(o)
                elif isinstance(o, Relation):
                    relations.append(o)
            if not vertex and not relations and len(ports) is 2:
                # simple port -> port connection
                utils.addToListIfNotAlreadyThere(rdic['links'], utils.sortList([utils.uniqueNameForPort(p) for p in ports]))
            elif vertex and not relations:
                # there is a vertex in this relation, so each port connects to this vertex
                for port in ports:
                    utils.addToListIfNotAlreadyThere(rdic['links'], utils.sortList([utils.uniqueNameForPort(port), vertex['name']]))
            elif vertex and relations:
                # this means there is a vertex -> vertex link
                for r in relations:
                    vertex2 = utils.getVertexFromRelation(r)
                    if not vertex2:
                        raise(Exception('should be a vertex to vertex link, but the linking relation doesn\'t have a vertex. i=%s, r=%s' % (i, r)))
                    utils.addToListIfNotAlreadyThere(rdic['links'], utils.sortList([vertex['name'], vertex2['name']]))
                for port in ports:
                    utils.addToListIfNotAlreadyThere(rdic['links'], utils.sortList([utils.uniqueNameForPort(port), vertex['name']]))
            else:
                raise(Exception('unable to handle relation %s' % i))
        elif isinstance(i, TextAttribute):
            annotation = {'text': i.text.getExpression()}
            aparams = [i for i in i.containedObjectsIterator()]
            textsize = [p for p in aparams if p.getName() == 'textSize']
            if textsize:
                annotation['text_size'] = textsize[0].getToken()
            ff = [p for p in aparams if p.getName() == 'fontFamily']
            if ff:
                annotation['font_family'] = ff[0].getToken().stringValue()
            col = [p for p in aparams if p.getName() == 'textColor']
            if col:
                annotation['text_color'] = utils.floatcolortohex(col[0].getToken().toString()[1:-1].split(', '))
            bold = [p for p in aparams if p.getName() == 'bold']
            if bold and bold[0].getToken().booleanValue():
                annotation['bold'] = 'true'
            italic = [p for p in aparams if p.getName() == 'italic']
            if italic and italic[0].getToken().booleanValue():
                annotation['italic'] = 'true'
            location = [p for p in aparams if p.getName() == '_location']
            if location:
                annotation['location'] = utils.locationToDict(location[0].getValueAsString())
            rdic['annotations'].append(annotation)
        elif isinstance(i, Port):
            port = {'name': i.getName(), 'id' : utils.uniqueNameForPort(i), 'location': utils.locationToDict(i.getAttribute('_location').getValueAsString())}
            if i.isInput():
                port['input'] = True
            if i.isOutput():
                port['output'] = True
            if i.isMultiport():
                port['multiport'] = True
            rdic['ports'].append(port)
        else:
            print 'unhandled object: %s' % i
    return rdic

def getActorProperties(id, path):
    model = WorkflowCache().getModel(id)
    iterator = model.containedObjectsIterator()
    path = path.split('/')
    for p in path:
        m = [i for i in model.containedObjectsIterator() if i.getName() == p]
        if m:
            model = m[0]
    attribs = [i for i in model.attributeList() if not i.getName().startswith('_')]
    properties = []
    for a in attribs:
        if isinstance(a, KeplerDocumentationAttribute):
            pass
        elif isinstance(a, SemanticType):
            pass
        elif isinstance(a, NamedObjId):
            pass
        else:
            try:
                attr = {'name':a.getName(), 'id':a.getFullName(), 'value':a.getValueAsString()}
                properties.append(attr)
            except:
                pass
    return properties
        

def executeWorkflow(id):

    moml = storage.getWorkflowMoML(id)
        
    parser = MoMLParser()
    toplevel = parser.parse(moml)
    manager = Manager(toplevel.workspace(), "jythonManager")
    toplevel.setManager(manager)
    
    bso = ByteArrayOutputStream()
    bse = ByteArrayOutputStream()
    defaultout = System.out
    defaulterr = System.err
    System.setOut(PrintStream(bso))
    System.setErr(PrintStream(bse))
    try:
        print 'executing workflow...'
        manager.execute()
        success = True
        print '...execution successful'
    except Exception, e:
        print '...execution failed'
        success = False
        
    standardout = bso.toString()
    standarderr = bse.toString()
    System.setOut(defaultout)
    System.setErr(defaulterr)
    return {'stdout': standardout, 'stderr': standarderr, 'success': success }