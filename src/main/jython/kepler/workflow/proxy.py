from ptolemy.actor import Manager, CompositeActor, Actor, Director
from ptolemy.moml import MoMLParser, Vertex
from ptolemy.moml.filter import RemoveGraphicalClasses
from ptolemy.kernel import Relation, Port, Entity
from ptolemy.vergil.kernel.attributes import TextAttribute
from ptolemy.vergil.basic import KeplerDocumentationAttribute
from ptolemy.actor.gui import SizeAttribute
from org.kepler.sms import SemanticType
from org.kepler.moml import NamedObjId

import java.lang.Object
import java.lang.Class
import ptolemy.data.IntMatrixToken

import utils
from utils import validateMoML


import ptolemy.data.Token
class __token_proxy__(object):
    """
    """
    def __init__(self, obj):
        if not isinstance(obj, ptolemy.data.Token):
            raise('must be a Token type')
        self.__obj = ojb


import ptolemy.data.DoubleToken
class __float_based_attribute_proxy__(object):
    """
    there is no FloatToken type in kepler, and no double type in python
    but they are mixable
    """
    def __init__(self, javaobj):
        self.javaobj = javaobj
    def get(self):
        return self.javaobj.getToken().doubleValue()
    def set(self, x):
        t = ptolemy.data.DoubleToken(x)
        self.javaobj.setToken(t)

    def __repr__(self):
        return str(self.get())

import ptolemy.data.StringToken
class __string_based_attribute_proxy__(object):
    def __init__(self, javaobj):
        self.javaobj = javaobj
    def get(self):
        return self.javaobj.getExpression()
    def set(self, x):
        self.javaobj.setExpression(x)
    def __repr__(self):
        return self.get()

import ptolemy.data.ArrayToken
class __array_based_attribute_proxy__(object):
    def __init__(self, javaobj):
        self.javaobj = javaobj
    def get(self):
        r = []
        t = self.javaobj.getToken()
        for i in range(t.length()):
            r.append(t.getElement(0))

def lazy_proxy_assign(obj):
    if isinstance(obj, (Actor, Director)):
        return ModelProxy(obj)
    if hasattr(obj, 'getToken'):
        t = obj.getToken()
        if isinstance(t, ptolemy.data.DoubleToken):
            return __float_based_attribute_proxy__(obj)
        elif isinstance(t, ptolemy.data.StringToken):
            pass # ignore this, since it'll get set in the next pass.. this may be silly tho
    if hasattr(obj, 'getExpression'):
        return __string_based_attribute_proxy__(obj)
    if isinstance(obj, java.lang.Class):
        return obj.__class__.__name__
    else:
        print 'lazy_proxy_ unable to assign %s a proxy' % obj
        return obj

do_parser_once = True

