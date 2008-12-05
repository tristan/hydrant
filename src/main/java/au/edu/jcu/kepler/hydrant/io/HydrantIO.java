package au.edu.jcu.kepler.hydrant.io;

import ptolemy.kernel.util.NamedObj;

import au.edu.jcu.kepler.hydrant.ReplacementManager;

public abstract class HydrantIO {

    protected NamedObj owner;
    protected ReplacementManager replacementManager;

    public void initialise(NamedObj owner, String id) {
	this.owner = owner;
	this.replacementManager = (ReplacementManager)owner.getContainer().getAttribute("replacement-manager");
    }

    public abstract void setInput(String input);

    public String getOwnerName() {
	return this.owner.getFullName();
    }
}