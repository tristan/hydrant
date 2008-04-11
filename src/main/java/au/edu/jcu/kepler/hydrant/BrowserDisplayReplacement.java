package au.edu.jcu.kepler.hydrant;

import java.util.HashMap;

import java.io.File;
import java.io.IOException;
import java.net.URI;

import ptolemy.actor.TypedAtomicActor;
import ptolemy.actor.TypedIOPort;
import ptolemy.data.BooleanToken;
import ptolemy.data.StringToken;
import ptolemy.data.type.BaseType;
import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.attributes.URIAttribute;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;

/**
 * Replacment for org.geon.BrowserDisplay.
 * 
 **/
public class BrowserDisplayReplacement extends TypedAtomicActor {
    public BrowserDisplayReplacement(CompositeEntity container, String name)
	throws IllegalActionException, NameDuplicationException {
	super(container, name);
	
	inputURL = new TypedIOPort(this, "inputURL", true, false);
	inputURL.setTypeEquals(BaseType.STRING);

	trigger = new TypedIOPort(this, "trigger", true, false);
	trigger.setTypeEquals(BaseType.BOOLEAN);
    }
	
    public TypedIOPort inputURL;

    public TypedIOPort trigger;
	
    /** Represent the URL to be display. */
    private String strFileOrURL;
    /** Indicator that there are more tokens to consume. */
    private boolean reFire = true;

    public void fire() throws IllegalActionException {
	boolean val = false;
	for (int i = 0; i < trigger.getWidth(); i++) {
              if (trigger.hasToken(i)) {
		  val = ((BooleanToken)trigger.get(i)).booleanValue();
		  if (val == false) {
		      inputURL.get(0); // consume token
		  }
	      }
	}
	try {
	    StringToken fileToken = null;
	    try {
		fileToken = (StringToken)inputURL.get(0);
	    } catch (Exception ex) {
		// pass
	    }
	    if (fileToken != null) {
		strFileOrURL = fileToken.stringValue();
		int lineEndInd = strFileOrURL.indexOf("\n");
		if (lineEndInd != -1) {
		    strFileOrURL = strFileOrURL.substring(0, lineEndInd);
		}
		if (!strFileOrURL.trim().toLowerCase().startsWith("http")) {
		    File toDisplay = new File(strFileOrURL);
		    if (!toDisplay.isAbsolute()) {
			URI modelURI = URIAttribute.getModelURI(this);
			if (modelURI != null) {
			    URI newURI = modelURI.resolve(strFileOrURL);
			    toDisplay = new File(newURI);
			    strFileOrURL = toDisplay.getAbsolutePath();
			}
		    }
		    String canonicalPath = toDisplay.getCanonicalPath();
		    strFileOrURL = "file:///" + canonicalPath;
		}

		ReplacementManager man = 
		    ReplacementUtils.getReplacementManager(this);
		HashMap data_map = new HashMap();
		String name = getFullName();
		data_map.put("name", name);
		data_map.put("type", "URI");
		data_map.put("filename", strFileOrURL);
		man.writeData(data_map);

	    } else {
		reFire = false;
	    }
	} catch (Exception e) {
	}
    }

    public boolean postfire() throws IllegalActionException {
	return reFire;
    }
    
    public void wrapup() {
	reFire = true;
    }
}
