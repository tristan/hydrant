package au.edu.jcu.kepler.hydrant;

import java.io.File;
import java.util.HashMap;

import org.geon.BinaryFileWriter;

import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;

public class BinaryFileWriterReplacement extends BinaryFileWriter {

	public BinaryFileWriterReplacement(CompositeEntity container, String name)
			throws IllegalActionException, NameDuplicationException {
		super(container, name);
		// TODO Auto-generated constructor stub
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
