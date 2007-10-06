import re, sys
from ptolemy.moml import MoMLParser, Vertex
from ptolemy.moml.filter import RemoveGraphicalClasses
from java.lang import Class, Throwable, NoClassDefFoundError, NullPointerException
from ptolemy.kernel.util import NamedObj

re_class_attribs = re.compile(r'class=\"([\.\w]+)\"')

class ValidationError(Exception):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)
        def getValue(self):
            return self.value

def validateMoML(moml):
    errors = []
    classnames = getAllClassesInMoML(moml)
    # run the MoML filters over the class list
    for filter in MoMLParser.getMoMLFilters():
        classnames = [classname for classname in classnames if filter.filterAttributeValue(None, None, None, classname) != None]
    for classname in classnames:
        try:
            __import__(classname)
        except ImportError:
            error = {'cause':'ImportError', 'message':classname}
            errors.append(error)
        try:
            print 'checking class: %s' % classname
            obj = sys.modules.get(classname)()
#           if isinstance(obj, NamedObj):
#               pass
        except NoClassDefFoundError, e:
            error = {'cause':'java.lang.NoClassDefFoundError when loading actor %s' % classname, 'message':e.getMessage()}
            errors.append(error)
        except NullPointerException:
            pass
        except TypeError:
            pass
    # we just loaded a heap of classes into the default workspace, to avoid problems lets remove them
    NamedObj().workspace().removeAll()

    # if we have errors, raise them
    if errors:
        #print 'we have errors: %s' % errors
        raise ValidationError(errors)
    return True #{'result':errors == [], 'errors': errors }

def getAllClassesInMoML(moml):
    return {}.fromkeys(re_class_attribs.findall(moml)).keys()

def locationToDict(s):
    """ converts location string from kepler workflows into a {'x':x, 'y':y} dict """
    if type(s) is type(''):
        t = tuple(s[1:-1].replace(' ','').split(','))
    elif type(s) is type([]):
        t = s
    else:
        raise(Exception('unable to convert location in type %s' % type(s)))
    return {'x':t[0], 'y':t[1]}

def getVertexFromRelation(r):
    vertices = [v for v in r.containedObjectsIterator() if isinstance(v, Vertex)]
    for v in vertices:
        vertex = {'name': '%s__%s' % (r.getName(), v.getName()), 'location':locationToDict(v.getValueAsString())}
        return vertex
    return None

def addToListIfNotAlreadyThere(list, object):
    if object not in list:
        list.append(object)

def sortList(list):
    list.sort()
    return list

def objectDetailsFromKeplerPath(path):
    l = path.split('.')
    if l[0] is not '':
        raise(Exception('invalid kepler path, %s' % path))
    return {'object': l[-1], 'workflow': len(l) > 2 and l[1] or '', 'parent': len(l) > 3 and l[-2] or ''}

def uniqueNameForPort(port):
    return port.getFullName().replace('.', '__').replace(' ', '_')

def floatcolortohex(s):
    return ('%2x%2x%2x' % ( int(255 * float(s[0])), int(255 * float(s[1])), int(255 * float(s[2])) )).replace(' ', '0')
