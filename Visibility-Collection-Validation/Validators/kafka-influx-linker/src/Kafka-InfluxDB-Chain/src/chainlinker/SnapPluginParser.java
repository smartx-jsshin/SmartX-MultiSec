package chainlinker;

import java.util.HashMap;

/*
 * This class serve as a template for all Snap plugin parsers.
 */
public abstract class SnapPluginParser {
	Long lValue = 0L;
	Double lfValue = 0.0;
	@SuppressWarnings("rawtypes")
	Class lClass = lValue.getClass();
	@SuppressWarnings("rawtypes")
	Class lfClass = lfValue.getClass();	
	
	@SuppressWarnings("rawtypes")
	HashMap<String, Class> typeMap = new HashMap<>(); 
	
	public void loadParserMap(HashMap<String, SnapPluginParser> map) {
		for (String dataName : typeMap.keySet()) {
			map.put(dataName, this);
		}
	}
	
	// This method is to describe how the parser will feed the given data into pointBuilder.
	public void addField(
			org.influxdb.dto.Point.Builder pointBuilder, 
			String dataTypeName, 
			Object data
			) throws ClassNotFoundException {
		if (!isParsible(dataTypeName))  throw new ClassNotFoundException ();
		
		try {
			ReflectivePointFieldFeeder.addField(
					pointBuilder, typeMap.get(dataTypeName), data);
		} catch (ClassNotFoundException e) {
			throw new ClassNotFoundException ();
		}
	}
	
	// This method is to describe whether the parser is able to handle data with the given name.
	// This exists to handle data with parameterized names.
	public boolean isParsible(String dataTypeName) {
		if (typeMap.get(dataTypeName) != null) return true;
		return false;
	}	
}