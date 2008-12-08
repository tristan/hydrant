package au.edu.jcu.kepler.hydrant.io;

import ptolemy.kernel.util.NamedObj;

import au.edu.jcu.kepler.hydrant.ReplacementManager;

/**
   This abstract class is the base for all Actor-IO devices built for Hydrant.
 **/
public abstract class HydrantIO {

    protected NamedObj owner;
    protected ReplacementManager replacementManager;

    /** Sets the owner variable and stores a reference to the workflow's Replacement Manager.
     **/
    public void initialise(NamedObj owner, String id) {
	this.owner = owner;
	this.replacementManager = (ReplacementManager)owner.getContainer().getAttribute("replacement-manager");
    }

    public abstract void setInput(String input);

    public String getOwnerName() {
	return this.owner.getFullName();
    }
}