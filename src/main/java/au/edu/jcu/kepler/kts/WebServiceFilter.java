package au.edu.jcu.kepler.kts;

import java.util.HashMap;

import ptolemy.kernel.util.NamedObj;
import ptolemy.moml.MoMLFilter;
import ptolemy.moml.MoMLParser;

public class WebServiceFilter implements MoMLFilter {

	private static HashMap _replacements;
	
	static {
		_replacements = new HashMap();
		_replacements.put("ptolemy.actor.lib.gui.Display", "au.edu.jcu.kepler.kts.DisplayReplacement");
		_replacements.put("ptolemy.actor.lib.gui.XYPlotter", "au.edu.jcu.kepler.kts.XYPlotterReplacement");
	}
	
	public String filterAttributeValue(NamedObj container, String element,
			String attributeName, String attributeValue) {
		if (attributeValue == null) {
			return null;
		} else if (_replacements.containsKey(attributeValue)) {
			MoMLParser.setModified(true);
			return (String)_replacements.get(attributeValue);
		}
		return attributeValue;
	}

	public void filterEndElement(NamedObj container, String elementName)
			throws Exception {
	}
	
	public String toString() {
		return _replacements.toString();
	}

}
