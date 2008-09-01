package au.edu.jcu.kepler.hydrant;

import ptolemy.actor.IOPort;
import ptolemy.actor.lib.Exec;
import ptolemy.data.StringToken;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;
import ptolemy.kernel.CompositeEntity;

public class CommandLineReplacement extends Exec {

    public CommandLineReplacement(CompositeEntity container, String name)
            throws NameDuplicationException, IllegalActionException {
        super(container, name);
    }

    public void fire() throws IllegalActionException {
	command.update();
	if (((StringToken) command.getToken()).stringValue() != null) {
            String _commandStr = ((StringToken) command.getToken())
                    .stringValue();

	    // get the user who is running the job
	    String user = ReplacementUtils.getReplacementManager(this).getCurrentUsername();
	    //_commandStr = "sudo su - " + user + "; " + _commandStr;
	    // get the input
	    String in = ((StringToken)input.get(0)).stringValue();
	    // create a new input string
	    String out = "sudo su - " + user + "\"; " + _commandStr + "; " + in + "; ";
	    // set the command to /bin/sh so that the input is run like a shell script
	    command.setToken(new StringToken("/bin/sh"));
	    // get the first port in the source ports list of input
	    IOPort p = (IOPort)(input.sourcePortList().get(0));
	    // send the new input string from the source port so that the original Exec actor can get it.
	    p.send(0, new StringToken(out));

	    
	}
	super.fire();
    }

}