var express = require('express');
var router = express.Router();

var username = "admin";

//ManhNT start
router.get('/onionringviewops', function(req, res){
	var data = null;
	console.log(username);
	resourceProvider.getDataMultiSliceVisibility(username, function(error, databj)
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
			res.render('onionringviewops.jade', {title: 'Onion-ring-based Visualization', data : JSON.stringify(data), controllerList : JSON.stringify(controllerList)});
		}
	}
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

module.exports = router;