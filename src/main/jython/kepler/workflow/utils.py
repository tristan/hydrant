import re, sys, traceback
from ptolemy.moml import MoMLParser, Vertex
from ptolemy.moml.filter import RemoveGraphicalClasses
from java.lang import Class, Throwable, NoClassDefFoundError, NullPointerException
from ptolemy.kernel.util import NamedObj
from org.python.core import PyJavaPackage
from ptolemy.moml import MoMLParser

class ValidationError(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)
        def getValue(self):
            return self.value

def checkClassHeirachy(klass):
    if klass is None:
        return None
    try:
        klass = klass.getSuperclass()
    except NoClassDefFoundError, e:
        return e
    # TODO: uploading more than one workflow causes nullpointer exceptions
    # figure out why
    except NullPointerException, e:
        return None
    return checkClassHeirachy(klass)


def addMoMLFilters(filters):
    """
    checks each filter to make sure it's not already been added
    and only adds new filters if they haven't
    """
    current_filters = MoMLParser.getMoMLFilters() or []
    fcs = [f.__class__ for f in current_filters]
    for f in filters:
        if f.__class__ not in fcs:
            MoMLParser.addMoMLFilter(f)

def check_moml_dependencies(moml):
    """ Checks all the classes in a MoML file by importing each one
    along with it's entire class heirarchy checking for any missing
    classes or libraries.

    Returns a list of any errors found.
    """
    messages = []
    classnames = getAllClassesInMoML(moml)
    # run the MoML filters over the class list
    momlfilters = MoMLParser.getMoMLFilters() or []
    for filter in momlfilters:
        _classnames = []
        for c in classnames:
            fn = filter.filterAttributeValue(None, None, "", c)
            if fn != None:
               _classnames.append(fn)
        classnames = _classnames

    # check each of the classes for errors
    for classname in classnames:
        try:
            # get a list of the package heirarchy for the class
            k_list = classname.split('.')[1:]
            # get the base package
            klass = __import__(classname)
            # check if the imported object is a javapackage, rather than a class,
            # and if so loop thru the package heirarchy to find the class
            while isinstance(klass, PyJavaPackage):
                klass = getattr(klass, k_list[0])
                k_list = k_list[1:]
            # once we have the class itself, check it's class heirarchy for errors
            errors = checkClassHeirachy(klass)
            if errors is not None:
                #print 'NEW ERROR MESSAGE: %s' % errors
                messages.append({'type':'ERROR','message': errors})
        except ImportError, e:
            error = {'type':'ERROR', 'message':e}
            messages.append(error)

    # we just loaded a heap of classes into the default workspace, to avoid problems lets remove them
    NamedObj().workspace().removeAll()
    return messages


import org.xml.sax.ErrorHandler
import org.xml.sax.EntityResolver
from javax.xml.parsers import DocumentBuilderFactory
from org.xml.sax import InputSource
#from java.io import ByteArrayInputStream
from java.io import StringReader
from java.lang import String
from javax.xml.transform.dom import DOMSource
from javax.xml.transform import TransformerFactory
from javax.xml.transform import OutputKeys
from javax.xml.transform.stream import StreamSource
from javax.xml.transform.stream import StreamResult
from settings import PROJECT_HOME

class _ErrorHandler(org.xml.sax.ErrorHandler):
    def fatalError(self, exception):
        print 'FATAL (%s): %s' % (exception.getLineNumber(), exception.getMessage())
    def error(self, exception):
        print 'ERROR (%s): %s' % (exception.getLineNumber(), exception.getMessage())
    def warning(self, exception):
        print 'WARNING (%s): %s' % (exception.getLineNumber(), exception.getMessage())

class _EntityResolver(org.xml.sax.EntityResolver):
    def resolveEntity(self, publicId, systemId):
        if systemId == "http://ptolemy.eecs.berkeley.edu/xml/dtd/MoML_1.dtd":
	    return InputSource(PROJECT_HOME + "/src/etc/MoML_1.dtd")
        else:
	    return None
	
def validate_moml(moml_str):
    try:
        factory = DocumentBuilderFactory.newInstance()
	factory.setValidating(True)
	builder = factory.newDocumentBuilder()
	builder.setErrorHandler(_ErrorHandler())
	builder.setEntityResolver(_EntityResolver())
	xmlDocument = builder.parse(InputSource(StringReader(moml_str)))#ByteArrayInputStream(String(moml_str).getBytes()))
	return True
    except:
        traceback.print_exc()
	return False

def _get_parser():
    rgc = RemoveGraphicalClasses()
    rgc.remove('ptolemy.vergil.kernel.attributes.TextAttribute')
    MoMLParser.setMoMLFilters([rgc])
    parser = MoMLParser()
    parser.reset()
    return parser

def parse_moml(moml_str):
    _get_parser().parse(moml_str)

def parse_moml_file(moml_file):
    try:
        _get_parser().parseFile(moml_file)
    except Exception, e:
        print e.getMessage()
        raise

re_class_attribs = re.compile(r'class=\"([\.\w]+)\"')
def getAllClassesInMoML(moml):
    """ Runs a regexp over a moml to find the values of all class="..."
    attributes.
    """
    return {}.fromkeys(re_class_attribs.findall(moml)).keys()

def locationToDict(s):
    """ Converts location string from kepler workflows into a {'x':x,
    'y':y} styled dict.
    """
    if type(s) in [unicode, str]:
        t = tuple(s[1:-1].replace(' ','').split(','))
    elif type(s) is type([]):
        t = s
    else:
        raise(Exception('unable to convert location in type %s' % type(s)))
    return {'x':float(t[0]), 'y':float(t[1])}

def getVertexFromRelation(r):
    """ Takes a Kepler object and returns a dict representing the first
    Vertex object that was found.
    """
    vertices = [v for v in r.containedObjectsIterator() if isinstance(v, Vertex)]
    for v in vertices:
        vertex = {'name': '%s__%s' % (r.getName(), v.getName()), 'location':locationToDict(v.getValueAsString())}
        return vertex
    return None

def addToListIfNotAlreadyThere(list, object):
    """ A shortcut to add a value to a list only if the value isn't
    already in the list.
    """
    if object not in list:
        list.append(object)

def sortList(list):
    """ A wrapper for list.sort() which returns the list. """
    list.sort()
    return list

def objectDetailsFromKeplerPath(path):
    l = path.split('.')
    if l[0] is not '':
        raise(Exception('invalid kepler path, %s' % path))
    return {'object': l[-1], 'workflow': len(l) > 2 and l[1] or '', 'parent': len(l) > 3 and l[-2] or ''}

def uniqueNameForPort(port):
    """ Uses a port's full name to build a unique, html complient, name
    to reference the port.
    """
    return port.getFullName().replace('.', '__').replace(' ', '_')

def floatcolortohex(s):
    """ Takes an array of float representations of rgb color values and
    returns a hex string representing the same color.
    """
    return ('%2x%2x%2x' % ( int(255 * float(s[0])), int(255 * float(s[1])), int(255 * float(s[2])) )).replace(' ', '0')
