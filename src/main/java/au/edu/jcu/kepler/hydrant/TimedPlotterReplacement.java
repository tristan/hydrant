package au.edu.jcu.kepler.hydrant;

import ptolemy.actor.TypedIOPort;
import ptolemy.data.BooleanToken;
import ptolemy.data.DoubleToken;
import ptolemy.data.IntToken;
import ptolemy.data.expr.Parameter;
import ptolemy.data.type.BaseType;
import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;
import ptolemy.kernel.util.StringAttribute;

public class TimedPlotterReplacement extends PlotterBase {
	public TimedPlotterReplacement(CompositeEntity container, String name)
    throws IllegalActionException, NameDuplicationException {
		super(container, name);
		
		input = new TypedIOPort(this, "input", true, false);
        input.setMultiport(true);
        input.setTypeEquals(BaseType.DOUBLE);
	}
	
	public TypedIOPort input;
		
    public boolean postfire() throws IllegalActionException {
        double currentTimeValue;
        int width = input.getWidth();
        int offset = ((IntToken) startingDataset.getToken()).intValue();

        for (int i = width - 1; i >= 0; i--) {
            if (input.hasToken(i)) {
            	
                currentTimeValue = input.getModelTime(i).getDoubleValue();

                DoubleToken currentToken = (DoubleToken) input.get(i);
                double currentValue = currentToken.doubleValue();

                // NOTE: We assume the superclass ensures this cast is safe.
                //((Plot) plot).addPoint(i + offset, currentTimeValue,
                //        currentValue, true);
                add_point(i, currentTimeValue, currentValue);
            	
            }
        }

        return super.postfire();
    }

}
