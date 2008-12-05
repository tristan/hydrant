package au.edu.jcu.kepler.hydrant.io;

import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.IOException;

import ptolemy.kernel.util.NamedObj;

public class StringInput extends HydrantIO implements ptolemy.actor.io.StringInput {

    private String val = null;
    private Thread thisthread;

    public void initialise(NamedObj owner, String id) {
	super.initialise(owner, id);
    }

    public String getInput(String prompt) {
	thisthread = Thread.currentThread();
	replacementManager.setWaitingForInput(prompt, "STRING", (HydrantIO)this);
	while (val == null) {
	    try {
		thisthread.sleep(100000);
	    } catch (InterruptedException e) {}
	}
	String result = val;
	val = null;
	return result;
    }

    public void setInput(String input) {
	val = input;
	thisthread.interrupt();
    }

    public void stop() {
	// if the workflow is stopped we want to break out of this so it doesn't hang the job.
	val = "";
	thisthread.interrupt();
    }
}