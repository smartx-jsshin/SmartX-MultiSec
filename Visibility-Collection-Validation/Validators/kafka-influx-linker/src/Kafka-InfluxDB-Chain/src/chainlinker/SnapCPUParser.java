package chainlinker;

/*
 * Corresponding to snap-plugin-collector-cpu
 * 
 * CAUTION: This setting may fail in case if the plugins' version mismatch with the below.
 * - collector:cpu:2
 */
public class SnapCPUParser extends SnapPluginParser {
	// The regex must be updated when data type name changes.
	// Pattern: /intel/procfs/cpu/("all" or a number without 0 front of it)/utilization_percentage
	String regex = "^\\/intel\\/procfs\\/cpu\\/(0|[1-9][0-9]*|all)\\/utilization_percentage$";
	
	public SnapCPUParser() {
		super();
		
		typeMap.put("/intel/procfs/cpu/all/utilization_percentage", lfClass);
		
		// Pattern: /intel/procfs/cpu/(0 or numbers not starting with 0)/utilization_percentage
		regexTypeMap.put("^\\/intel\\/procfs\\/cpu\\/(0|[1-9][0-9]*|all)\\/utilization_percentage$", lfClass);
		
		regexSet = regexTypeMap.keySet();
	}			
	
}
