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

public abstract class ReplacementManager extends SingletonAttribute {
    public ReplacementManager(NamedObj container, String name)
	throws NameDuplicationException, IllegalActionException {
	super(container, name);
    }

    public abstract void writePythonData(PyDictionary data);
    public abstract String getCurrentUsername();

    public abstract void setWaitingForInput(String prompt, String type, HydrantIO iodev);

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
