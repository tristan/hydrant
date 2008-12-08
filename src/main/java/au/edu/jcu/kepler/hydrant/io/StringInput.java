package au.edu.jcu.kepler.hydrant.io;

import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.IOException;

import ptolemy.kernel.util.NamedObj;

public class StringInput extends HydrantIO implements ptolemy.actor.io.StringInput {

    private String val = null;

    // since multiple threads will be working on the one object, we need to store
    // reference to the thread that is handling the execution of the actor so it
    // can be woken up when required.
    private Thread thisthread;

    public void initialise(NamedObj owner, String id) {
	super.initialise(owner, id);
    }

    /**
     **/
    public String getInput(String prompt) {
	thisthread = Thread.currentThread();
	// let the portal know that we need some input from the user.
	replacementManager.setWaitingForInput(prompt, "STRING", (HydrantIO)this);
	while (val == null) { // keep looping until we have a value
	    try {
		thisthread.sleep(300000); // sleep for 5 minutes (or until interrupted)
	    } catch (InterruptedException e) {}
	}
	String result = val;
	// reset val to null, incase there are multiple iterations of the workflow
	val = null;
	return result;
    }

    /**
       The setInput function is used by the portal to pass input from the user to the
       workflow.
     **/
    public void setInput(String input) {
	val = input;
	thisthread.interrupt();
    }

    /** stop is called by the owner of this device when a workflow stop request is given
     **/
    public void stop() {
	// if the workflow is stopped we want to break out of this so it doesn't hang the job.
	val = "";
	thisthread.interrupt();
    }
}