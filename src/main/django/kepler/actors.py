
class Actor:
    """ representation of a kepler actor in python """
    def __init__(self, name="", properties={}, location=(0,0)):
        self.name = name
        self.properties = properties
        self.location = location
        self.ports = []

class Port:
    """ representation of a port in a kepler workflow """
    INPUT = 'input'
    OUTPUT = 'output'
    INOUT = 'inout'
    def __init__(self, name='', direction=None):
        self.name = name     
        if direction is not self.INPUT and direction is not self.OUTPUT and direction is not self.INOUT and direction is not None:
            raise Exception('direction must be type \"' + self.INPUT + '\" or \"' + self.OUTPUT + '\" or \"' + self.INOUT + '\"')
        self.direction = direction or self.INOUT
        
    def isInput(self):
        """ if the port is an input port, return True """
        return self.direction is self.INPUT or self.direction is self.INOUT
    
    def isOutput(self):
        """ if the port is an output port, return True """
        return self.direction is self.OUTPUT or self.direction is self.INOUT
        
class Relation:
    """ representation of a relation in a kepler workflow """
    def __init__(self, width=1, location=(0,0)):
        self.width = width
        self.location = location

class Link:
    """ representation of a link between ports and relations in kepler
        workflows.
        
        the start and end variables can be either a Relation or a Port    """
    def __init__(self, start=None, end=None):
        self.start = port
        self.end = relation
    
class CompositeActor(Actor):
    """ representation of a composite kepler actor in python
        this can be used to define a workflow    """
    def __init__(self, name='', properties={}, location=(0,0), actors=[], relations=[], links=[]):
        Actor.__init__(self, name, properties, location)
        self.actors = actors
        self.relations = relations
        self.links = links
        
if __name__ == "__main__":
    """ testing functions """
    print 'testing Port functionality'
    p = Port(direction=Port.INPUT)
    if not p.isInput() or p.isOutput():
        raise Exception('expected INPUT port type failed')
    p = Port(direction=Port.OUTPUT)
    if not p.isOutput() or p.isInput():
        raise Exception('expected OUTPUT port type failed')
    p = Port('test')
    if not p.isInput() or not p.isOutput():
        raise Exception('expected INOUT port type failed')
    if p.name is not 'test':
        raise Exception('name assignment failed')
    print 'all tests passed'