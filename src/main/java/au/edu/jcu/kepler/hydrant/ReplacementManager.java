package au.edu.jcu.kepler.hydrant;

import java.io.ByteArrayOutputStream;
import java.util.HashMap;

import org.python.core.PyArray;
import org.python.core.PyDictionary;
import org.python.core.PyInteger;
import org.python.core.PyList;
import org.python.core.PyObject;
import org.python.core.PySequence;
import org.python.core.PyString;
import org.python.core.PyType;

import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;
import ptolemy.kernel.util.NamedObj;
import ptolemy.kernel.util.SingletonAttribute;

import au.edu.jcu.kepler.hydrant.io.HydrantIO;

/**
   ReplacementManager is a class used by Hydrant as a proxy for communication
   Between a running workflow and the portal. It provides an interface for
   Actors to send data to the portal and in the case of actors which block
   while waiting for user input, the functionality to get that input back
   to the actors.

   This class is abstract and needs to be implemented by the Portal which
   requires it.
   TODO: this code is python specific. It may be better to make this a generic
   interface, and move the python specific code to a python extension.

   TODO: the name ReplacementManager came from the class's original purpose,
   which was simply as a helper class to Replacement Actors. Now that the
   Replacement Actor concept is being phased out by the Actor-IO concept
   the name of this class does not suit it's function and should be renamed.
 **/
public abstract class ReplacementManager extends SingletonAttribute {
    public ReplacementManager(NamedObj container, String name)
	throws NameDuplicationException, IllegalActionException {
	super(container, name);
    }

    /**
       takes the python dictionary provided by writeData and
       uses it to save the data in a portal specific way.
     **/
    public abstract void writePythonData(PyDictionary data);

    /**
       get the username of the user whom the running job belongs to.
     **/
    public abstract String getCurrentUsername();

    /**
       alert the portal that an actor is waiting for user input.
     **/
    public abstract void setWaitingForInput(String prompt, String type, HydrantIO iodev);

    /**
       constructs a python dictionary from the provided hashmap.
     **/
    public void writeData(HashMap data_map) {
	PyDictionary d = new PyDictionary();
	for (Object key: data_map.keySet()) {
	    if ((key instanceof String)) {
		Object value = data_map.get(key);
		if (value instanceof String) {
		    d.__setitem__((String)key, new PyString((String)value));
		} else if (value instanceof ByteArrayOutputStream) {
		    PyArray pa = new PyArray(byte.class, ((ByteArrayOutputStream)value).toByteArray());
		    d.__setitem__((String)key, pa);
		}
	    }
	}
	writePythonData(d);
    }
}
