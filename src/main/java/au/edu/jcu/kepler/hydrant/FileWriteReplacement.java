package au.edu.jcu.kepler.hydrant;

import java.io.File;
import java.util.HashMap;

import org.geon.FileWrite;

import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;

/**
 * This is used to replace LineWriter and FileWrite actors
 * replacing LineWriter with this will cause an output port to
 * be created on LineWriter, but this shouldn't be a problem as
 * it will not be connected to anything. This is done to avoid
 * duplicating code which is what would have to happen if a
 * replacement was made for each actor. 
 * 
 * @author tristan
 *
 */
public class FileWriteReplacement extends FileWrite {

	public FileWriteReplacement(CompositeEntity container, String name)
			throws IllegalActionException, NameDuplicationException {
	    super(container, name);
	}
	
	public void wrapup() throws IllegalActionException {
	    super.wrapup();
	    File f = new File(fileName.getExpression());
	    if (f.exists()) {
		ReplacementManager man = ReplacementUtils.getReplacementManager(this);
		HashMap data_map = new HashMap();
		data_map.put("name", getFullName());
		data_map.put("type", "FILE");
		data_map.put("filename", fileName.getExpression());
		man.writeData(data_map);
	    }
	}
}
