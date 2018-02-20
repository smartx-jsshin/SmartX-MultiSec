package chainlinker;

/*
 * Corresponding to snap-plugin-collector-psutil
 * 
 * CAUTION: This setting may fail in case if the plugins' version mismatch with the below.
 * - collector:psutil:6
 */
public class SnapPSUtilParser extends SnapPluginParser {
	public SnapPSUtilParser() {
		typeMap.put("intel/psutil/load/load1", lfClass);
		typeMap.put("intel/psutil/load/load5", lfClass);
		typeMap.put("intel/psutil/load/load15", lfClass);
		typeMap.put("intel/psutil/vm/free", lClass);
		typeMap.put("intel/psutil/vm/used", lClass);
		typeMap.put("intel/psutil/vm/available", lClass);		
	}
		
	public void addField(
			org.influxdb.dto.Point.Builder pointBuilder, 
			String dataTypeName, 
			Object data
			) throws ClassNotFoundException {
		try {
			ReflectivePointFieldFeeder.addField(
					pointBuilder, typeMap.get(dataTypeName), data);
		} catch (ClassNotFoundException e) {
			throw new ClassNotFoundException ();
		}
	}
	
	public boolean isParsible(String dataTypeName) {
		if (typeMap.get(dataTypeName) != null) return true;
		return false;
	}
}