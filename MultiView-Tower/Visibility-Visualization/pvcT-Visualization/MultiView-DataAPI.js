var MongoClient = require('mongodb').MongoClient;
var dateFormat = require('dateformat');
const assert = require('assert');
const { resolve } = require('path');

class ResourceProvider {
	constructor() {
		this.playgroundConfig = require("./config.json").playground;
		this.mongoConfig = require("./config.json")["document-db"];
		this.mongoUrl = 
			"mongodb://" + this.mongoConfig.userId + ":" + this.mongoConfig.userPassword +
			"@" + this.mongoConfig.ipaddr + ":" + this.mongoConfig.port +
			"/" + this.mongoConfig.authDb;
		console.log("[ResourceProvider] " + "MongoDB URL : " + this.mongoUrl);
	}
	
	//Get MultiView Users
	getUsers(callback) {
		console.log("[ResourceProvider] getUsers() is called");

		var mongoClient = new MongoClient(this.mongoUrl, { useUnifiedTopology: true });

		var self = this;
		mongoClient.connect(function (err, _mongoClient) {
			assert.equal(null, err);

			var multiviewDb = _mongoClient.db(self.mongoConfig.multiviewDb);
			var collection = multiviewDb.collection(self.mongoConfig.collectionMap.users);
			assert.notEqual(null, collection);

			collection.find({}).toArray(function (err, users) {
				console.log("[ResourceProvider | getUsers()] Acquired Data: \"");
				console.log(users);
				assert.equal(null, err);
				callback(null, users);
				_mongoClient.close();
			});
		});
	}
	
	//Get pBoxes List From MongoDB for TCP throughput-based Topology
	getTCPTopologyList(callback) {
		console.log("[ResourceProvider] getTCPTopologyList() is called");

		var mongoClient = new MongoClient(this.mongoUrl, { useUnifiedTopology: true });

		var self = this;
		mongoClient.connect(function (err, _mongoClient) {
			assert.equal(null, err);

			var multiviewDb = _mongoClient.db(self.mongoConfig.multiviewDb);
			var collection = multiviewDb.collection(self.mongoConfig.collectionMap.tcpTopology);
			assert.notEqual(null, collection);

			collection.find({}, { 
				srcBoxname: true, destBoxname: true, 
				srcBoxID: true, destBoxID: true, 
				value: true, score: true, _id: false 
			}).sort({ srcBoxID: -1 }).toArray(function (err, boxes) {
				console.log("[ResourceProvider | getTCPTopologyList()] Acquired Data: ");
				console.log(boxes);
				assert.equal(null, err);
				callback(null, boxes);
				_mongoClient.close();
			});
		});
	}

	// getPlaygroundTopologyList (callback) {
	// 	var mongoClient = new MongoClient(this.mongoUrl, { useUnifiedTopology: true });

	// 	var self = this;
	// 	mongoClient.connect(function (err, _mongoClient) {
	// 		assert.equal(null, err);

	// 		console.log('Physical Boxes List: ');
	// 		var playgroundTopologyDb = _mongoClient.db(self.mongoConfig.multiviewDb);
	// 		var collection = playgroundTopologyDb.collection(self.mongoConfig.collectionMap.playgroundTopology);

	// 		collection.find({}, { 
	// 			srcBoxname: true, destBoxname: true, 
	// 			srcBoxID: true, destBoxID: true, 
	// 			value: true, score: true, _id: false 
	// 		}).sort({ srcBoxID: -1 }).toArray(function (err, users) {
	// 			assert.equal(null, err);
	// 			callback(null, users);
	// 			_mongoClient.close();
	// 		});
	// 	});
	// }

	// //Get pBoxes List From MongoDB
	// getpBoxList(callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('Physical Boxes List: ');
	// 		// Locate all the entries using find
	// 		var collection = db.collection("configuration-pbox-list");
	// 		//collection.find({type: 'B**'},{box: true, host: true, management_ip: true, management_ip_status: true, data_ip: true, data_ip_status: true, control_ip: true, control_ip_status: true, _id: false}).sort({host: -1}).toArray(function(err, boxes){
	// 		collection.find({ $or: [{ type: 'B**' }, { type: 'C**' }] }, { box: true, boxID: true, management_ip: true, management_ip_status: true, data_ip: true, data_ip_status: true, control_ip: true, control_ip_status: true, _id: false }).sort({ host: -1 }).toArray(function (err, boxes) {
	// 			//	db.close();
	// 			//console.log(boxes);
	// 			callback(null, boxes);
	// 			db.close();
	// 		});
	// 		//console.log (db.boxes);
	// 	});
	// }
	// //Get vSwitches List From MongoDB
	// getvSwitchList(callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('OVS bridges List: ');
	// 		var collection = db.collection("configuration-vswitch-list");
	// 		collection.find({}, { type: true, bridge: true, topologyorder: true, _id: false }).sort({ topologyorder: 1 }).toArray(function (err, switchList) {
	// 			//db.close();
	// 			callback(null, switchList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get OVS Bridge Status From MongoDB
	// getovsBridgeStatus(callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('OVS Bridge Status: ');
	// 		var collection = db.collection("configuration-vswitch-status");
	// 		collection.find({}, { box: true, bridge: true, status: true, _id: false }).sort({ box: -1 }).toArray(function (err, ovsBridgeStatus) {
	// 			//db.close();
	// 			callback(null, ovsBridgeStatus);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get Controllers List From MongoDB New
	// getControllerList(callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		var collection = db.collection("playground-controllers-list");
	// 		collection.find({}, { controllerIP: true, controllerName: true, controllerStatus: true, controllerSoftware: true, _id: false }).sort({ controllerName: -1 }).toArray(function (err, controllers) {
	// 			callback(null, controllers);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get OpenStack Instances List From MongoDB
	// getvBoxList(callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('OpenStack instances List: ');
	// 		var collection = db.collection("vm-instance-list");
	// 		collection.find({}, { box: true, name: true, osuserid: true, ostenantid: true, vlanid: true, state: true, _id: false }).sort({ box: -1 }).toArray(function (err, vBoxList) {
	// 			callback(null, vBoxList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get OpenStack Instances List for Specific Tenant From MongoDB
	// getTenantvBoxList(tenantID, callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('OpenStack instances List in Tenant : ' + tenantID);
	// 		var collection = db.collection("vm-instance-list");
	// 		collection.find({ ostenantid: tenantID }, { _id: false, state: false, osuserid: false, vlandid: false }).sort({ box: -1 }).toArray(function (err, vBoxList) {
	// 			//db.close();
	// 			console.log(vBoxList);
	// 			callback(null, vBoxList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get IoT Host List From MongoDB New
	// getIoTHostList(callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('IoT Host List: ');
	// 		var collection = db.collection("IoT-Host-list");
	// 		collection.find({}, { boxID: true, hostID: true, macaddress: true, ipaddress: true, vlanid: true, _id: false }).sort({ boxID: -1 }).toArray(function (err, iotHostList) {
	// 			callback(null, iotHostList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get Workloads List From MongoDB
    // /*ResourceProvider.prototype.getServicesList = function(callback)
    // {
    //     MongoClient.connect(mongourl, function(err, db)
    //     {
    //         console.log('Services List: ');
    //         var collection = db.collection("configuration-service-list");
    //         collection.find({type: 'B**'},{box: true, name: true, osusername: true, ostenantname: true, vlanid: true, state: true, _id: false}).sort({box: -1}).toArray(function(err, vmList){
    //                 //db.close();
    //                 callback(null,vmList);
    //                 db.close();
    //         });
    //     });
    // };*/
	// //Get Tenant-vlan Mapping List
	// gettenantvlanmapList(callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		//console.log('Tenant-vlan Mapping List: '+tenantID);
	// 		var collection = db.collection("configuration-tenant-vlan-mapping");
	// 		collection.find({}, { _id: false }).sort({ name: -1 }).toArray(function (err, tenantList) {
	// 			callback(null, tenantList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get Bridge-vlan Mapping List
	// getbridgevlanmapList(vlanID, callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('Bridge-vlan Mapping for ' + vlanID);
	// 		var collection = db.collection("configuration-bridge-vlan-map-rt");
	// 		collection.find({ vlan: vlanID }, { _id: false, timestamp: false }).sort({ vlan: -1 }).toArray(function (err, vlanList) {
	// 			callback(null, vlanList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get Operator Controller Flow Rules
	// getOpsSDNConfigList(boxID, callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('Flow Rules List: ' + boxID);
	// 		var currentTime = new Date();
	// 		console.log('System Time: ' + currentTime);
	// 		dateFormat(currentTime.setMinutes(currentTime.getMinutes() - 59));
	// 		console.log('Updated Time: ' + currentTime);
	// 		var collection = db.collection("flow-configuration-sdn-controller-rt");
	// 		collection.find({ controllerIP: '103.22.221.152', boxID: boxID }, { _id: false }).sort({ name: -1 }).toArray(function (err, rulesList) {
	// 			callback(null, rulesList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get Operator Controller Flow Statistics
	// getOpsSDNStatList(boxID, callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('Flow Statistics List: ');
	// 		var currentTime = new Date();
	// 		console.log('System Time: ' + currentTime);
	// 		dateFormat(currentTime.setMinutes(currentTime.getMinutes() - 5));
	// 		console.log('Updated Time: ' + currentTime);
	// 		var collection = db.collection("flow-stats-sdn-controller-rt");
	// 		collection.find({ controllerIP: '103.22.221.152', boxID: boxID }, { _id: false }).sort({ name: -1 }).toArray(function (err, statList) {
	// 			callback(null, statList);
	// 			db.close();
	// 		});
	// 	});
	// }
	// //Get Active Monitoring data From MongoDB for TCP throughput
	// getAMDataTCPperDay(boxID, startDate, endDate, callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('Active Monitoring TCP data / day: ');
	// 		var collection = db.collection("topolgoy-tcp-data-raw");
	// 		collection.find({ $and: [{ srcBoxname: boxID }, { timestamp: { $gte: { "$date": startDate }, $lte: { "$date": endDate } } }] }).count().toArray(function (err, data) {
	// 			callback(null, data);
	// 			db.close();
	// 		});
	// 	});
	// }
	
