package au.edu.jcu.kepler.hydrant;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.StringTokenizer;

import org.jfree.chart.ChartFactory;
import org.jfree.chart.JFreeChart;
import org.jfree.chart.encoders.KeypointPNGEncoderAdapter;
import org.jfree.chart.plot.PlotOrientation;
import org.jfree.data.xy.XYSeries;
import org.jfree.data.xy.XYSeriesCollection;

import ptolemy.actor.TypedAtomicActor;
import ptolemy.data.BooleanToken;
import ptolemy.data.IntToken;
import ptolemy.data.expr.Parameter;
import ptolemy.data.type.BaseType;
import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.Configurable;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;
import ptolemy.kernel.util.StringAttribute;

public class PlotterBase extends TypedAtomicActor implements Configurable {
	public PlotterBase(CompositeEntity container, String name)
    throws IllegalActionException, NameDuplicationException {
		super(container, name);
		
		startingDataset = new Parameter(this, "startingDataset", new IntToken(0));
        startingDataset.setTypeEquals(BaseType.INT);
		
		fillOnWrapup = new Parameter(this, "fillOnWrapup", new BooleanToken(true));
        fillOnWrapup.setTypeEquals(BaseType.BOOLEAN);

        legend = new StringAttribute(this, "legend");
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

    protected JFreeChart _chart;
    protected XYSeriesCollection _dataset;
    protected List<String> _legend;
    
	public void initialize() throws IllegalActionException {
		_dataset = new XYSeriesCollection(); 
    	_chart = ChartFactory.createXYLineChart(getName(), "", "", _dataset, PlotOrientation.VERTICAL, true, false, false);
    	
    	String value = legend.getExpression();
    	_legend = new ArrayList<String>();
        if ((value != null) && !value.trim().equals("")) {
            StringTokenizer tokenizer = new StringTokenizer(value, ",");
            while (tokenizer.hasMoreTokens()) {
                _legend.add(tokenizer.nextToken().trim());
            }
        }
	}
	
	protected void add_point(int series_id, double xvalue, double yvalue) {
		XYSeries series = null;
    	try {
    		series = _dataset.getSeries(series_id);
    	} catch (IllegalArgumentException e) {
    		String key;
    		try {
    			key = _legend.get(series_id);
    		} catch (IndexOutOfBoundsException e1) {
    			key = Integer.toString(series_id);
    		}
    		series = new XYSeries(key);
    		_dataset.addSeries(series);
    	}
    	series.add(xvalue, yvalue);	
	}

	@SuppressWarnings("unchecked")
	public void wrapup() {
		ReplacementManager man = ReplacementUtils.getReplacementManager(this);
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
		return null;
	}

	public String getConfigureText() {
		// TODO Auto-generated method stub
		return null;
	}
        
}
