package chainlinker;
import java.util.HashMap;
import java.util.LinkedList;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.json.simple.JSONArray;

/*
 * Not confirmed about what happens when InfluxDB connection failed.
 * No reference or documents are found. Need to be reinforced.
 */

public class SnapParser {
	private static final Logger logger = LogManager.getLogger(SnapParser.class);
	protected LinkedList<Backend> backends;

	protected HashMap<String, SnapPluginParser> parserMap = new HashMap<>();
	protected LinkedList<SnapPluginParser> parserList = new LinkedList<>();
	protected ConfigLoader config;

	public SnapParser() {
		config = ConfigLoader.getInstance();
		backends = config.getBackends();
		// TODO: Must make this reflective.
		HashMap<String, Class<? extends SnapPluginParser>> parserClassMap = SnapPluginManifest.getInstance().getPluginManifestMap();
		try {
			for (String collector : config.getSnapConfig().getCollectors()) {
				Class<? extends SnapPluginParser> parserClass = parserClassMap.get(collector);
				logger.debug("Loading SnapPluginParser module '" + parserClass.getName() + "' for plugin '" + collector + "'");
				parserList.add(parserClass.newInstance());
			}
		} catch (InstantiationException e) {
			logger.fatal("Failed to instantitate given class from SnapPluginManifest. Is SnapPluginManifest is properly written?", e);
		} catch (IllegalAccessException e) {
			logger.fatal("Failed to instantitate given class from SnapPluginManifest. Is SnapPluginManifest is properly written?", e);
		}
		
		for (SnapPluginParser parserIter : parserList) {
			parserIter.loadParserMap(parserMap);
		}
	}
	
	public void processMessage(JSONArray msgValue) {
		for (Backend backend : backends) {
			backend.processMessage(msgValue, parserMap, parserList);			
		}
	}	

}
