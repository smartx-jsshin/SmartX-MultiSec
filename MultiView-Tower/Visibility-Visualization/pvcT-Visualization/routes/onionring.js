module.exports = function(provider){

	var router = require('express').Router();
	var resourceProvider = provider;
	
	// var username = "admin";

	//The route was changed from /onionring/onionringviewops
	router.get('/onionring2d', function(req, res){
		var data = null;
        console.log("[Router | onionring/onionring2d] Route to /onionring/onionring2d");

		resourceProvider.getOnionRingData(function(error, databj){
			data = databj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionring/onionring2d.pug', {onionRingData: data});
			}
		}
	});

	router.get('/onionring3d', function(req, res){
		var data = null;
        console.log("[Router | onionring/onionring3d] Route to /onionring/onionring3d");

		resourceProvider.getOnionRing3DData(function(error, databj){
			data = databj;
			console.log(data);
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionring/onionring3d.pug', {onionRing3DData: data});
			}
		}
	});

	router.get('/onionring3d/update', async function(req, res){
		res.set({
			"Content-Type": "text/event-stream",
			"Cache-Control": "no-cache",
			"Connection": "keep-alive",
			"Access-Control-Allow-Origin": "*"
		});
		res.flushHeaders(); // flush the headers to establish SSE with client
	
		const mongoCol = await resourceProvider.getMongoSecLevelCollection("multi-sec-boxes");
		var boxStatusList = await mongoCol.find().toArray();

		// console.log(mongoCol);

		const changeStream = mongoCol.watch({ fullDocument: 'updateLookup' });
		changeStream.on("change", (changeEvent) => { 
			console.log(changeEvent);
			var respMsg = null;
			if (changeEvent.operationType === "delete"){
				boxStatusList.some(function (boxStatus, idx) {
					if (boxStatus["_id"] === changeEvent.documentKey["_id"]){				
						boxStatusList.splice(idx, 1);

						respMsg = {};
						respMsg.name = boxStatus.name;
						respMsg.where = boxStatus.where;
						respMsg.tier = boxStatus.tier;
						respMsg.operationType = "delete"
						return true;
					}
				});
			} else if(changeEvent.operationType === "insert"){
				boxStatusList.push(changeEvent.fullDocument);

				respMsg = changeEvent.fullDocument;
				delete respMsg["_id"];
				respMsg.operationType = changeEvent.operationType;

			} 
			else if(changeEvent.operationType === "update"){
				respMsg = changeEvent.fullDocument;
				delete respMsg["_id"];
				respMsg.operationType = changeEvent.operationType;
			}
			else{
				// boxStatusList.some(function (boxStatus, idx) {
				// 	if (boxStatus["_id"] === changeEvent.documentKey["_id"]){				
				// 		boxStatusList.splice(idx, 1);

				// 		respMsg = {};
				// 		respMsg.name = boxStatus.name;
				// 		respMsg.where = boxStatus.where;
				// 		respMsg.tier = boxStatus.tier;
				// 		respMsg.operationType = "delete"
				// 		return true;
				// 	}
				// });

				respMsg = changeEvent.fullDocument;
				delete respMsg["_id"];
				respMsg.operationType = changeEvent.operationType;
			}
			// res.write(`data: ${JSON.stringify({msg: respMsg})} \n\n`);
			res.write(`data: ${JSON.stringify(respMsg)} \n\n`);

		});

		setTimeout(function(){
			mongoCol.updateOne(
				{"name": "P-Center"},
				{$set: {"resource": "2"} }
				);
		}, 1000);

		// setTimeout(function(){
		// 	// send HTTP request to updateUrl
		// 	res.write(`data: ${JSON.stringify({msg: "Hello"})} \n\n`);
		// 	console.log("Test");
		// }, 1000);
		
		// res.on('close', () => {
		// 	console.log('client dropped me');
		// 	res.end();
		// });
	});
	
	// router.get('/onionringviewtenant/*', function(req, res){
	// 	var data = null;
	// 	console.log(username);
	// 	resourceProvider.getDataMultiSliceVisibilityTenant('demo', function(error, databj)
	// 	{
	// 		data = databj;
	// 		showView();
	// 	});
	// 	resourceProvider.getControllerList(function(error, controllerobj)
	// 	{
	// 		controllerList = controllerobj;
	// 		console.log(controllerList);
	// 		showView();
	// 	});
	// 	function showView()
	// 	{
	// 		if(data !== null && controllerList !== null){
	// 			//console.log('Onion-ring Visualization Rendering'+data);
	// 			res.render('onionringviewtenant.jade', {title: 'Onion-ring-based Visualization', data : JSON.stringify(data), controllerList : JSON.stringify(controllerList)});
	// 	}
	//   }
	// });
	
	
	// // Route for TEIN International API Call
	// router.get('/teinint', function(req, res){
	// 	var data = null;
		
	// 	resourceProvider.getTwoRingAPI(function(error, dataobj)
	// 	{
	// 		data = dataobj;
	// 		showView();
	// 	});
		
	// 	function showView()
	// 	{
	// 		if(data !== null){
	// 			res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
	// 		}
	// 	}
	// });
	
	// // Route for REN API Call
	// router.get('/ren', function(req, res){
	// 	var data = null;
		
	// 	resourceProvider.getThreeRingAPI(function(error, dataobj)
	// 	{
	// 		data = dataobj;
	// 		showView();
	// 	});
		
	// 	function showView()
	// 	{
	// 		if(data !== null){
	// 			res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
	// 		}
	// 	}
	// });
	
	// // Route for Sites API Call
	// router.get('/sites', function(req, res){
	// 	var data = null;
		
	// 	resourceProvider.getFourRingAPI(function(error, dataobj)
	// 	{
	// 		data = dataobj;
	// 		showView();
	// 	});
		
	// 	function showView()
	// 	{
	// 		if(data !== null){
	// 			res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
	// 		}
	// 	}
	// });
	
	// // Route for SmartX Boxes/Micro-Boxes API Call
	// router.get('/boxes', function(req, res){
	// 	var data = null;
		
	// 	resourceProvider.getFiveRingAPI(function(error, dataobj)
	// 	{
	// 		data = dataobj;
	// 		showView();
	// 	});
		
	// 	function showView()
	// 	{
	// 		if(data !== null){
	// 			res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
	// 		}
	// 	}
	// });
	
	// // Route for SmartX Boxes/Micro-Boxes API Call
	// router.get('/vms', function(req, res){
	// 	var data = null;
		
	// 	resourceProvider.getSixRingAPI(function(error, dataobj)
	// 	{
	// 		data = dataobj;
	// 		showView();
	// 	});
		
	// 	function showView()
	// 	{
	// 		if(data !== null){
	// 			res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
	// 		}
	// 	}
	// });
	
	// // Route for SmartX Boxes/Micro-Boxes API Call
	// router.get('/flows', function(req, res){
	// 	var data = null;
		
	// 	resourceProvider.getSevenRingAPI(function(error, dataobj)
	// 	{
	// 		data = dataobj;
	// 		showView();
	// 	});
		
	// 	function showView()
	// 	{
	// 		if(data !== null){
	// 			res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
	// 		}
	// 	}
	// });
	
	// // Route for SmartX Boxes/Micro-Boxes API Call
	// router.get('/workload', function(req, res){
	// 	var data = null;
		
	// 	resourceProvider.getEightRingAPI(function(error, dataobj)
	// 	{
	// 		data = dataobj;
	// 		showView();
	// 	});
		
	// 	function showView()
	// 	{
	// 		if(data !== null){
	// 			res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
	// 		}
	// 	}
	// });

	return router;
}