	_getTopologyDataFromFile(_filename){
		return new Promise(function(resolve, reject){
			var _topologyData = require("./public/config/" + _filename);
			console.log("[ResourceProvider] _getTopologyDataFromFile() is called" );
			console.log(_topologyData);
			resolve(_topologyData);
		});
	}

	async _getCollectionAllDocs(multiviewDb, collectionName) {
		var collection = multiviewDb.collection(collectionName);
		var data = await collection.find().toArray();
		return data;
	}

	async _getCollectionDoc(multiviewDb, collectionName, rule) {
		var collection = multiviewDb.collection(collectionName);
		var data = await collection.find(rule).toArray();
		return data;
	}


	//
	// For Onion-ring 3D Visualization
	//

	_findMultiSecElement(topology, elemName){
		console.log("in _findElement(): " + elemName);
		console.log(topology);

		var res;
		if (Array.isArray(topology)){

			topology.forEach(topoElem => {
				if (res) {
					console.log("found");
					return res;
				}
				res = this._findMultiSecElement(topoElem, elemName);
			});

		} else {

			if (topology.name == elemName){
				console.log("Hit!!")
				console.log(topology);
				return topology;

			} else if (topology.childElements){

				topology.childElements.forEach(childElem => {
					if (res) {
						console.log("found");
						return res;
					}

					res = this._findMultiSecElement(childElem, elemName);
				});

			} else return null;
		}

		return res;
	}

	_enrichTopologyWithSecData(topology, multisec) {
		var pgTopo = topology.playground_topology;

		multisec.forEach(box => {
			const whereList = box.where.split(".");
			const tierList = box.tier.split("-");

			var isPhysical = true;
			if (tierList[tierList.length - 1] == "virtual"){
				isPhysical = false;
				whereList.pop(whereList.length -1);
			}

			var curLoc = pgTopo;
			whereList.forEach(whereElem => {
				curLoc = this._findMultiSecElement(curLoc, whereElem);
				console.log("curLoc");
				console.log(curLoc);
			});

			if (!curLoc) return;

			if (isPhysical){
				curLoc["securityLevel"] = box.securityLevel;

			} else {
				
				if (!curLoc["childElements"]) {
					curLoc["childElements"] = [];
				}

				var newVirtualBox = {};
				newVirtualBox["name"] = box.name;
				newVirtualBox["tier"] = box.tier;
				newVirtualBox["securityLevel"] = box.securityLevel;
				curLoc["childElements"].push(newVirtualBox);
			}
		});
	}

	async getOnionRing3DData(callback) {
		console.log("[ResourceProvider] getOnionRing3DData() is called");

		var readFromFile = false;
		var topologyData, multiSecData;
		var mongoClient, multiviewDb;
		var self = this;

		if (readFromFile){
			self._getTopologyDataFromFile("topology-k1.v2.json").then(
				// Load Topology Data from File
				function(_topologyData){
					topologyData = _topologyData
				}
			).
			then(
				function(){
					console.log(topologyData);
					callback(null, JSON.stringify(topologyData));
				}
			);

		} else {
			mongoClient = await new MongoClient(this.mongoUrl, { useUnifiedTopology: true }).connect();
			multiviewDb = mongoClient.db(self.mongoConfig.multiviewDb);
	
			var topologyData = await self._getCollectionDoc(multiviewDb, self.mongoConfig.collectionMap.playgroundTopology, {"type": "3d"})
			console.log(topologyData);
			var multiSecData = await self._getCollectionAllDocs(multiviewDb, self.mongoConfig.collectionMap.multiSecBoxes);
			console.log(multiSecData);
			await self._enrichTopologyWithSecData(topologyData[0], multiSecData);
			await mongoClient.close();
			callback(null, JSON.stringify(topologyData[0]));
		}
	}

	//
	// For Onion-ring 2D Visualization
	//
	_findBoxFromTopology(topology, matchingRule){
		if (topology.name.toLowerCase() === matchingRule.name.toLowerCase()) {
			return topology;
		}
		if ( (topology.hasOwnProperty("contains")) && (topology.contains.length !== 0) ){
			var res = null;
			topology.contains.some(elem => {
				res = this._findBoxFromTopology(elem, matchingRule);
				if (res !== null){
					return true;
				}
			});
			if (res !== null){
				return res;
			}
		}
		if ( (topology.hasOwnProperty("sublayer")) && (topology.sublayer.length !== 0) ){
			var res = null;
			topology.sublayer.some(elem => {
				res = this._findBoxFromTopology(elem, matchingRule);
				if (res !== null){
					return res;
				}
			});
			if (res !== null){
				return res;
			}
		}
		return null;
	}

	_addVCboxesToTopology(boxStatus, topology, tenantList, colorPallettes){
		const tenantColorPallete = colorPallettes["tenantColorPallete"];
		const statusColorPallete = colorPallettes["statusColorPallete"];
		console.log(tenantColorPallete);

		boxStatus.forEach(box => {
			// select the boxes having type virtual/container
			console.log("_addVCboxesToTopology(), Cur Box "+ box.name + " " + box.tier + " " + box.where);
			var boxTier = box.tier.split(".").pop();

			var parentBoxTier = null;
			var parentBoxName = null;
			var parentPhysicalBox = null;

			if (boxTier === "vcbox"){
				// find the physical box which is a parent of this virtual/container box.
				// parent name, parent type
				let tmpArr = box.tier.split(".");
				tmpArr.pop();
				parentBoxTier = "";
				tmpArr.forEach(function(item, idx) {
					parentBoxTier = parentBoxTier + item;
					if (idx !== (tmpArr.length-1) ){
						parentBoxTier = parentBoxTier + ".";
					}
				});
				console.log("parentBoxTier: " + parentBoxTier);

				parentBoxName = box.where.split(".");
				parentBoxName = parentBoxName[parentBoxName.length - 1]

				// console.log("" + parentBoxTier + " " + parentBoxName);
				var rule = {
					"name": parentBoxName
				};

				console.log("")
				parentPhysicalBox = this._findBoxFromTopology(topology, rule);
				console.log("	parentPhysicalBox: " + parentPhysicalBox);

				if (parentPhysicalBox !== null){
					// Create a box instance for the virtual/container box
					var vcBoxInst = {}
					vcBoxInst["name"] = box.name;
					// vcBoxInst["description"] = box.name;
					vcBoxInst["statusColor"] = statusColorPallete[box.status];
					
					// var tenantIdx = 1;
					// tenantList.some(function(tnt, idx) {
					// 	console.log("tenant from tenantList: " + tnt.username + " " + idx);
					// 	if (tnt.username === box.tenant){
					// 		vcBoxInst["description"] = "Box Name: " + box.name + "," + "Tenant Name: " + tnt.username;
					// 		if (tnt.hasOwnProperty("tenantColor") && tnt.tenantColor !== null){
					// 			vcBoxInst["tenantColor"] = tnt.tenantColor;
					// 		}else {
					// 			tenantIdx = idx + 1;
					// 			vcBoxInst["tenantColor"] = tenantColorPallete[tenantIdx];
					// 		}
					// 		return true;
					// 	}
					// });

					// Insert the created instance to the located physical box
					parentPhysicalBox.contains.push(vcBoxInst);
				}				
			}
		});
	}

	_findBoxStatusElement(boxStatus, matchingRule){
		var matchedBox = null;
		boxStatus.some(box => {
			var check = true
			Object.keys(matchingRule).forEach(k => {
				if (box[k].toLowerCase() !== matchingRule[k].toLowerCase()) {
					check = false;
				}
			});

			if (check === true) {
				matchedBox = box;
			}
			return check;
		});

		return matchedBox;
	}

