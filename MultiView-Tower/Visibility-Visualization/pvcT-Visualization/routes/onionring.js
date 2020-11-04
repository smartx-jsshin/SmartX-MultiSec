module.exports = function(provider){

	var router = require('express').Router();
	var resourceProvider = provider;
	
	var username = "admin";

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
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionring/onionring3d.pug', {onionRing3DData: data});
			}
		}
	});

	router.get('/onionring3d/update', function(req, res){
		res.set({
			"Content-Type": "text/event-stream",
			"Cache-Control": "no-cache",
			"Connection": "keep-alive",
			"Access-Control-Allow-Origin": "*"
		});
		res.flushHeaders(); // flush the headers to establish SSE with client
	
		// let counter = 0;
		// let interValID = setInterval(() => {
		// 	counter++;
		// 	if (counter >= 10) {
		// 		clearInterval(interValID);
		// 		res.end(); // terminates SSE session
		// 		return;
		// 	}
		// 	res.write(`data: ${JSON.stringify({num: counter})}\n\n`); // res.write() instead of res.send()
		// }, 1000);
	
		// If client closes connection, stop sending events

		const pipeline = [ { $match: { runtime: { $lt: 15 } } } ];
		const changeStream = await collection.watch(pipeline);

		changeStream.on("change", (changeEvent) => { 
			/* your callback function */ 
		});

		setTimeout(function(){
			// send HTTP request to updateUrl
			res.write(`data: ${JSON.stringify({msg: "Hello"})} \n\n`);
			console.log("Test");
		}, 1000);
		
		res.on('close', () => {
			console.log('client dropped me');
			res.end();
		});
	});
	
	router.get('/onionringviewtenant/*', function(req, res){
		var data = null;
		console.log(username);
		resourceProvider.getDataMultiSliceVisibilityTenant('demo', function(error, databj)
		{
			data = databj;
			showView();
		});
		resourceProvider.getControllerList(function(error, controllerobj)
		{
			controllerList = controllerobj;
			console.log(controllerList);
			showView();
		});
		function showView()
		{
			if(data !== null && controllerList !== null){
				//console.log('Onion-ring Visualization Rendering'+data);
				res.render('onionringviewtenant.jade', {title: 'Onion-ring-based Visualization', data : JSON.stringify(data), controllerList : JSON.stringify(controllerList)});
		}
	  }
	});
	
	
	// Route for TEIN International API Call
	router.get('/teinint', function(req, res){
		var data = null;
		
		resourceProvider.getTwoRingAPI(function(error, dataobj)
		{
			data = dataobj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
			}
		}
	});
	
	// Route for REN API Call
	router.get('/ren', function(req, res){
		var data = null;
		
		resourceProvider.getThreeRingAPI(function(error, dataobj)
		{
			data = dataobj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
			}
		}
	});
	
	// Route for Sites API Call
	router.get('/sites', function(req, res){
		var data = null;
		
		resourceProvider.getFourRingAPI(function(error, dataobj)
		{
			data = dataobj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
			}
		}
	});
	
	// Route for SmartX Boxes/Micro-Boxes API Call
	router.get('/boxes', function(req, res){
		var data = null;
		
		resourceProvider.getFiveRingAPI(function(error, dataobj)
		{
			data = dataobj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
			}
		}
	});
	
	// Route for SmartX Boxes/Micro-Boxes API Call
	router.get('/vms', function(req, res){
		var data = null;
		
		resourceProvider.getSixRingAPI(function(error, dataobj)
		{
			data = dataobj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
			}
		}
	});
	
	// Route for SmartX Boxes/Micro-Boxes API Call
	router.get('/flows', function(req, res){
		var data = null;
		
		resourceProvider.getSevenRingAPI(function(error, dataobj)
		{
			data = dataobj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
			}
		}
	});
	
	// Route for SmartX Boxes/Micro-Boxes API Call
	router.get('/workload', function(req, res){
		var data = null;
		
		resourceProvider.getEightRingAPI(function(error, dataobj)
		{
			data = dataobj;
			showView();
		});
		
		function showView()
		{
			if(data !== null){
				res.render('onionringviewapi.jade', {title: 'Onion-ring Visualization', data : JSON.stringify(data)});
			}
		}
	});

	return router;
}