package chainlinker;

/*
 * Corresponding to snap-plugin-collector-cpu
 * 
 * CAUTION: This setting may fail in case if the plugins' version mismatch with the below.
 * - collector:cpu:2
 */
public class SnapCPUParser extends SnapPluginParser {
	// The regex must be updated when data type name changes.
	String regex = "^intel\\/procfs\\/cpu\\/(0|[1-9][0-9]*|all)\\/utilization_percentage$";
	
	public SnapCPUParser() {
		typeMap.put("intel/procfs/cpu/all/utilization_percentage", lfClass);
	}			
	
	// Overridden due to parameterized data names.
	public boolean isParsible(String dataTypeName) {
		if (dataTypeName.matches(regex)) {
			return true;			
		} else {
			return false;			
		}
	}	
}
