package au.edu.jcu.kepler.hydrant.io;

import au.edu.jcu.kepler.hydrant.ReplacementManager;
import ptolemy.kernel.util.NamedObj;

import java.util.HashMap;

public class TextOutput implements ptolemy.actor.io.TextOutput {

    private NamedObj owner;
    private ReplacementManager replacementManager;

    public void initialise(NamedObj owner, String id) {
	this.owner = owner;
	this.replacementManager = (ReplacementManager)owner.getContainer().getAttribute("replacement-manager");
    }

    public void write(String text) {
	HashMap data_map = new HashMap();
	String name = owner.getFullName();
	data_map.put("name", name);
	data_map.put("type", "TEXT");
	data_map.put("output", text);
	replacementManager.writeData(data_map);
    }
}