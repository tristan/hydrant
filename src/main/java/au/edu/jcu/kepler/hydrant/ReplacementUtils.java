package au.edu.jcu.kepler.hydrant;

import ptolemy.actor.TypedAtomicActor;
import ptolemy.kernel.CompositeEntity;

public class ReplacementUtils {
	public static ReplacementManager getReplacementManager(TypedAtomicActor e) {
		CompositeEntity container = (CompositeEntity) e.getContainer();
		return (ReplacementManager)container.getAttribute("replacement-manager");
	}
}
