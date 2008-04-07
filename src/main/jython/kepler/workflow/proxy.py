import md5
import traceback

import java.lang.Class
import java.lang.Object
import java.lang.ExceptionInInitializerError
import ptolemy.data.ArrayToken
import ptolemy.data.DoubleToken
import ptolemy.data.IntMatrixToken
import ptolemy.data.StringToken
import ptolemy.kernel.util.StringAttribute
from org.kepler.sms import SemanticType
from org.kepler.moml import NamedObjId
from ptolemy.actor import Manager, CompositeActor, Actor, Director
from ptolemy.actor.gui import SizeAttribute
from ptolemy.actor.sched import Scheduler
from ptolemy.data.type import BaseType
from ptolemy.moml import MoMLParser, Vertex
from ptolemy.moml.filter import RemoveGraphicalClasses
from ptolemy.kernel import Relation, Port, Entity
from ptolemy.vergil.basic import KeplerDocumentationAttribute
from ptolemy.vergil.kernel.attributes import TextAttribute

import utils

# the following classes are getter and setter objects
# for specific types of tokens. these wrap the token
# specific getter and setter methods into simple
# get and set functions such that other code
# doesn't have to waste time figuring out the type
# of the token and have different cases for
# the different types of tokens. Python's dynamic
# typing makes this seemless.

