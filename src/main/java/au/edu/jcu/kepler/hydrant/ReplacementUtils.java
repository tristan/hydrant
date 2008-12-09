package au.edu.jcu.kepler.hydrant;

import ptolemy.actor.TypedAtomicActor;
import ptolemy.kernel.CompositeEntity;

/**
   This class provides generic utilities used by Replacement Actors.
 **/
public class ReplacementUtils {

    /**
       gets 
     **/
    public static ReplacementManager getReplacementManager(TypedAtomicActor e) {
	CompositeEntity container = (CompositeEntity) e.getContainer();
	return (ReplacementManager)container.getAttribute("replacement-manager");
    }
}