class ModelProxy(object):
    def __init__(self, m):
        try:
            if isinstance(m, basestring):
                self.from_moml(m)
            else:
                self.from_model(m)
            self.has_entities = hasattr(self.model, 'getEntities')
            self.has_attribs = hasattr(self.model, 'getAttributes')
            self.has_ports = hasattr(self.model, 'getPorts')

            #if self.has_entities:
            #    self.entities = [ModelProxy(i) for i in self.model.entityList()]
            #if self.has_attribs:
            #    self.attributes = self.model.attributeList()
            #if self.has_ports:
            #    self.ports = self.model.portList()

            if hasattr(self.model, 'name'):
                self.name = self.model.name
        except Exception, e:
            raise Exception('expects either moml or a model type')
    def from_moml(self, moml):
        global do_parser_once
        if do_parser_once:
            rgc = RemoveGraphicalClasses()
            rgc.remove('ptolemy.vergil.kernel.attributes.TextAttribute')
            MoMLParser.addMoMLFilter(rgc)
            do_parser_once = False
        parser = MoMLParser()

        validateMoML(moml)

        self.model = parser.parse(moml)

    def from_model(self, model):
        if isinstance(model, (Entity, Actor, Director)):
            self.model = model
        else:
            raise Exception('%s : %s' % (type(model), self.model.__class__))

    def __getitem__(self, x):
        global type_mapping
        m = None
        if hasattr(self.model, x):
            m = getattr(self.model, x)
        if not m and self.has_attribs:
            m = self.model.getAttribute(x)
        if not m and self.has_entities:
            m = self.model.getEntity(x)
        if not m and self.has_ports:
            m = self.model.getPort(x)
        if not m:
            return None
        try:
            return lazy_proxy_assign(m)
        except:
            import traceback
            traceback.print_exc()
            return ModelProxy(m)

    def get(self, x):
        return self.__getitem__(x)

    def keys(self):
        d = []
        if self.has_attribs:
            d.extend([i.name for i in self.model.getAttributes()])
        if self.has_entities:
            d.extend([i.name for i in self.model.getEntities()])
        if self.has_ports:
            d.extend([i.name for i in self.model.getPorts()])
        return d

    def __str__(self):
        return '%s {%s}' % (self.model.__class__, self.model.getFullName())

    def __unicode__(self):
        return unicode(self.__str__())

    def set_actor_property(self, path_to_actor, property, value):
        """
        path_to_actor should be a list with the path to the actor
        i.e. for a namespace '.workflow_name.path.to.actor', the resulting list
        should be ['path', 'to', 'actor'].
        if an empty list is found, it is assumed that we're at the level required
        to access the property
        """
        if path_to_actor:
            self.get(path_to_actor[0]).set_actor_property(path_to_actor[1:], property, value)
        else:
            self.get(property).set(value)

    def get_actor_property(self, path_to_actor, property):
        if path_to_actor:
            return self.get(path_to_actor[0]).get_actor_property(path_to_actor[1:], property)
        else:
            m = self.get(property)
            if hasattr(m, 'get'):
                return m.get()
            else:
                return m

    def get_all_actors(self):
        if self.has_entities:
            return [ModelProxy(i) for i in self.model.entityList() if isinstance(i, ptolemy.actor.Actor)]
        else:
            return []

    def get_as_dict(self, path=[], top=True):
        # TODO: NEED ERROR HANDLING

        rdic = {'actors':[], 'vertices':[], 'links':[], 'annotations':[], 'ports':[]}

        # if path is not empty, then traverse the model until the requested actor is found
        if path:
            nextlvl = self.get(path[0])
            rdic = nextlvl.get_as_dict(path[1:], False)
            if top:
                crumbs = []
                tp = ''
                for p in path:
                    if p != '':
                        crumbs.append({'name':p, 'path':'%s%s%s' % (tp, tp and '/' or '', p)})
                        tp = crumbs[-1]['path']
                        #for i in self.model.containedObjectsIterator():
                        #    if i.getName() == p:
                        #        self.model = i
                rdic['crumbs'] = crumbs[:-1]
                print crumbs
            return rdic

        rdic['name'] = self.model.getName()
        #if self.model.getName() != metadata['name']:
        #    rdic['composite'] = True
        if not top:
            rdic['composite'] = True
        iterator = self.model.containedObjectsIterator()
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
                    annotation['text_size'] = textsize[0].getToken().toString()
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

    def get_properties(self, path=[]):
        if path:
            g = self.get(path[0])
            return g.get_properties(path[1:])
        attribs = [i for i in self.model.attributeList() if not i.getName().startswith('_')]
        properties = []
        for a in attribs:
            if isinstance(a, KeplerDocumentationAttribute):
                pass # we don't really care about the doc
            elif isinstance(a, SemanticType):
                pass # we don't need to know the semantic type
            elif isinstance(a, NamedObjId):
                pass # ...
            elif a.getName() == 'class':
                pass # ignore class properties for now
            else:
                try:
                    attr = {'name':a.getName(), 'id':a.getFullName(), 'value':a.getValueAsString()}
                    if hasattr(a, 'getChoices') and a.getChoices():
                        attr['choices'] = list(a.getChoices())
                    properties.append(attr)
                except:
                    pass
        return properties

    def is_actor(self, path):
        """
        returns true if this model is an actor
        returns false for composite actors
        """
        if path:
            g = self.get(path[0])
            return g.is_actor(path[1:])
        if isinstance(self.model, Actor) and not isinstance(self.model, CompositeActor):
            return True
        else:
            return False

    def get_xml(self):
        return self.model.exportMoML()
