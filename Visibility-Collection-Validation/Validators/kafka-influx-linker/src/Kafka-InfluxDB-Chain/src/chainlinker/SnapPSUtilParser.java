package chainlinker;

/*
 * Corresponding to snap-plugin-collector-psutil
 * 
 * CAUTION: This setting may fail in case if the plugins' version mismatch with the below.
 * - collector:psutil:6
 */
public class SnapPSUtilParser extends SnapPluginParser {
	public SnapPSUtilParser() {
		super();
		// All these data forms must be updated when snap publisher's output format is changed.
		
		typeMap.put("/intel/psutil/load/load1", lfClass);
		typeMap.put("/intel/psutil/load/load5", lfClass);
		typeMap.put("/intel/psutil/load/load15", lfClass);
		typeMap.put("/intel/psutil/vm/free", lClass);
		typeMap.put("/intel/psutil/vm/used", lClass);
		typeMap.put("/intel/psutil/vm/available", lClass);
		typeMap.put("/intel/psutil/net/all/bytes_recv", lClass);
		typeMap.put("/intel/psutil/net/all/bytes_sent", lClass);
		typeMap.put("/intel/psutil/net/all/packets_recv", lClass);
		typeMap.put("/intel/psutil/net/all/packets_sent", lClass);
		
		// Pattern: /intel/psutil/net/(alphanumerical(lowercase only) or _ or .)/(bytes_recv or bytes_sent or packets_recv or packets_sent)
		regexTypeMap.put("^\\/intel\\/psutil\\/net\\/([0-9]|[a-z]|_|\\.)*\\/(bytes_recv|bytes_sent|packets_recv|packets_sent)$", lClass);
		
		regexSet = regexTypeMap.keySet();
	}
}