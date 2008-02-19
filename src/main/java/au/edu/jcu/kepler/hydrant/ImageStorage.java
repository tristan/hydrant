package au.edu.jcu.kepler.hydrant;

import java.io.File;
import java.util.HashMap;

import ptolemy.actor.TypedAtomicActor;
import ptolemy.actor.TypedIOPort;
import ptolemy.actor.lib.Sink;
import ptolemy.data.StringToken;
import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;

/**
 * A replacement for the  util.ImageJActor actor.
 **/
public class ImageStorage extends TypedAtomicActor {
    public ImageStorage(CompositeEntity container, String name)
	throws NameDuplicationException, IllegalActionException {
	super(container, name);
        input = new TypedIOPort(this, "input", true, false);
        input.setMultiport(true);
    }

    ///////////////////////////////////////////////////////////////////
    ////                     ports and parameters                  ////
    
    /** 
     * The input port, which is a multiport.
     */
    public TypedIOPort input;
    
    public synchronized void fire() throws IllegalActionException {
    	if (input.getWidth() > 0) {
	    if (input.hasToken(0)) {
    	        String filename = ((StringToken)input.get(0)).stringValue();
    	        File f = new File(filename);
    	        if (f.exists()) {
		    ReplacementManager man = ReplacementUtils.getReplacementManager(this);
		    HashMap data_map = new HashMap();
		    data_map.put("name", getFullName());
		    data_map.put("type", "IMAGE");
		    data_map.put("filename", filename);
		    try {
			String ext = filename.substring(filename.lastIndexOf("."));
			data_map.put("format", ext.toLowerCase());
		    } catch (IndexOutOfBoundsException e) {
		    }
		    man.writeData(data_map);
    	        }
	    }
    	}
    }
}
