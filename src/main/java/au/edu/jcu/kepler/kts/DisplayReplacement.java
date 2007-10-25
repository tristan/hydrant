package au.edu.jcu.kepler.kts;

import java.util.HashMap;

import ptolemy.actor.TypedAtomicActor;
import ptolemy.actor.TypedIOPort;
import ptolemy.data.BooleanToken;
import ptolemy.data.StringToken;
import ptolemy.data.Token;
import ptolemy.data.expr.Parameter;
import ptolemy.data.type.BaseType;
import ptolemy.kernel.CompositeEntity;
import ptolemy.kernel.util.IllegalActionException;
import ptolemy.kernel.util.NameDuplicationException;
import ptolemy.kernel.util.StringAttribute;

/**
 * Relplaces the Display actor in kepler workflows, 
 * 
 **/
public class DisplayReplacement extends ReplacementActor {
	public DisplayReplacement(CompositeEntity container, String name)
    throws IllegalActionException, NameDuplicationException {
		super(container, name);
		
        input = new TypedIOPort(this, "input", true, false);
        input.setMultiport(true);
        input.setTypeEquals(BaseType.GENERAL);

        rowsDisplayed = new Parameter(this, "rowsDisplayed");
        rowsDisplayed.setExpression("10");
        columnsDisplayed = new Parameter(this, "columnsDisplayed");
        columnsDisplayed.setExpression("40");

        suppressBlankLines = new Parameter(this, "suppressBlankLines");
        suppressBlankLines.setTypeEquals(BaseType.BOOLEAN);
        suppressBlankLines.setToken(BooleanToken.FALSE);

        title = new StringAttribute(this, "title");
        title.setExpression("");
	}
	
    /** The horizontal size of the display, in columns. This contains
     *  an integer, and defaults to 40.
     */
    public Parameter columnsDisplayed;

    /** The input port, which is a multiport.
     */
    public TypedIOPort input;

    /** The vertical size of the display, in rows. This contains an
     *  integer, and defaults to 10.
     */
    public Parameter rowsDisplayed;

    /** The flag indicating whether this display actor suppress
     *  blank lines. The default value is false.
     */
    public Parameter suppressBlankLines;

    /** The title to put on top. */
    public StringAttribute title;
	
    private StringBuffer _output;
    
	public void initialize() throws IllegalActionException {
		// set up output source
		_output = new StringBuffer();
	}
	
	public boolean postfire() throws IllegalActionException {
		// write tokens to the output source
		int width = input.getWidth();
		for (int i = 0; i < width; i++) {
			if (input.hasToken(i)) {
				Token token = input.get(i);
				String value = token.toString();
				if (token instanceof StringToken) {
					value = ((StringToken)token).stringValue();
				}
				_output.append(value+"\n");
			}
		}
		return super.postfire();	
	}
	
	public void wrapup() {
		ReplacementManager man = getReplacementManager();
		HashMap data_map = new HashMap();
		data_map.put("name", getFullName());
		data_map.put("type", "TEXT");
		data_map.put("output", _output.toString());
		man.writeData(data_map);
	}
}
