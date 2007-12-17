package au.edu.jcu.kepler.hydrant;

import java.io.ByteArrayOutputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.StringTokenizer;

import ptolemy.actor.TypedIOPort;
import ptolemy.data.BooleanToken;
import ptolemy.data.DoubleToken;
import ptolemy.data.IntToken;
import ptolemy.data.expr.Parameter;
import ptolemy.data.type.BaseType;
import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.Configurable;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;
import ptolemy.kernel.util.StringAttribute;
import ptolemy.plot.Plot;

import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.ChartFactory;
import org.jfree.chart.encoders.KeypointPNGEncoderAdapter;
import org.jfree.chart.plot.PlotOrientation;

public class XYPlotterReplacement extends PlotterBase {
	public XYPlotterReplacement(CompositeEntity container, String name)
    throws IllegalActionException, NameDuplicationException {
		super(container, name);
		
		inputX = new TypedIOPort(this, "inputX", true, false);
        inputX.setMultiport(true);
        inputX.setTypeEquals(BaseType.DOUBLE);

        inputY = new TypedIOPort(this, "inputY", true, false);
        inputY.setMultiport(true);
        inputY.setTypeEquals(BaseType.DOUBLE);
	}
	
	
	/** Input port for the horizontal axis, with type DOUBLE. */
    public TypedIOPort inputX;

    /** Input port for the vertical axis, with type DOUBLE. */
    public TypedIOPort inputY;
     
    public boolean postfire() throws IllegalActionException {
        int widthX = inputX.getWidth();
        int widthY = inputY.getWidth();

        if (widthX != widthY) {
            throw new IllegalActionException(this,
                    " The number of input channels mismatch.");
        }

        int offset = ((IntToken) startingDataset.getToken()).intValue();

        //for (int i = widthX - 1; i >= 0; i--) {
        for (int i = 0 ; i < widthX ; i++) {
            boolean hasX = false;
            boolean hasY = false;
            double xValue = 0.0;
            double yValue = 0.0;

            if (inputX.hasToken(i)) {
                xValue = ((DoubleToken) inputX.get(i)).doubleValue();
                hasX = true;
            }

            if (inputY.hasToken(i)) {
                yValue = ((DoubleToken) inputY.get(i)).doubleValue();
                hasY = true;
            }

            if (hasX && hasY) {
                // NOTE: We assume the superclass ensures this cast is safe.
                //((Plot) plot).addPoint(i + offset, xValue, yValue, true);
            	add_point(i, xValue, yValue);
            }
        }
        return super.postfire();
    }
}