package au.edu.jcu.kepler.hydrant;

import ptolemy.actor.TypedAtomicActor;
import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;

public class ReplacementActor extends TypedAtomicActor {

	public ReplacementActor(CompositeEntity container, String name)
    throws IllegalActionException, NameDuplicationException {
		super(container, name);
	}
	
	protected ReplacementManager getReplacementManager() {
		CompositeEntity container = (CompositeEntity)getContainer();
		return (ReplacementManager)container.getAttribute("replacement-manager");
	}
	
}