	_enrichTopologyWithStatusData(topology, boxStatus, boxAllocMap, tenantList, colorPallettes){
		console.log("_enrichTopologyWithStatusData() " + topology.name);
		const tenantColorPallete = colorPallettes["tenantColorPallete"];
		const statusColorPallete = colorPallettes["statusColorPallete"];

		var rule = null;
		var boxStatusElement = null;

		rule = {"name": topology.name};
		boxStatusElement = this._findBoxStatusElement(boxStatus, rule);

		// Add Status Color
		if ( !(topology.hasOwnProperty("statusColor"))) {
			if (boxStatusElement !== null && boxStatusElement.hasOwnProperty("status")){
				let idx = boxStatusElement["status"];
				topology["statusColor"] = statusColorPallete[idx];
			} else {
				topology["statusColor"] = statusColorPallete[0];
			}
		}

		if (boxStatusElement !== null){
			// Find the tenant who occupies the box from Box Alloc table
			var tenantName = null;
			boxAllocMap.some(function(boxAlloc, idx){
				if (boxAlloc.name === boxStatusElement.name){
					tenantName = boxAlloc.tenant;
					return true;
				}
				return false;
			});

			// Find the color of the tenant from the tenant list
			var tenantColor = null;
			if (tenantName !== null){
				tenantList.some(function(tnt, idx) {
					console.log("tenant from tenantList: " + tnt.username + " " + idx);
					if (tnt.username === tenantName){
						tenantColor = tnt.tenantColor;
						return true;
					}
				});
			}

			if (tenantName === null || tenantColor === null){
				tenantName = "operator";
				tenantColor = "black";
			}

			topology["tenantColor"] = tenantColor;
			var boxDesc = "Box Name: " + topology.name + ", " + "Tenant Name: " + tenantName;
			if (boxStatusElement["status"] === 2){
				boxDesc = boxDesc + ", Status: Active"; 
			} else if (boxStatusElement["status"] === 0){
				boxDesc = boxDesc + ", Status: Inctive"; 
			}
			topology["description"] = boxDesc;

		}

		// if (boxStatusElement !== null && boxStatusElement.hasOwnProperty("tenant")){
		// 	tenantList.some(function(tnt, idx) {
		// 		console.log("tenant from tenantList: " + tnt.name + " " + idx);
		// 		if (tnt.username === boxStatusElement.tenant){
		// 			topology["tenantColor"] = tnt.tenantColor;
		// 			topology["description"] = "Box Name: " + topology.name + "," + "Tenant Name: " + tnt.username;
		// 			return true;
		// 		}
		// 	});
		// }

		// Add the default values to unassigned attributes for the visualization
		// Add Tenant Color
		if (!(topology.hasOwnProperty("tenantColor"))){
			let tenantIdx = 1;
			topology["tenantColor"] = tenantColorPallete[tenantIdx];
		}
		// Add Description
		if (!(topology.hasOwnProperty("description"))){
			topology["description"] = "Box Name: " + topology.name + "," + "Tenant Name: operator";
		}
		// The field "value" will be used by psd3 to determine the size of ring segments
		topology["value"] = 1;


		// Traverse other elements on outer layers
		if (topology.hasOwnProperty("contains")){
			topology.contains.forEach(containedBoxes => {
				this._enrichTopologyWithStatusData(containedBoxes, boxStatus, boxAllocMap, tenantList, colorPallettes);
			});
		}
		if (topology.hasOwnProperty("sublayer")){
			topology.sublayer.forEach(subBoxes => {
				this._enrichTopologyWithStatusData(subBoxes, boxStatus, boxAllocMap, tenantList, colorPallettes);
			});
		}
	}
	
	async getOnionRingData(callback){
		console.log("[ResourceProvider] getOnionRingData() is called");

		var readFromFile = false;
		var topologyData;
		var mongoClient, multiviewDb;
		var self = this;

		if (readFromFile){
			self._getTopologyDataFromFile("topology-k1.scenario3.json").then(
				function(_topologyData){
					topologyData = _topologyData
				}
			)
			.then(
				function(){
					console.log(topologyData);
					callback(null, JSON.stringify(topologyData));
				}
			);
		} else {
			mongoClient = await new MongoClient(this.mongoUrl, { useUnifiedTopology: true }).connect();
			multiviewDb = mongoClient.db(self.mongoConfig.multiviewDb);

			var tenantList = await self._getCollectionAllDocs(multiviewDb, self.mongoConfig.collectionMap.users);
			var statusColorPallete = ["#EFEFEF", "#FFFF66", "#90FF90"];
			var tenantColorPallete = ["LightGrey", "Black"];
			const colorPallettes = {
				"statusColorPallete": statusColorPallete,
				"tenantColorPallete": tenantColorPallete
			}

			tenantList.forEach(tnt => {
				if (tnt.role === "operator"){
					var tntIdx = tenantList.indexOf(tnt);
					tenantList.splice(tntIdx, 1);
				}else {
					if (tnt.hasOwnProperty("tenantColor")){
						tenantColorPallete.push(tnt.tenantColor);
					} else{
						var randomColor = "#" + Math.floor(Math.random()*16777215).toString(16);
						tenantColorPallete.push(randomColor);
					}
				}
			});
	
			var topologyData = await self._getCollectionDoc(multiviewDb, self.mongoConfig.collectionMap.playgroundTopology, {"type": "2d"})
			console.log(topologyData);

			var pvBoxStatusData = await self._getCollectionAllDocs(multiviewDb, self.mongoConfig.collectionMap.pvBoxStatus);
			console.log(pvBoxStatusData);

			var boxAllocMap = await self._getCollectionAllDocs(multiviewDb, self.mongoConfig.collectionMap.boxAlloc);

			await self._addVCboxesToTopology(pvBoxStatusData, topologyData[0].playground_topology, tenantList, colorPallettes);
			await self._enrichTopologyWithStatusData(topologyData[0].playground_topology, pvBoxStatusData, boxAllocMap, tenantList, colorPallettes);
			
			mongoClient.close();
			topologyData = JSON.stringify([topologyData[0].playground_topology]);
			console.log(topologyData);
			callback(null, topologyData);		
		}
	}

