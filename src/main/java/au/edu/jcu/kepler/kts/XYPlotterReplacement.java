package au.edu.jcu.kepler.kts;

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

public class XYPlotterReplacement extends ReplacementActor implements Configurable {
	public XYPlotterReplacement(CompositeEntity container, String name)
    throws IllegalActionException, NameDuplicationException {
		super(container, name);
		
		startingDataset = new Parameter(this, "startingDataset",
                new IntToken(0));
        startingDataset.setTypeEquals(BaseType.INT);
		
		fillOnWrapup = new Parameter(this, "fillOnWrapup", new BooleanToken(
                true));
        fillOnWrapup.setTypeEquals(BaseType.BOOLEAN);

        legend = new StringAttribute(this, "legend");
		
		inputX = new TypedIOPort(this, "inputX", true, false);
        inputX.setMultiport(true);
        inputX.setTypeEquals(BaseType.DOUBLE);

        inputY = new TypedIOPort(this, "inputY", true, false);
        inputY.setMultiport(true);
        inputY.setTypeEquals(BaseType.DOUBLE);
	}
	
	/** The starting dataset number to which data is plotted.
     *  This parameter has type IntToken, with default value 0.
     *  Its value must be non-negative.
     */
	public Parameter startingDataset;
	
	/** If true, fill the plot when wrapup is called.
     *  This parameter has type BooleanToken, and default value true.
     */
    public Parameter fillOnWrapup;

    /** A comma-separated list of labels to attach to each data set.
     *  This is always a string, with no enclosing quotation marks.
     */
    public StringAttribute legend;
	
	/** Input port for the horizontal axis, with type DOUBLE. */
    public TypedIOPort inputX;

    /** Input port for the vertical axis, with type DOUBLE. */
    public TypedIOPort inputY;
    
    protected JFreeChart _chart;
    protected XYSeriesCollection _dataset;
    protected List<String> _legend;
    
    public void initialize() throws IllegalActionException {
    	_dataset = new XYSeriesCollection(); 
    	_chart = ChartFactory.createXYLineChart("XY Plotter", "", "", _dataset, PlotOrientation.VERTICAL, true, false, false);
    	
    	String value = legend.getExpression();
    	_legend = new ArrayList<String>();
        if ((value != null) && !value.trim().equals("")) {
            StringTokenizer tokenizer = new StringTokenizer(value, ",");
            while (tokenizer.hasMoreTokens()) {
                _legend.add(tokenizer.nextToken().trim());
            }
        }
	}
    
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
            	XYSeries series = null;
            	try {
            		series = _dataset.getSeries(i);
            	} catch (IllegalArgumentException e) {
            		String key;
            		try {
            			key = _legend.get(i);
            		} catch (IndexOutOfBoundsException e1) {
            			key = Integer.toString(i);
            		}
            		series = new XYSeries(key);
            		_dataset.addSeries(series);
            	}
            	series.add(xValue, yValue);
            }
        }
        return super.postfire();
    }
    
    @SuppressWarnings("unchecked")
	public void wrapup() {
		ReplacementManager man = getReplacementManager();
		HashMap data_map = new HashMap();
		data_map.put("name", getFullName());
		data_map.put("type", "IMAGE");
		
		ByteArrayOutputStream baos = new ByteArrayOutputStream();
		KeypointPNGEncoderAdapter encoder = new KeypointPNGEncoderAdapter();
		try {
			encoder.encode(_chart.createBufferedImage(480, 300), baos);
		} catch (IOException e) {
			e.printStackTrace();
			return;
		}
		
		data_map.put("format", "PNG");
		data_map.put("output", baos);
		man.writeData(data_map);
	}

	public void configure(URL base, String source, String text)
			throws Exception {
		// TODO Auto-generated method stub	
	}

	public String getConfigureSource() {
		// TODO Auto-generated method stub
		return "";
	}

	public String getConfigureText() {
		// TODO Auto-generated method stub
		return "";
	}
}