class __float_based_attribute_proxy__(object):

    """ Wraps float based kepler attributes. Note that there is no
    FloatToken type in kepler, and no double type in python but they
    are interchangable.
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

class __string_based_attribute_proxy__(object):

    """ Wraps string based attributes.
    """

    def __init__(self, javaobj):
        self.javaobj = javaobj
    
    def get(self):
        return self.javaobj.getExpression()
    
    def set(self, x):
        self.javaobj.setExpression(x)
    
    def __repr__(self):
        return self.get()

class __array_based_attribute_proxy__(object):

    """ An attempt to wrap an array based attribute. This has
    not yet been completed or tested.
    """

    def __init__(self, javaobj):
        self.javaobj = javaobj

    def get(self):
        r = []
        t = self.javaobj.getToken()
        for i in range(t.length()):
            r.append(t.getElement(0))

def lazy_proxy_assign(obj):
    """ Tries to figure out the type of object passed to it and wraps
    it using either the WorkflowProxy or one of the above proxy objects.

    Note that the only case where anything other than the string proxy
    is used is for DoubleTokens. This is because most other tokens have
    the getExpression() and setExpression() functions which handle
    string based representations of the token's value. This works very
    well with Python, and thus most other token types have been left to
    be handled by the string proxy.
    """

    if isinstance(obj, (Actor, Director)):
        return EntityProxy(obj)
    if hasattr(obj, 'getToken'):
        t = obj.getToken()
        if isinstance(t, ptolemy.data.DoubleToken):
            return __float_based_attribute_proxy__(obj)
        elif isinstance(t, ptolemy.data.StringToken):
            return __string_based_attribute_proxy__(obj)
    if hasattr(obj, 'getExpression'):
        return __string_based_attribute_proxy__(obj)
    # If the object is a Class object, return the name of the class
    # NOTE: not quite sure what the rational was behind this.
    if isinstance(obj, java.lang.Class):
        return obj.__class__.__name__
    else:
        # if this can't figure out what to do with this object, it is probably un-proxyable
        # thus the object itself is just returned
        # NOTE: it may make more sense to throw an exception here
        print 'lazy_proxy_ unable to assign %s a proxy' % obj
        return obj

class ActorMap(object):

    """ Attemp at a Map to make accessing actors easier
    
    FullName: .workflow-name.Composite Actor Name.Actor Name
    Get Actor: from Composite Actor Object: obj.getEntity('Actor Name')
    Flat Map: md5 full name : Actor Object
    
    NOTE: INCOMPLETE AND NOT USED
    """

    def __init__(self, toplevel):
        self.map = {}
        while True:
            ent_list = toplevel.allAtomicEntityList()
            director = toplevel.getDirector()
            if director:
                obj_list.append(director)
            obj_list.extend(ent.allCompositeEntityList())
            for obj in obj_list:
                hash = md5.new(obj.getFullName()).hexdigest()
                if self.map.has_key(hash):
                    raise Exception('duplicate hash found')
                self.map[hash] = obj

class EntityProxy(object):

    """ This object's purpose is to make accessing the various parts of
    a workflow simpler.
    """

    def __init__(self, input, filters=[]):
        """ object constructor
        
        Keyword attributes:
        input -- either a string containing the contents of a MoML file
        (the contents of the file, not the actual file) or one of the
        following Java objects or their subclasses: 
        ptolemy.kernel.Entity, ptolemy.actor.Actor, 
        ptolemy.actor.Director.
        filters -- a list of MoMLFilter objects. generally used by
        hydrant to replace actors for portal execution.
        """
        try:
            if isinstance(input, basestring):
                self.from_moml(input, filters)
            else:
                self.from_entity(input)

            self.has_entities = hasattr(self.proxied_entity, 'getEntities')
            self.has_attribs = hasattr(self.proxied_entity, 'getAttributes')
            self.has_ports = hasattr(self.proxied_entity, 'getPorts')

            if hasattr(self.proxied_entity, 'name'):
                self.name = self.proxied_entity.name
        except Exception, e:
            traceback.print_exc()
            raise Exception('expects either moml or a model type')

    def from_moml(self, moml, filters=[]):
        """ Attempts to create a model from a string containing MoML
        code.

        Keyword attributes:
        moml -- the MoML string
        filters -- a list of MoMLFilter objects
        """

        # apply the RemoveGraphicalClasses MoMLFilter
        # but remove the TextAttribute class from the filter
        # such that annotations don't get removed from the model
        rgc = RemoveGraphicalClasses()
        rgc.remove('ptolemy.vergil.kernel.attributes.TextAttribute')
        # create a new list for the filters, and use 
        # MoMLParser.setMoMLFilters with the new list. setMoMLFitlers is
        # used because the MoML filters object inside MoMLParser is
        # static, the only filtering on addMoMLFilter is memory address
        # filtering, and the filters specific to hydrant are only used
        # when executing a workflow, and no removeMoMLFilter object is
        # present. This is simply the easiest way to ensure nothing
        # goes wrong.
        f = [rgc]
        f.extend(filters)
        MoMLParser.setMoMLFilters(f)

        messages = utils.validateMoML(moml)

        # If a list is returned by validateMoML an error has occured 
        # during validation, and we shouldn't continue.
        if messages is []:
            raise Exception('VALIDATION ERRORS')

        parser = MoMLParser()
        parser.reset()
        try:
            self.proxied_entity = parser.parse(moml)
        except java.lang.ExceptionInInitializerError, e:
            e.printStackTrace()
            raise
    
    # from_model attempts to takes in a model to proxy
    def from_entity(self, entity):
        """ Sets the entity which this object will proxy.
        
        Keyword arguments:
        entity -- The entity to proxy. Only accepted if it is an object
        which extends from one of the Ptolemy classes: Entity, Actor or
        Director.
        """
        if isinstance(entity, (Entity, Actor, Director)):
            self.proxied_entity = entity
        else:
            raise Exception('%s : %s' % (type(entity), self.proxied_entity.__class__))

    def _build_entity_map(self):
        for o in proxied_entity.containedObjectsIterator():
            pass

    def __getitem__(self, x):
        """ The implementation of __getitem__ attemtps to return a proxy
        object of the attribute named x. x could be an attribute of the
        proxied entity, an actor (in the case of composite entities) or
        the port of an actor.
        """

        m = None
        if hasattr(self.proxied_entity, x):
            m = getattr(self.proxied_entity, x)
        if not m and self.has_attribs:
            m = self.proxied_entity.getAttribute(x)
        if not m and self.has_entities:
            m = self.proxied_entity.getEntity(x)
        if not m and self.has_ports:
            m = self.proxied_entity.getPort(x)
        if not m:
            return None
        try:
            return lazy_proxy_assign(m)
        except:
            # the above should usually work, so if it doesn't tell us
            # why then attempt to assign a construct a new proxy object
            # using the attribute
            traceback.print_exc()
            return EntityProxy(m)

    def get(self, x):
        """ Returns an entity who's name is given in x. The
        resulting entity is either a proxy object
        """
        return self.__getitem__(x)

    def keys(self):
        """ Return a list of all the available keys that can be
        requested successfully from __getitem__.
        """
        d = []
        if self.has_attribs:
            d.extend([i.name for i in self.proxied_entity.getAttributes()])
        if self.has_entities:
            d.extend([i.name for i in self.proxied_entity.getEntities()])
        if self.has_ports:
            d.extend([i.name for i in self.proxied_entity.getPorts()])
        return d

    def __str__(self):
        return '%s {%s}' % (self.proxied_entity.__class__, self.proxied_entity.getFullName())

    def __unicode__(self):
        return unicode(self.__str__())

    def set_actor_property(self, path_to_actor, property, value):
        """ A function which traverses into the actor hierachy to
        find the desired property and then sets the value of
        that property to the specified value.

        Keyword arguments:
        path_to_actor -- A list of strings denoting the path to the
        actor to which the desired property belongs, starting with
        the next actor down from the current entity. If this is
        empty, then the current proxied entity should contain the
        desired property.
        property -- The name of the desired property.
        value -- The value to assign to the property.
        """
        if path_to_actor:
            self.get(path_to_actor[0]).set_actor_property(path_to_actor[1:], property, value)
        else:
            self.get(property).set(value)

    def get_actor_property(self, path_to_actor, property):
        """ A function which traverses into the actor hierachy to
        find the desired property and then returns the value of
        that property.

        Keyword arguments:
        path_to_actor -- A list of strings denoting the path to the
        actor to which the desired property belongs, starting with
        the next actor down from the current entity. If this is
        empty, then the current proxied entity should contain the
        desired property.
        property -- The name of the desired property.
        """
        if path_to_actor:
            return self.get(path_to_actor[0]).get_actor_property(path_to_actor[1:], property)
        else:
            m = self.get(property)
            # If the property itself has a get() function then
            # call it to get the real value of the property,
            # otherwise just return the property itself.
            if hasattr(m, 'get'):
                return m.get()
            else:
                return m

    def get_all_actors(self):
        """ Returns a list of all the actors under the proxied entity
        """
        if self.has_entities:
            return [EntityProxy(i) for i in self.proxied_entity.entityList() if isinstance(i, ptolemy.actor.Actor)]
        else:
            return []

    def get_as_dict(self, path=[], top=True):
        """ A comprehensive function which explores the entity, assuming 
        that it is a CompositeEntity type object, and returns a
        dictionary representation of the entity. This function was built
        for the purpose of creating a JSON type representation of a
        Workflow or Composite Actor such that it can be passed to a
        Django template such that js-graph.it code could be generated
        to render the workflow graph on a web page.

        
        Keyword arguments:
        path -- The path to the actor which the dict needs to represent.
        Only needed if the dict being represented is not the base entity.
        top -- true for the inital call of get_as_dict, and used to tell
        when the crumbs section should be processed. this shouldn't be
        set directly by the user
    
        Returns:
        rdic -- Definition of dictionary structure as follows:
        name -- The name of the entity.
        composite -- Only set if the entity is composite.
        canvas -- A dictionary with 'x' and 'y' keys which denote the
        size of the workflow canvas.
        actors -- A list of all actors directly below this entity. Each
        actor entry is a dictionary with the following keys:
            name -- The name of the actor
            location -- A dictionary with 'x' and 'y' keys representing
            the location of the actor on the workflow canvas.
            inputports -- A list of strings containing the names of this
            actor's input ports.
            outputports -- A list of strings containing the names of
            this actor's output ports.
            composite -- Only set if the actor is a Composite Actor.
        director -- Only present if the entity has a director. the entry
        is a dictionary with keys: 'name' and 'location'.
        ports -- A list of dictionarys denoting the ports this entity
        has. Each dictionary has keys: 'name', which is the verbose name
        for the port, 'id' which is a unique id which can be used to
        refer to the port and 'location'. Each port also contains one of
        the following attributes, depending on what type of port it is:
        'input', 'output', 'multiport'.
        vertices -- A list of dictionaries denoting all the vertices
        contained by this entity. A vertex is the little black diamond
        that links relations together. Each vertex entry contains a
        'name' and a 'location' key.
        links -- a link is a connection between different components.
        Either side of a link can be a port or a vertex. The links are
        presented as a list of lists. The internal lists always contains
        two elements which are the names of the two objects that the
        link connects. Lists are used over tuples because they can be
        sorted and thus easily avoid duplicate entries.
        annotations -- a list of dictionaries denoting all the
        annotations contained by this entity. Annotations have a 'text'
        key containing the text of the annotation, a 'location' key,
        and the following keys, which are standard text presentations
        details: 'text_size', 'font_family', 'bold', 'italic',
        'text_color'.

        TODO: 
            * NEED ERROR HANDLING
            * turn this into a private function, to remove the ability
            for the user to set the top variable
        """

        # Create the initial object that will eventually be returned to
        # the caller.
        rdic = {'actors':[], 'vertices':[], 'links':[], 'annotations':[], 'ports':[]}

        # If path is not empty, then traverse the actor hierachy until
        # the requested actor is found
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
                rdic['crumbs'] = crumbs[:-1]
            return rdic

        min_x = min_y = 1000000
        max_x = max_y = -1000000

        # get the name of the model
        rdic['name'] = self.proxied_entity.getName()
        if not top:
            rdic['composite'] = True
        iterator = self.proxied_entity.containedObjectsIterator()
        for i in iterator:
            loc = None
            if isinstance(i, SizeAttribute):
                #print i.getToken().toString()
                rdic['canvas'] = utils.locationToDict(i.getToken().toString())
            elif isinstance(i, Actor):
                # this section handles actors
                a = {}
                a['name'] = i.getName()
                loc = a['location'] = utils.locationToDict(i.getAttribute('_location').getValueAsString())
                a['inputports'] = [utils.uniqueNameForPort(p) for p in i.inputPortList()]
                a['outputports'] = [utils.uniqueNameForPort(p) for p in i.outputPortList()]
                # check if the actor is composite
                if isinstance(i, CompositeActor):
                    a['composite'] = True
                rdic['actors'].append(a)
            elif isinstance(i, Director):
                # this section handles the director entity if one is
                # present.
                loc = utils.locationToDict(i.getAttribute('_location').getValueAsString())
                rdic['director'] = {'name':i.getName(), 'location':loc }
            elif isinstance(i, Relation):
                # this section handles relation entities, which produces
                # vertices and links.
                vertex = utils.getVertexFromRelation(i)
                if vertex:
                    utils.addToListIfNotAlreadyThere(rdic['vertices'], vertex)
                ports = []
                relations = []
                # traverse through the list of objects linked by this
                # relation and add them to a list based on the type of
                # object
                for o in i.linkedObjectsList():
                    if isinstance(o, Port):
                        ports.append(o)
                    elif isinstance(o, Relation):
                        relations.append(o)

                # The following section takes the data found from the
                # previous exploration and deciphers from it what is
                # involved in this relation.

                if not vertex and not relations and len(ports) is 2:
                    # Simple port -> port connection
                    utils.addToListIfNotAlreadyThere(rdic['links'], 
                                                     utils.sortList([
                                utils.uniqueNameForPort(p) for p in ports]))
                elif vertex and not relations:
                    # all ports are connected to a single vertex
                    for port in ports:
                        utils.addToListIfNotAlreadyThere(rdic['links'],
                                                         utils.sortList([
                                    utils.uniqueNameForPort(port), 
                                    vertex['name']]))
                elif vertex and relations:
                    # Relation contains vertex -> vertex connections.
                    # Go through the list of relations and pull out
                    # the vertex for each relation.
                    for r in relations:
                        vertex2 = utils.getVertexFromRelation(r)
                        if not vertex2:
                            raise(Exception('should be a vertex to vertex link,\
but the linking relation doesn\'t have a vertex. i=%s, r=%s' % (i, r)))
                        utils.addToListIfNotAlreadyThere(rdic['links'],
                                                         utils.sortList([
                                    vertex['name'], vertex2['name']]))
                    # If there were any ports found as well, then the
                    # ports should be linked to the original vertex.
                    for port in ports:
                        utils.addToListIfNotAlreadyThere(rdic['links'],
                                                         utils.sortList([
                                    utils.uniqueNameForPort(port), vertex['name']
                                    ]))
                # If none of the above scenarios occur then raise an
                # exception because there is a scenario that's not
                # been discovered yet.
                else:
                    raise(Exception('unable to handle relation %s' % i))
            elif isinstance(i, TextAttribute):
                # handling annotations. nothing too tricky about this.
                # there are some commented out sections using the style
                # attribute that i've left because it looks like rubbish
                # but there may have been some method behind my maddness
                annotation = {'text': i.text.getExpression()}
                #try:
                #    style = i.text.attributeList()[0]
                #except:
                #    style = None
                aparams = [i for i in i.containedObjectsIterator()]
                textsize = [p for p in aparams if p.getName() == 'textSize']
                if textsize:
                    annotation['text_size'] = textsize[0].getToken().toString()
                ff = [p for p in aparams if p.getName() == 'fontFamily']
                if ff:
                    annotation['font_family'] = ff[0].getToken().stringValue()
                col = [p for p in aparams if p.getName() == 'textColor']
                if col:
                    annotation['text_color'] = utils.floatcolortohex(
                        col[0].getToken().toString()[1:-1].split(', '))
                bold = [p for p in aparams if p.getName() == 'bold']
                if bold and bold[0].getToken().booleanValue():
                    annotation['bold'] = 'true'
                italic = [p for p in aparams if p.getName() == 'italic']
                if italic and italic[0].getToken().booleanValue():
                    annotation['italic'] = 'true'
                location = [p for p in aparams if p.getName() == '_location']
                if location:
                    loc = annotation['location'] = utils.locationToDict(
                        location[0].getValueAsString())
                #    if style is not None:
                #        loc['x'] += style.width.getToken().intValue()
                #        loc['y'] += style.height.getToken().intValue()
                rdic['annotations'].append(annotation)
            elif isinstance(i, Port):
                # handling ports, very simple.
                loc = utils.locationToDict(
                    i.getAttribute('_location').getValueAsString())
                port = {'name': i.getName(), 
                        'id' : utils.uniqueNameForPort(i),
                        'location': loc}
                if i.isInput():
                    port['input'] = True
                if i.isOutput():
                    port['output'] = True
                if i.isMultiport():
                    port['multiport'] = True
                rdic['ports'].append(port)
            else:
                # failed to process this item!
                print 'unhandled object: %s' % i
            # if a location was present for the found entity, then
            # compare the x and y coordinates with the previously found
            # max and min and set them appropriatly
            if loc is not None:
                if float(loc['x']) > max_x:
                    max_x = float(loc['x'])
                if float(loc['x']) < min_x:
                    min_x = float(loc['x'])
                if float(loc['y']) > max_y:
                    max_y = float(loc['y'])
                if float(loc['y']) < min_y:
                    min_y = float(loc['y'])
        # set the canvas width and height based on the max and min
        # locations of the contained entities including a bit of padding
        rdic['canvas']['x'] = (max_x - min_x) + 200.0
        rdic['canvas']['y'] = (max_y - min_y) + 200.0

        # the following is a bit of crazyness to try and normalize the
        # positions of all the contained entities. this is required
        # since the canvas size has been set to contain the workflow
        # only and remove excess white space, thus all the entity
        # locations will not match up to the canvas.
        do_x_offset = lambda a: a['location'].__setitem__(
            'x', a['location']['x'] - (min_x - 50))
        do_y_offset = lambda a: a['location'].__setitem__(
            'y', a['location']['y'] - (min_y - 50))
        if rdic.has_key('director'):
            do_x_offset(rdic['director'])
            do_y_offset(rdic['director'])
        for a in rdic['actors']:
            do_x_offset(a)
            do_y_offset(a)
        for a in rdic['annotations']:
            do_x_offset(a)
            do_y_offset(a)
        for p in rdic['ports']:
            do_x_offset(p)
            do_y_offset(p)
        for v in rdic['vertices']:
            do_x_offset(v)
            do_y_offset(v)
        return rdic

    def get_properties(self, path=[]):
        """ Returns a list of all the properties for this entity.

        If path is specified, recursivly finds the entity refered to by
        path and returns the result of get_properties for that entity

        The resulting list is a list of dictionaries with the
        following keys:
        name --  the verbose name of the property
        id -- the unique id of the property
        value -- the string representation of the property's value
        type -- the type of entity (either 'FILE', 'TEXT', 'CHECKBOX', \
        'SELECT')
        choices -- only present for 'SELECT' typed properties, and \
        lists all the options that could be selected for the property
        """
        if path:
            g = self.get(path[0])
            return g.get_properties(path[1:])
        attribs = [i for i in self.proxied_entity.attributeList() 
                   if not i.getName().startswith('_')]
        properties = []
        for a in attribs:
            if isinstance(a, KeplerDocumentationAttribute):
                pass # we don't really care about the doc
            elif isinstance(a, SemanticType):
                pass # we don't need to know the semantic type
            elif isinstance(a, NamedObjId):
                pass # ...
            elif isinstance(a, Scheduler):
                pass # ignore schedulers
            elif a.getName() == 'class' or a.getName() == 'kar':
                pass # ignore class properties and kar attribures for now
            else:
                try:
                    if hasattr(a, 'getExpression'):
                        value = a.getExpression()
                    elif hasattr(a, 'getValueAsString'):
                        value = a.getValueAsString()
                    else:
                        try:
                            value = a.getToken().toString()
                        except:
                            value = ''
                            traceback.print_exc()
                    attr = {'name':a.getName(), 'id':a.getFullName(), 'value':value}
                    if isinstance(a, ptolemy.data.expr.FileParameter):
                        attr['type'] = 'FILE'
                    elif isinstance(a, ptolemy.kernel.util.StringAttribute):
                        for i in a.attributeList():
                            if isinstance(i, ptolemy.actor.gui.style.TextStyle):
                                attr['type'] = 'TEXT'
                    elif a.getType() == BaseType.BOOLEAN:
                        attr['type'] = 'CHECKBOX'
                        attr['value'] = a.getToken().booleanValue()
                    if hasattr(a, 'getChoices') and a.getChoices():
                        attr['type'] = 'SELECT'
                        attr['choices'] = list(a.getChoices())
                    properties.append(attr)
                except:
                    print a
                    traceback.print_exc()
        return properties

    def is_actor(self, path=None):
        """ Returns true if this entity is an actor, false for composite
        actors and anything else.
        
        If path is specified, recursivly finds the entity refered to by
        path and returns the result of is_actor for that entity.
        """
        if path:
            g = self.get(path[0])
            return g.is_actor(path[1:])
        if isinstance(self.proxied_entity, Actor) and not isinstance(self.proxied_entity, CompositeActor):
            return True
        else:
            return False

    def get_xml(self):
        """ Returns the MoML code for the current entity.
        this may be different from the MoML that the entity proxy
        was instantiated from if there have been modifications
        made to properties
        """
        return self.proxied_entity.exportMoML()