	//ManhNT
	getDataMultiSliceVisibility(userID, callback) {
		MongoClient.connect(mongourl, function (err, client) {
			const db = client.db('multiviewdb');
			// var colConfigMultiUser = db.collection('configuration-multiview-users');
			var colUnderlay_main = db.collection('underlay_main');
			var colunder_int = db.collection('underlay_int');
			var colunder_ren = db.collection('underlay_REN');
			var playground_sites = db.collection('playground_sites');
			var colpBox = db.collection('pbox-list');
			var colIoTHostList = db.collection('IoT-Host-list');
			var colVMInstance = db.collection('vm-instance-list');
			var flowvisor_slice = db.collection('flowvisor_slice');
			var data = [];
			var main = 0;
			colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
				colunder_int.find({}).toArray(function (err, rUnder_int) {
					colunder_ren.find({}).toArray(function (err, rUnder_ren) {
						playground_sites.find({}).toArray(function (err, rplayground_sites) {
							colpBox.find({ type: 'B**' }).toArray(function (err, rpBox) {
								flowvisor_slice.find({}).toArray(function (err, rVLANs) {
									colVMInstance.find({}).toArray(function (err, rVM) {
										colIoTHostList.find({}).toArray(function (err, rIoT) {
											//TEIN Main
											for (var i = 0; i < rUnderlay_main.length; i++) {
												rUnderlay_main[i].drilldown = [];
												rUnderlay_main[i].resource = 4;
												rUnderlay_main[i].label = rUnderlay_main[i].name;
												rUnderlay_main[i].info = rUnderlay_main[i].name;
												rUnderlay_main[i].color = 'white';
												rUnderlay_main[i].textBoder = 'LightGrey';
												//TEIN International
												for (var j = 0; j < rUnder_int.length; j++) {
													if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
														rUnder_int[j].drilldown = [];
														rUnder_int[j].resource = 5;
														rUnder_int[j].label = rUnder_int[j].name;
														rUnder_int[j].info = "TEIN International \n " + rUnder_int[i].name;
														rUnder_int[j].color = 'white';
														rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
														rUnderlay_main[i].drilldown.push(rUnder_int[j]);
														//National Research Networks
														for (var k = 0; k < rUnder_ren.length; k++) {
															if (rUnder_ren[k].intID == rUnder_int[j].intID) {
																rUnder_ren[k].drilldown = [];
																rUnder_ren[k].resource = 10;
																rUnder_ren[k].label = rUnder_ren[k].name;
																rUnder_ren[k].info = "Underlay Ren Info \n" + rUnder_ren[k].name;
																rUnder_ren[k].color = 'white';
																rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
																rUnder_int[j].drilldown.push(rUnder_ren[k]);
																//Playground sites
																for (var l = 0; l < rplayground_sites.length; l++) {
																	if (rplayground_sites[l].RENID == rUnder_ren[k].RENID) {
																		rplayground_sites[l].drilldown = [];
																		rplayground_sites[l].resource = 6;
																		rplayground_sites[l].label = rplayground_sites[l].name;
																		rplayground_sites[l].info = "Site Info \n Name: " + rplayground_sites[l].name;
																		rplayground_sites[l].color = 'white';
																		rplayground_sites[l].colorBoder = '#90EE90';
																		rUnder_ren[k].drilldown.push(rplayground_sites[l]);
																		//Physical Boxes
																		for (var m = 0; m < rpBox.length; m++) {
																			if (rpBox[m].site == rplayground_sites[l].siteID) {
																				rpBox[m].drilldown = [];
																				rpBox[m].resource = 1;
																				rpBox[m].label = '' + rpBox[m].boxType;
																				rpBox[m].info = "Box Info \n Box Name: " + rpBox[m].boxName + "\n" + " Site: " + rpBox[m].site;
																				if (rpBox[m].data_ip_status == "GREEN") {
																					rpBox[m].color = 'white';
																					console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
																					console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
																				}
																				else if (rpBox[m].data_ip_status == "ORANGE") {
																					rpBox[m].color = '#ffcc99'; //light Orange
																					console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
																					console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
																				}
																				else {
																					rpBox[m].color = '#ffcce0'; //light red
																					console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
																					console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
																				}
																				rpBox[m].colorBoder = 'MediumSeaGreen'; //MediumSeaGreen
																				rplayground_sites[l].drilldown.push(rpBox[m]);
																				//Tenant VLAN IDs
																				for (var n = 0; n < rVLANs.length; n++) {
																					if (rVLANs[n].boxName == rpBox[m].boxName) {
																						rVLANs[n].drilldown = [];
																						rVLANs[n].resource = 7;
																						rVLANs[n].label = '' + rVLANs[n].VLANID;
																						rVLANs[n].info = "VLAN: " + rVLANs[n].VLANID + "\n" + " Box: " + rVLANs[n].boxName;
																						rVLANs[n].color = 'white';
																						rVLANs[n].colorBoder = '#FFD700'; //Navajo white
																						rpBox[m].drilldown.push(rVLANs[n]);
																						//OpenStack VMs
																						for (var o = 0; o < rVM.length; o++) {
																							console.log(rVM[o].boxName + " " + rVM[o].state);
																							if (rVM[o].box == rVLANs[n].boxName) {
																								rVM[o].drilldown = [];
																								rVM[o].resource = 3;
																								rVM[o].label = '' + rVM[o].name;
																								rVM[o].info = "VM info \n Name: " + rVM[i].name + " - Box: " + rVM[i].boxName;
																								rVM[o].colorBoder = '#FFD700'; //Gold
																								if (rVM[o].state == "Running") {
																									rVM[o].color = 'white';
																									console.log(rVM[o].boxName + " " + rVM[o].state);
																								}
																								else {
																									rVM[o].color = "#ffcce0"; //light red
																								}
																								rVLANs[n].drilldown.push(rVM[o]);
																								var sFlows = { "resource": "11", "label": "SF", "info": "Click to get details about sampled flows", "color": "white", "colorBoder": "#0040ff" }; //Blue
																								rVM[o].drilldown.push(sFlows);
																								sFlows.drilldown = [];
																								var tPackets = { "resource": "12", "label": "TP", "info": "Click to get details about packets", "color": "white", "colorBoder": "#0040ff" }; //Blue
																								sFlows.drilldown.push(tPackets);
																							}
																						}
																						//IoT Hosts
																						for (var p = 0; p < rIoT.length; p++) {
																							if (rIoT[p].box == rVLANs[n].boxName) {
																								rIoT[p].drilldown = [];
																								rIoT[p].resource = 3;
																								rIoT[p].label = '' + rIoT[p].hostID;
																								rIoT[p].info = "IoT info \n Name: " + rIoT[p].hostID + " - Box: " + rIoT[p].ipaddress;
																								rIoT[p].color = 'white';
																								rIoT[p].colorBoder = '#FFD700'; //Gold
																								rVLANs[n].drilldown.push(rIoT[p]);
																								var sFlows = { "resource": "11", "label": "SF", "info": "Click to get details about sampled flows", "color": "white", "colorBoder": "#0040ff" }; //Blue
																								rIoT[p].drilldown.push(sFlows);
																								sFlows.drilldown = [];
																								var tPackets = { "resource": "12", "label": "TP", "info": "Click to get details about packets", "color": "white", "colorBoder": "#0040ff" }; //Blue
																								sFlows.drilldown.push(tPackets);
																							}
																						}
																					}
																				}
																			}
																		}
																	}
																}
															}
														}
													}
												}
												data = rUnderlay_main;
												//console.log(data);
											}
											callback(null, data);
										});
									});
								});
							});
						});
					});
				});
			});
		});
	}

	// getDataMultiSliceVisibilityTenant(userID, callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colConfigMultiUser = db.collection('configuration-multiview-users');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var colunder_ren = db.collection('underlay_REN');
	// 		var playground_sites = db.collection('playground_sites');
	// 		var colpBox = db.collection('pbox-list');
	// 		var colIoTHostList = db.collection('IoT-Host-list');
	// 		var colVMInstance = db.collection('vm-instance-list');
	// 		var flowvisor_slice = db.collection('flowvisor_slice');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				colunder_ren.find({}).toArray(function (err, rUnder_ren) {
	// 					playground_sites.find({}).toArray(function (err, rplayground_sites) {
	// 						colpBox.find({ type: 'B**' }).toArray(function (err, rpBox) {
	// 							flowvisor_slice.find({}).toArray(function (err, rVLANs) {
	// 								colVMInstance.find({}).toArray(function (err, rVM) {
	// 									colIoTHostList.find({}).toArray(function (err, rIoT) {
	// 										//TEIN Main
	// 										for (var i = 0; i < rUnderlay_main.length; i++) {
	// 											rUnderlay_main[i].drilldown = [];
	// 											rUnderlay_main[i].resource = 4;
	// 											rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 											rUnderlay_main[i].info = rUnderlay_main[i].name;
	// 											rUnderlay_main[i].color = 'white';
	// 											rUnderlay_main[i].textBoder = 'LightGrey';
	// 											//TEIN International
	// 											for (var j = 0; j < rUnder_int.length; j++) {
	// 												if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 													rUnder_int[j].drilldown = [];
	// 													rUnder_int[j].resource = 5;
	// 													rUnder_int[j].label = rUnder_int[j].name;
	// 													rUnder_int[j].info = "TEIN International \n " + rUnder_int[i].name;
	// 													rUnder_int[j].color = 'white';
	// 													rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 													rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 													//National Research Networks
	// 													for (var k = 0; k < rUnder_ren.length; k++) {
	// 														if (rUnder_ren[k].intID == rUnder_int[j].intID) {
	// 															rUnder_ren[k].drilldown = [];
	// 															rUnder_ren[k].resource = 10;
	// 															rUnder_ren[k].label = rUnder_ren[k].name;
	// 															rUnder_ren[k].info = "Underlay Ren Info \n" + rUnder_ren[k].name;
	// 															rUnder_ren[k].color = 'white';
	// 															rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
	// 															rUnder_int[j].drilldown.push(rUnder_ren[k]);
	// 															//Playground sites
	// 															for (var l = 0; l < rplayground_sites.length; l++) {
	// 																if (rplayground_sites[l].RENID == rUnder_ren[k].RENID) {
	// 																	rplayground_sites[l].drilldown = [];
	// 																	rplayground_sites[l].resource = 6;
	// 																	rplayground_sites[l].label = rplayground_sites[l].name;
	// 																	rplayground_sites[l].info = "Site Info \n Name: " + rplayground_sites[l].name;
	// 																	rplayground_sites[l].color = 'white';
	// 																	rplayground_sites[l].colorBoder = '#90EE90';
	// 																	rUnder_ren[k].drilldown.push(rplayground_sites[l]);
	// 																	//Physical Boxes
	// 																	for (var m = 0; m < rpBox.length; m++) {
	// 																		if (rpBox[m].site == rplayground_sites[l].siteID) {
	// 																			rpBox[m].drilldown = [];
	// 																			rpBox[m].resource = 1;
	// 																			rpBox[m].label = '' + rpBox[m].boxType;
	// 																			rpBox[m].info = "Box Info \n Box Name: " + rpBox[m].boxName + "\n" + " Site: " + rpBox[m].site;
	// 																			if (rpBox[m].data_ip_status == "GREEN") {
	// 																				rpBox[m].color = 'white';
	// 																				console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																				console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																			}
	// 																			else if (rpBox[m].data_ip_status == "ORANGE") {
	// 																				rpBox[m].color = '#ffcc99'; //light Orange
	// 																				console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																				console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																			}
	// 																			else {
	// 																				rpBox[m].color = '#ffcce0'; //light red
	// 																				console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																				console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																			}
	// 																			rpBox[m].colorBoder = 'MediumSeaGreen'; //MediumSeaGreen
	// 																			rplayground_sites[l].drilldown.push(rpBox[m]);
	// 																			//Tenant VLAN IDs
	// 																			for (var n = 0; n < rVLANs.length; n++) {
	// 																				if (rVLANs[n].boxName == rpBox[m].boxName) {
	// 																					rVLANs[n].drilldown = [];
	// 																					rVLANs[n].resource = 7;
	// 																					rVLANs[n].label = '' + rVLANs[n].VLANID;
	// 																					rVLANs[n].info = "VLAN: " + rVLANs[n].VLANID + "\n" + " Box: " + rVLANs[n].boxName;
	// 																					rVLANs[n].color = 'white';
	// 																					rVLANs[n].colorBoder = '#FFD700'; //Navajo white
	// 																					rpBox[m].drilldown.push(rVLANs[n]);
	// 																					//OpenStack VMs
	// 																					for (var o = 0; o < rVM.length; o++) {
	// 																						console.log(rVM[o].boxName + " " + rVM[o].state);
	// 																						if (rVM[o].box == rVLANs[n].boxName) {
	// 																							rVM[o].drilldown = [];
	// 																							rVM[o].resource = 3;
	// 																							rVM[o].label = '' + rVM[o].name;
	// 																							rVM[o].info = "VM info \n Name: " + rVM[i].name + " - Box: " + rVM[i].boxName;
	// 																							rVM[o].colorBoder = '#FFD700'; //Gold
	// 																							if (rVM[o].state == "Running") {
	// 																								rVM[o].color = 'white';
	// 																								console.log(rVM[o].boxName + " " + rVM[o].state);
	// 																							}
	// 																							else {
	// 																								rVM[o].color = "#ffcce0"; //light red
	// 																							}
	// 																							rVLANs[n].drilldown.push(rVM[o]);
	// 																							var sFlows = { "resource": "11", "label": "SF", "info": "Click to get details about sampled flows", "color": "white", "colorBoder": "#0040ff" }; //Blue
	// 																							rVM[o].drilldown.push(sFlows);
	// 																							sFlows.drilldown = [];
	// 																							var tPackets = { "resource": "12", "label": "TP", "info": "Click to get details about packets", "color": "white", "colorBoder": "#0040ff" }; //Blue
	// 																							sFlows.drilldown.push(tPackets);
	// 																						}
	// 																					}
	// 																					//IoT Hosts
	// 																					for (var p = 0; p < rIoT.length; p++) {
	// 																						if (rIoT[p].box == rVLANs[n].boxName) {
	// 																							rIoT[p].drilldown = [];
	// 																							rIoT[p].resource = 3;
	// 																							rIoT[p].label = '' + rIoT[p].hostID;
	// 																							rIoT[p].info = "IoT info \n Name: " + rIoT[p].hostID + " - Box: " + rIoT[p].ipaddress;
	// 																							rIoT[p].color = 'white';
	// 																							rIoT[p].colorBoder = '#FFD700'; //Gold
	// 																							rVLANs[n].drilldown.push(rIoT[p]);
	// 																							var sFlows = { "resource": "11", "label": "SF", "info": "Click to get details about sampled flows", "color": "white", "colorBoder": "#0040ff" }; //Blue
	// 																							rIoT[p].drilldown.push(sFlows);
	// 																							sFlows.drilldown = [];
	// 																							var tPackets = { "resource": "12", "label": "TP", "info": "Click to get details about packets", "color": "white", "colorBoder": "#0040ff" }; //Blue
	// 																							sFlows.drilldown.push(tPackets);
	// 																						}
	// 																					}
	// 																				}
	// 																			}
	// 																		}
	// 																	}
	// 																}
	// 															}
	// 														}
	// 													}
	// 												}
	// 											}
	// 											data = rUnderlay_main;
	// 											//console.log(data);
	// 										}
	// 										callback(null, data);
	// 									});
	// 								});
	// 							});
	// 						});
	// 					});
	// 				});
	// 			});
	// 		});
	// 	});
	// }
	// //VM's Visualization API
	// getSevenRingAPI(callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var colunder_ren = db.collection('underlay_REN');
	// 		var playground_sites = db.collection('playground_sites');
	// 		var colpBox = db.collection('pbox-list');
	// 		var colVMInstance = db.collection('vm-instance-list');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				colunder_ren.find({}).toArray(function (err, rUnder_ren) {
	// 					playground_sites.find({}).toArray(function (err, rplayground_sites) {
	// 						colpBox.find({ type: 'B**' }).toArray(function (err, rpBox) {
	// 							colVMInstance.find({}).toArray(function (err, rVM) {
	// 								for (var i = 0; i < rUnderlay_main.length; i++) {
	// 									rUnderlay_main[i].drilldown = [];
	// 									rUnderlay_main[i].resource = 1;
	// 									rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 									rUnderlay_main[i].info = "TEIN Main";
	// 									rUnderlay_main[i].color = 'white';
	// 									rUnderlay_main[i].textBoder = 'LightGrey';
	// 									//TEIN International
	// 									for (var j = 0; j < rUnder_int.length; j++) {
	// 										if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 											rUnder_int[j].drilldown = [];
	// 											rUnder_int[j].resource = 2;
	// 											rUnder_int[j].label = rUnder_int[j].name;
	// 											rUnder_int[j].info = "TEIN International: " + rUnder_int[i].name;
	// 											rUnder_int[j].color = 'white';
	// 											rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 											rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 											//National Research Networks
	// 											for (var k = 0; k < rUnder_ren.length; k++) {
	// 												if (rUnder_ren[k].intID == rUnder_int[j].intID) {
	// 													rUnder_ren[k].drilldown = [];
	// 													rUnder_ren[k].resource = 3;
	// 													rUnder_ren[k].label = rUnder_ren[k].name;
	// 													rUnder_ren[k].info = "Underlay REN: " + rUnder_ren[k].name;
	// 													rUnder_ren[k].color = 'white';
	// 													rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
	// 													rUnder_int[j].drilldown.push(rUnder_ren[k]);
	// 													//Playground Sites
	// 													for (var l = 0; l < rplayground_sites.length; l++) {
	// 														if (rplayground_sites[l].RENID == rUnder_ren[k].RENID) {
	// 															rplayground_sites[l].drilldown = [];
	// 															rplayground_sites[l].resource = 4;
	// 															rplayground_sites[l].label = rplayground_sites[l].name;
	// 															rplayground_sites[l].info = "Site Name: " + rplayground_sites[l].name;
	// 															rplayground_sites[l].color = 'white';
	// 															rplayground_sites[l].colorBoder = '#90EE90';
	// 															rUnder_ren[k].drilldown.push(rplayground_sites[l]);
	// 															//Physical Boxes
	// 															for (var m = 0; m < rpBox.length; m++) {
	// 																if (rpBox[m].site == rplayground_sites[l].siteID) {
	// 																	rpBox[m].drilldown = [];
	// 																	rpBox[m].resource = 5;
	// 																	rpBox[m].label = '' + rpBox[m].boxType;
	// 																	rpBox[m].info = "Box Name: " + rpBox[m].boxName + "\n" + " Site: " + rpBox[m].site;
	// 																	if (rpBox[m].data_ip_status == "GREEN") {
	// 																		rpBox[m].color = 'white';
	// 																		console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																		console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																	}
	// 																	else if (rpBox[m].data_ip_status == "ORANGE") {
	// 																		rpBox[m].color = '#ffcc99'; //light Orange
	// 																		console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																		console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																	}
	// 																	else {
	// 																		rpBox[m].color = '#ffcce0'; //light red
	// 																		console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																		console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																	}
	// 																	rpBox[m].colorBoder = 'MediumSeaGreen'; //MediumSeaGreen
	// 																	rplayground_sites[l].drilldown.push(rpBox[m]);
	// 																	//OpenStack VMs
	// 																	for (var o = 0; o < rVM.length; o++) {
	// 																		if (rVM[o].box == rpBox[m].boxName) {
	// 																			rVM[o].drilldown = [];
	// 																			rVM[o].resource = 6;
	// 																			rVM[o].label = '' + rVM[o].name;
	// 																			rVM[o].info = "VM: " + rVM[o].name + " Box: " + rpBox[m].boxName;
	// 																			rVM[o].colorBoder = '#FFD700'; //Gold
	// 																			if (rVM[o].state == "Running") {
	// 																				rVM[o].color = 'white';
	// 																			}
	// 																			else {
	// 																				rVM[o].color = "#ffcce0"; //light red
	// 																			}
	// 																			rpBox[m].drilldown.push(rVM[o]);
	// 																			var sFlows = { "resource": "11", "label": "SF", "info": "Click to get details about sampled flows", "color": "white", "colorBoder": "#0040ff" }; //Blue
	// 																			rVM[o].drilldown.push(sFlows);
	// 																			//sFlows.drilldown = [];
	// 																			//var tPackets = {"resource": "12", "label": "TP", "info": "Click to get details about packets", "color": "white", "colorBoder": "#0040ff"}; //Blue
	// 																			//sFlows.drilldown.push(tPackets);
	// 																		}
	// 																	}
	// 																}
	// 															}
	// 														}
	// 													}
	// 												}
	// 											}
	// 										}
	// 									}
	// 									data = rUnderlay_main;
	// 									console.log(data);
	// 								}
	// 								callback(null, data);
	// 							});
	// 						});
	// 					});
	// 				});
	// 			});
	// 		});
	// 	});
	// }
	// //VM's Visualization API
	// getEightRingAPI(callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var colunder_ren = db.collection('underlay_REN');
	// 		var playground_sites = db.collection('playground_sites');
	// 		var colpBox = db.collection('pbox-list');
	// 		var colVMInstance = db.collection('vm-instance-list');
	// 		var colWorkload = db.collection('workload-list');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				colunder_ren.find({}).toArray(function (err, rUnder_ren) {
	// 					playground_sites.find({}).toArray(function (err, rplayground_sites) {
	// 						colpBox.find({ type: 'B**' }).toArray(function (err, rpBox) {
	// 							colVMInstance.find({}).toArray(function (err, rVM) {
	// 								colWorkload.find({}).toArray(function (err, rWorkload) {
	// 									for (var i = 0; i < rUnderlay_main.length; i++) {
	// 										rUnderlay_main[i].drilldown = [];
	// 										rUnderlay_main[i].resource = 1;
	// 										rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 										rUnderlay_main[i].info = "TEIN Main";
	// 										rUnderlay_main[i].color = 'white';
	// 										rUnderlay_main[i].textBoder = 'LightGrey';
	// 										//TEIN International
	// 										for (var j = 0; j < rUnder_int.length; j++) {
	// 											if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 												rUnder_int[j].drilldown = [];
	// 												rUnder_int[j].resource = 2;
	// 												rUnder_int[j].label = rUnder_int[j].name;
	// 												rUnder_int[j].info = "TEIN International: " + rUnder_int[i].name;
	// 												rUnder_int[j].color = 'white';
	// 												rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 												rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 												//National Research Networks
	// 												for (var k = 0; k < rUnder_ren.length; k++) {
	// 													if (rUnder_ren[k].intID == rUnder_int[j].intID) {
	// 														rUnder_ren[k].drilldown = [];
	// 														rUnder_ren[k].resource = 3;
	// 														rUnder_ren[k].label = rUnder_ren[k].name;
	// 														rUnder_ren[k].info = "Underlay REN: " + rUnder_ren[k].name;
	// 														rUnder_ren[k].color = 'white';
	// 														rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
	// 														rUnder_int[j].drilldown.push(rUnder_ren[k]);
	// 														//Playground Sites
	// 														for (var l = 0; l < rplayground_sites.length; l++) {
	// 															if (rplayground_sites[l].RENID == rUnder_ren[k].RENID) {
	// 																rplayground_sites[l].drilldown = [];
	// 																rplayground_sites[l].resource = 4;
	// 																rplayground_sites[l].label = rplayground_sites[l].name;
	// 																rplayground_sites[l].info = "Site Name: " + rplayground_sites[l].name;
	// 																rplayground_sites[l].color = 'white';
	// 																rplayground_sites[l].colorBoder = '#90EE90';
	// 																rUnder_ren[k].drilldown.push(rplayground_sites[l]);
	// 																//Physical Boxes
	// 																for (var m = 0; m < rpBox.length; m++) {
	// 																	if (rpBox[m].site == rplayground_sites[l].siteID) {
	// 																		rpBox[m].drilldown = [];
	// 																		rpBox[m].resource = 5;
	// 																		rpBox[m].label = '' + rpBox[m].boxType;
	// 																		rpBox[m].info = "Box Name: " + rpBox[m].boxName + "\n" + " Site: " + rpBox[m].site;
	// 																		if (rpBox[m].data_ip_status == "GREEN") {
	// 																			rpBox[m].color = 'white';
	// 																			console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																			console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																		}
	// 																		else if (rpBox[m].data_ip_status == "ORANGE") {
	// 																			rpBox[m].color = '#ffe680'; //light Orange
	// 																			console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																			console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																		}
	// 																		else {
	// 																			rpBox[m].color = '#ff66a3'; //light red
	// 																			console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																			console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																		}
	// 																		rpBox[m].colorBoder = 'MediumSeaGreen'; //MediumSeaGreen
	// 																		rplayground_sites[l].drilldown.push(rpBox[m]);
	// 																		//OpenStack VMs
	// 																		for (var o = 0; o < rVM.length; o++) {
	// 																			if (rVM[o].box == rpBox[m].boxName) {
	// 																				rVM[o].drilldown = [];
	// 																				rVM[o].resource = 6;
	// 																				rVM[o].label = '' + rVM[o].name;
	// 																				rVM[o].info = "VM: " + rVM[o].name + " Box: " + rpBox[m].boxName;
	// 																				rVM[o].colorBoder = '#FFD700'; //Gold
	// 																				if (rVM[o].state == "Running") {
	// 																					rVM[o].color = 'white';
	// 																				}
	// 																				else {
	// 																					rVM[o].color = "#ff66a3"; //light red
	// 																				}
	// 																				rpBox[m].drilldown.push(rVM[o]);
	// 																				var sFlows = { "resource": "7", "label": "SF", "drilldown": [], "info": "Click to get details about sampled flows", "color": "white", "colorBoder": "#0040ff" }; //Blue
	// 																				rVM[o].drilldown.push(sFlows);
	// 																				//Workloads
	// 																				for (var p = 0; p < rWorkload.length; p++) {
	// 																					if (rWorkload[p].vmInstance == rVM[o].name) {
	// 																						rWorkload[p].drilldown = [];
	// 																						rWorkload[p].resource = 8;
	// 																						rWorkload[p].label = '' + rWorkload[p].workloadName;
	// 																						rWorkload[p].info = "Workload: " + rWorkload[p].name + " VM: " + rVM[o].name;
	// 																						rWorkload[p].colorBoder = '#ff66ff'; //Light Purple
	// 																						if (rWorkload[p].state == "Running") {
	// 																							rWorkload[p].color = 'white';
	// 																						}
	// 																						else {
	// 																							rWorkload[p].color = "#ff66a3"; //light red
	// 																						}
	// 																						sFlows.drilldown.push(rWorkload[p]);
	// 																					}
	// 																				}
	// 																			}
	// 																		}
	// 																	}
	// 																}
	// 															}
	// 														}
	// 													}
	// 												}
	// 											}
	// 										}
	// 										data = rUnderlay_main;
	// 										console.log(data);
	// 									}
	// 									callback(null, data);
	// 								});
	// 							});
	// 						});
	// 					});
	// 				});
	// 			});
	// 		});
	// 	});
	// }
	// //ManhNT end
	// //TEIN Internatioal Visualization API
	// getTwoRingAPI(callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				//TEIN Main
	// 				for (var i = 0; i < rUnderlay_main.length; i++) {
	// 					rUnderlay_main[i].drilldown = [];
	// 					rUnderlay_main[i].resource = 1;
	// 					rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 					rUnderlay_main[i].info = "TEIN Main";
	// 					rUnderlay_main[i].color = 'black';
	// 					rUnderlay_main[i].textBoder = 'LightGrey';
	// 					//TEIN International
	// 					for (var j = 0; j < rUnder_int.length; j++) {
	// 						if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 							rUnder_int[j].drilldown = [];
	// 							rUnder_int[j].resource = 2;
	// 							rUnder_int[j].label = rUnder_int[j].name;
	// 							rUnder_int[j].info = "TEIN International: " + rUnder_int[i].name;
	// 							rUnder_int[j].color = 'white';
	// 							rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 							rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 						}
	// 					}
	// 					data = rUnderlay_main;
	// 					console.log(data);
	// 				}
	// 				callback(null, data);
	// 			});
	// 		});
	// 	});
	// }
	// //REN Visualization API
	// getThreeRingAPI(callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var colunder_ren = db.collection('underlay_REN');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				colunder_ren.find({}).toArray(function (err, rUnder_ren) {
	// 					for (var i = 0; i < rUnderlay_main.length; i++) {
	// 						rUnderlay_main[i].drilldown = [];
	// 						rUnderlay_main[i].resource = 1;
	// 						rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 						rUnderlay_main[i].info = "TEIN Main";
	// 						rUnderlay_main[i].color = 'white';
	// 						rUnderlay_main[i].textBoder = 'LightGrey';
	// 						//TEIN International
	// 						for (var j = 0; j < rUnder_int.length; j++) {
	// 							if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 								rUnder_int[j].drilldown = [];
	// 								rUnder_int[j].resource = 2;
	// 								rUnder_int[j].label = rUnder_int[j].name;
	// 								rUnder_int[j].info = "TEIN International: " + rUnder_int[i].name;
	// 								rUnder_int[j].color = 'white';
	// 								rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 								rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 								//National Research Networks
	// 								for (var k = 0; k < rUnder_ren.length; k++) {
	// 									if (rUnder_ren[k].intID == rUnder_int[j].intID) {
	// 										rUnder_ren[k].drilldown = [];
	// 										rUnder_ren[k].resource = 3;
	// 										rUnder_ren[k].label = rUnder_ren[k].name;
	// 										rUnder_ren[k].info = "Underlay REN: " + rUnder_ren[k].name;
	// 										rUnder_ren[k].color = 'white';
	// 										rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
	// 										rUnder_int[j].drilldown.push(rUnder_ren[k]);
	// 									}
	// 								}
	// 							}
	// 						}
	// 						data = rUnderlay_main;
	// 						console.log(data);
	// 					}
	// 					callback(null, data);
	// 				});
	// 			});
	// 		});
	// 	});
	// }
	// //Sites Visualization API
	// getFourRingAPI(callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var colunder_ren = db.collection('underlay_REN');
	// 		var playground_sites = db.collection('playground_sites');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				colunder_ren.find({}).toArray(function (err, rUnder_ren) {
	// 					playground_sites.find({}).toArray(function (err, rplayground_sites) {
	// 						for (var i = 0; i < rUnderlay_main.length; i++) {
	// 							rUnderlay_main[i].drilldown = [];
	// 							rUnderlay_main[i].resource = 1;
	// 							rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 							rUnderlay_main[i].info = "TEIN Main";
	// 							rUnderlay_main[i].color = 'white';
	// 							rUnderlay_main[i].textBoder = 'LightGrey';
	// 							//TEIN International
	// 							for (var j = 0; j < rUnder_int.length; j++) {
	// 								if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 									rUnder_int[j].drilldown = [];
	// 									rUnder_int[j].resource = 2;
	// 									rUnder_int[j].label = rUnder_int[j].name;
	// 									rUnder_int[j].info = "TEIN International: " + rUnder_int[i].name;
	// 									rUnder_int[j].color = 'white';
	// 									rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 									rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 									//National Research Networks
	// 									for (var k = 0; k < rUnder_ren.length; k++) {
	// 										if (rUnder_ren[k].intID == rUnder_int[j].intID) {
	// 											rUnder_ren[k].drilldown = [];
	// 											rUnder_ren[k].resource = 3;
	// 											rUnder_ren[k].label = rUnder_ren[k].name;
	// 											rUnder_ren[k].info = "Underlay REN: " + rUnder_ren[k].name;
	// 											rUnder_ren[k].color = 'white';
	// 											rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
	// 											rUnder_int[j].drilldown.push(rUnder_ren[k]);
	// 											//Playground Sites
	// 											for (var l = 0; l < rplayground_sites.length; l++) {
	// 												if (rplayground_sites[l].RENID == rUnder_ren[k].RENID) {
	// 													rplayground_sites[l].drilldown = [];
	// 													rplayground_sites[l].resource = 4;
	// 													rplayground_sites[l].label = rplayground_sites[l].name;
	// 													rplayground_sites[l].info = "Site Name: " + rplayground_sites[l].name;
	// 													rplayground_sites[l].color = 'white';
	// 													rplayground_sites[l].colorBoder = '#90EE90';
	// 													rUnder_ren[k].drilldown.push(rplayground_sites[l]);
	// 												}
	// 											}
	// 										}
	// 									}
	// 								}
	// 							}
	// 							data = rUnderlay_main;
	// 							console.log(data);
	// 						}
	// 						callback(null, data);
	// 					});
	// 				});
	// 			});
	// 		});
	// 	});
	// }
	// //SmartX Boxes Visualization API
	// getFiveRingAPI(callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var colunder_ren = db.collection('underlay_REN');
	// 		var playground_sites = db.collection('playground_sites');
	// 		var colpBox = db.collection('pbox-list');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				colunder_ren.find({}).toArray(function (err, rUnder_ren) {
	// 					playground_sites.find({}).toArray(function (err, rplayground_sites) {
	// 						colpBox.find({ type: 'B**' }).toArray(function (err, rpBox) {
	// 							for (var i = 0; i < rUnderlay_main.length; i++) {
	// 								rUnderlay_main[i].drilldown = [];
	// 								rUnderlay_main[i].resource = 1;
	// 								rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 								rUnderlay_main[i].info = "TEIN Main";
	// 								rUnderlay_main[i].color = 'white';
	// 								rUnderlay_main[i].textBoder = 'LightGrey';
	// 								//TEIN International
	// 								for (var j = 0; j < rUnder_int.length; j++) {
	// 									if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 										rUnder_int[j].drilldown = [];
	// 										rUnder_int[j].resource = 2;
	// 										rUnder_int[j].label = rUnder_int[j].name;
	// 										rUnder_int[j].info = "TEIN International: " + rUnder_int[i].name;
	// 										rUnder_int[j].color = 'white';
	// 										rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 										rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 										//National Research Networks
	// 										for (var k = 0; k < rUnder_ren.length; k++) {
	// 											if (rUnder_ren[k].intID == rUnder_int[j].intID) {
	// 												rUnder_ren[k].drilldown = [];
	// 												rUnder_ren[k].resource = 3;
	// 												rUnder_ren[k].label = rUnder_ren[k].name;
	// 												rUnder_ren[k].info = "Underlay REN: " + rUnder_ren[k].name;
	// 												rUnder_ren[k].color = 'white';
	// 												rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
	// 												rUnder_int[j].drilldown.push(rUnder_ren[k]);
	// 												//Playground Sites
	// 												for (var l = 0; l < rplayground_sites.length; l++) {
	// 													if (rplayground_sites[l].RENID == rUnder_ren[k].RENID) {
	// 														rplayground_sites[l].drilldown = [];
	// 														rplayground_sites[l].resource = 4;
	// 														rplayground_sites[l].label = rplayground_sites[l].name;
	// 														rplayground_sites[l].info = "Site Name: " + rplayground_sites[l].name;
	// 														rplayground_sites[l].color = 'white';
	// 														rplayground_sites[l].colorBoder = '#90EE90';
	// 														rUnder_ren[k].drilldown.push(rplayground_sites[l]);
	// 														//Physical Boxes
	// 														for (var m = 0; m < rpBox.length; m++) {
	// 															if (rpBox[m].site == rplayground_sites[l].siteID) {
	// 																rpBox[m].drilldown = [];
	// 																rpBox[m].resource = 5;
	// 																rpBox[m].label = '' + rpBox[m].boxType;
	// 																rpBox[m].info = "Box Info \n Box Name: " + rpBox[m].boxName + "\n" + " Site: " + rpBox[m].site;
	// 																if (rpBox[m].data_ip_status == "GREEN") {
	// 																	rpBox[m].color = 'white';
	// 																	console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																	console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																}
	// 																else if (rpBox[m].data_ip_status == "ORANGE") {
	// 																	rpBox[m].color = '#ffcc99'; //light Orange
	// 																	console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																	console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																}
	// 																else {
	// 																	rpBox[m].color = '#ffcce0'; //light red
	// 																	console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																	console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																}
	// 																rpBox[m].colorBoder = 'MediumSeaGreen'; //MediumSeaGreen
	// 																rplayground_sites[l].drilldown.push(rpBox[m]);
	// 															}
	// 														}
	// 													}
	// 												}
	// 											}
	// 										}
	// 									}
	// 								}
	// 								data = rUnderlay_main;
	// 								console.log(data);
	// 							}
	// 							callback(null, data);
	// 						});
	// 					});
	// 				});
	// 			});
	// 		});
	// 	});
	// }
	// //VM's Visualization API
	// getSixRingAPI(callback) {
	// 	MongoClient.connect(mongourl, function (err, client) {
	// 		const db = client.db('multiviewdb');
	// 		var colUnderlay_main = db.collection('underlay_main');
	// 		var colunder_int = db.collection('underlay_int');
	// 		var colunder_ren = db.collection('underlay_REN');
	// 		var playground_sites = db.collection('playground_sites');
	// 		var colpBox = db.collection('pbox-list');
	// 		var colVMInstance = db.collection('vm-instance-list');
	// 		var data = [];
	// 		var main = 0;
	// 		colUnderlay_main.find({}).toArray(function (err, rUnderlay_main) {
	// 			colunder_int.find({}).toArray(function (err, rUnder_int) {
	// 				colunder_ren.find({}).toArray(function (err, rUnder_ren) {
	// 					playground_sites.find({}).toArray(function (err, rplayground_sites) {
	// 						colpBox.find({ type: 'B**' }).toArray(function (err, rpBox) {
	// 							colVMInstance.find({}).toArray(function (err, rVM) {
	// 								for (var i = 0; i < rUnderlay_main.length; i++) {
	// 									rUnderlay_main[i].drilldown = [];
	// 									rUnderlay_main[i].resource = 1;
	// 									rUnderlay_main[i].label = rUnderlay_main[i].name;
	// 									rUnderlay_main[i].info = "TEIN Main";
	// 									rUnderlay_main[i].color = 'white';
	// 									rUnderlay_main[i].textBoder = 'LightGrey';
	// 									//TEIN International
	// 									for (var j = 0; j < rUnder_int.length; j++) {
	// 										if (rUnder_int[j].mainID == rUnderlay_main[i].mainID) {
	// 											rUnder_int[j].drilldown = [];
	// 											rUnder_int[j].resource = 2;
	// 											rUnder_int[j].label = rUnder_int[j].name;
	// 											rUnder_int[j].info = "TEIN International: " + rUnder_int[i].name;
	// 											rUnder_int[j].color = 'white';
	// 											rUnder_int[j].colorBoder = 'LightGrey '; // Light Grey
	// 											rUnderlay_main[i].drilldown.push(rUnder_int[j]);
	// 											//National Research Networks
	// 											for (var k = 0; k < rUnder_ren.length; k++) {
	// 												if (rUnder_ren[k].intID == rUnder_int[j].intID) {
	// 													rUnder_ren[k].drilldown = [];
	// 													rUnder_ren[k].resource = 3;
	// 													rUnder_ren[k].label = rUnder_ren[k].name;
	// 													rUnder_ren[k].info = "Underlay REN: " + rUnder_ren[k].name;
	// 													rUnder_ren[k].color = 'white';
	// 													rUnder_ren[k].colorBoder = 'LightGrey'; // Grey
	// 													rUnder_int[j].drilldown.push(rUnder_ren[k]);
	// 													//Playground Sites
	// 													for (var l = 0; l < rplayground_sites.length; l++) {
	// 														if (rplayground_sites[l].RENID == rUnder_ren[k].RENID) {
	// 															rplayground_sites[l].drilldown = [];
	// 															rplayground_sites[l].resource = 4;
	// 															rplayground_sites[l].label = rplayground_sites[l].name;
	// 															rplayground_sites[l].info = "Site Name: " + rplayground_sites[l].name;
	// 															rplayground_sites[l].color = 'white';
	// 															rplayground_sites[l].colorBoder = '#90EE90';
	// 															rUnder_ren[k].drilldown.push(rplayground_sites[l]);
	// 															//Physical Boxes
	// 															for (var m = 0; m < rpBox.length; m++) {
	// 																if (rpBox[m].site == rplayground_sites[l].siteID) {
	// 																	rpBox[m].drilldown = [];
	// 																	rpBox[m].resource = 5;
	// 																	rpBox[m].label = '' + rpBox[m].boxType;
	// 																	rpBox[m].info = "Box Name: " + rpBox[m].boxName + "\n" + " Site: " + rpBox[m].site;
	// 																	if (rpBox[m].data_ip_status == "GREEN") {
	// 																		rpBox[m].color = 'white';
	// 																		console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																		console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																	}
	// 																	else if (rpBox[m].data_ip_status == "ORANGE") {
	// 																		rpBox[m].color = '#ffcc99'; //light Orange
	// 																		console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																		console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																	}
	// 																	else {
	// 																		rpBox[m].color = '#ffcce0'; //light red
	// 																		console.log(rpBox[m].boxName + " " + rpBox[m].data_ip_status);
	// 																		console.log(rpBox[m].boxName + ' ' + rpBox[m].color);
	// 																	}
	// 																	rpBox[m].colorBoder = 'MediumSeaGreen'; //MediumSeaGreen
	// 																	rplayground_sites[l].drilldown.push(rpBox[m]);
	// 																	//OpenStack VMs
	// 																	for (var o = 0; o < rVM.length; o++) {
	// 																		if (rVM[o].box == rpBox[m].boxName) {
	// 																			rVM[o].drilldown = [];
	// 																			rVM[o].resource = 6;
	// 																			rVM[o].label = '' + rVM[o].name;
	// 																			rVM[o].info = "VM: " + rVM[o].name + " Box: " + rpBox[m].boxName;
	// 																			rVM[o].colorBoder = '#FFD700'; //Gold
	// 																			if (rVM[o].state == "Running") {
	// 																				rVM[o].color = 'white';
	// 																			}
	// 																			else {
	// 																				rVM[o].color = "#ffcce0"; //light red
	// 																			}
	// 																			rpBox[m].drilldown.push(rVM[o]);
	// 																			//var sFlows = {"resource": "11", "label": "SF", "info": "Click to get details about sampled flows", "color": "white", "colorBoder": "#0040ff"}; //Blue
	// 																			//rVM[o].drilldown.push(sFlows);
	// 																			//sFlows.drilldown = [];
	// 																			//var tPackets = {"resource": "12", "label": "TP", "info": "Click to get details about packets", "color": "white", "colorBoder": "#0040ff"}; //Blue
	// 																			//sFlows.drilldown.push(tPackets);
	// 																		}
	// 																	}
	// 																}
	// 															}
	// 														}
	// 													}
	// 												}
	// 											}
	// 										}
	// 									}
	// 									data = rUnderlay_main;
	// 									console.log(data);
	// 								}
	// 								callback(null, data);
	// 							});
	// 						});
	// 					});
	// 				});
	// 			});
	// 		});
	// 	});
	// }

	// //Get pBoxes List From MongoDB New
	// getpBoxList (box_type, callback) {
	// 	//var boxes = {};//sboxes, cboxes, oboxes;
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		//console.log('Physical Boxes List: ');
	// 		var collection = db.collection("pbox-list");
	// 		//collection.find({type: 'B**'},{box: true, host: true, management_ip: true, management_ip_status: true, data_ip: true, data_ip_status: true, control_ip: true, control_ip_status: true, _id: false}).sort({host: -1}).toArray(function(err, boxes){
	// 		//collection.find({$or:[{boxType: 'S'},{boxType: 'C'},{boxType: 'O'}]},{boxID: true, boxName: true, management_ip: true, boxType: true, management_ip: true, management_ip_status: true, data1_ip: true, data1_ip_status: true, control_ip: true, control_ip_status: true, _id: false}).sort({boxName: -1}).toArray(function(err, boxes){
	// 		collection.find({ boxType: box_type, type: 'B**' }, { boxID: true, boxName: true, boxType: true, site: true, management_ip: true, management_ip_status: true, data_ip: true, data_ip_status: true, control_ip: true, control_ip_status: true, _id: false }).sort({ boxName: 1 }).toArray(function (err, boxes) {
	// 			callback(null, boxes);
	// 			db.close();
	// 		});
	// 	});
	// }


	// //Get Virtual Switches List From MongoDB New
	// getvSwitchList(switch_type, callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('OVS bridges List: ');
	// 		var collection = db.collection("vswitch-list");
	// 		collection.find({ boxType: switch_type }, { boxType: true, bridge: true, topologyorder: true, boxDevType: true, _id: false }).sort({ topologyorder: 1 }).toArray(function (err, switchList) {
	// 			callback(null, switchList);
	// 			db.close();
	// 		});
	// 	});
	// }


	// //Get Virtual Switches Status From MongoDB New
	// getovsBridgeStatus (box_type, callback) {
	// 	MongoClient.connect(mongourl, function (err, db) {
	// 		console.log('OVS Bridge Status: ');
	// 		var collection = db.collection("vswitch-status");
	// 		collection.find({ boxType: box_type }, { boxType: true, boxID: true, bridge: true, status: true, _id: false }).sort({ boxID: -1 }).toArray(function (err, ovsBridgeStatus) {
	// 			//db.close();
	// 			callback(null, ovsBridgeStatus);
	// 			db.close();
	// 		});
	// 	});
	// }
}

class VisibilityCenterConfig {
	constructor() {
		this.vCenterConfig = require("./config.json").vCenter;
	}
	
	getHost (){
		return this.vCenterConfig.host;
	}

	getPort() {
		return this.vCenterConfig.port;
	}

	getAuthPort(){
		return this.vCenterConfig.authPort;
	}
}

class PlaygroundConfig {
	constructor() {
		this.playgroundConfig = require("./config.json").playground;
	}

	getCloudControllerHost(){
		return this.playgroundConfig.cloudControllerHost;
	}

	getSDNControllerHost(){
		return this.playgroundConfig.sdnControllerHost;
	}
}

module.exports.ResourceProvider = new ResourceProvider();
module.exports.VisibilityCenterConfig = new VisibilityCenterConfig();
module.exports.PlaygroundConfig = new PlaygroundConfig();
//exports.UserProvider = UserProvider;
