var express = require('express');
var router = express.Router();

router.get('/resourcecentricviewops', function(req, res){
	var bboxList         = null;
    var sboxList         = null;
    var cboxList         = null;
    var oboxList         = null;
    var switchList      = null;
    var instanceList    = null;
    var workloadList    = 0;
    var ovsBridgeStatus = null;
    var boxes           = {};
    var pPathStatus     = null;
    
    var tasks = [
	function(callback){
    	resourceProvider.getpBoxList('B', (function(error, bboxobj)
    	{
		 	boxes.bbox = bboxobj;
	    	callback();
		}))
    },
    function(callback){
    	resourceProvider.getpBoxList('S', (function(error, sboxobj)
    	{
		 	boxes.sbox = sboxobj;
	    	//console.log(boxes.sbox);
	    	callback();
		 	//showView();
    	}))
    },
    
    function (callback){
    	resourceProvider.getpBoxList('C', (function(error, cboxobj)
    {
		 boxes.cbox = cboxobj;
	    //console.log(boxes.cbox);
	    callback();
		 //showView();
    }))
    },
    function (callback){
    	resourceProvider.getpBoxList('O', (function(error, oboxobj)
    	{
		 	boxes.obox = oboxobj;
	    	//console.log(boxes.obox);
	    	callback();
		 	//showView();
    	}))
    },
	function (callback){
    	resourceProvider.getvSwitchList('B', (function(error, bswitchobj)
    	{
    		boxes.bswitchList = bswitchobj;
       	   	callback();
		}))
    },
    function (callback){
    	resourceProvider.getvSwitchList('S', (function(error, sswitchobj)
    	{
    		boxes.sswitchList = sswitchobj;
       	//console.log(switchList);
			callback();
		 	//showView();
    	}))
    },
    function (callback){
    	resourceProvider.getvSwitchList('C', (function(error, cswitchobj)
    	{
    		boxes.cswitchList = cswitchobj;
       	//console.log(switchList);
			callback();
		 	//showView();
    	}))
    },
    function (callback){
    	resourceProvider.getvSwitchList('O', (function(error, oswitchobj)
    	{
    		boxes.oswitchList = oswitchobj;
       	//console.log(boxes.oswitchList);
			callback();
		 	//showView();
    	}))
    },
	function (callback){
    	resourceProvider.getovsBridgeStatus('B', function(error, bbridgestatusobj)
    	{
			console.log(bbridgestatusobj);
			boxes.bovsBridgeStatus = bbridgestatusobj;
			callback();
        })
    },
    function (callback){
    	resourceProvider.getovsBridgeStatus('S', function(error, sbridgestatusobj)
    	{
			boxes.sovsBridgeStatus = sbridgestatusobj;
			//console.log(ovsBridgeStatus);
			callback();
			//showView();
    	})
    },
    function (callback){
    	resourceProvider.getovsBridgeStatus('C', function(error, cbridgestatusobj)
    	{
			boxes.covsBridgeStatus = cbridgestatusobj;
			//console.log(boxes.covsBridgeStatus);
			callback();
			//showView();
    	})
    },
    function (callback){
    	resourceProvider.getovsBridgeStatus('O', function(error, obridgestatusobj)
    	{
			boxes.oovsBridgeStatus = obridgestatusobj;
			//console.log(boxes.oovsBridgeStatus);
			callback();
			//showView();
    	})
    },
    function(callback){
    	resourceProvider.getvBoxList(function(error, instanceobj)
    	{
			boxes.instanceList = instanceobj;
			//console.log(boxes.instanceList);
			callback();
			//showView();
    	})
    },
    function(callback){
    	resourceProvider.getIoTHostList(function(error, hostobj)
    	{
			boxes.iotHostList = hostobj;
			//console.log(boxes.iotHostList);
			callback();
      })
    },
    function(callback){
    	resourceProvider.getControllerList(function(error, controllerobj)
    	{
			boxes.controllerList = controllerobj;
			//console.log(boxes.controllerList);
			callback();
      })
    }
    ];

	 async.parallel(tasks, function(err) { 
			console.log('Resource-Centric View Rendering');
			res.render('resourcecentricviewops.jade', {
				bboxList         : JSON.stringify(boxes.bbox),
				sboxList         : JSON.stringify(boxes.sbox),
				cboxList         : JSON.stringify(boxes.cbox),
				oboxList         : JSON.stringify(boxes.obox),
				bswitchList      : JSON.stringify(boxes.bswitchList),
				sswitchList      : JSON.stringify(boxes.sswitchList),
				cswitchList      : JSON.stringify(boxes.cswitchList),
				oswitchList      : JSON.stringify(boxes.oswitchList),
				instanceList     : JSON.stringify(boxes.instanceList),
				iotHostList      : JSON.stringify(boxes.iotHostList),
				bovsBridgeStatus : JSON.stringify(boxes.bovsBridgeStatus),
				sovsBridgeStatus : JSON.stringify(boxes.sovsBridgeStatus),
				covsBridgeStatus : JSON.stringify(boxes.covsBridgeStatus),
				oovsBridgeStatus : JSON.stringify(boxes.oovsBridgeStatus),
				controllerList   : JSON.stringify(boxes.controllerList)
        	});
        });
	});
	
	// Route for Resource-Centric View
/*app.get('/resourcecentricviewops', function(req, res){
    var boxList         = null;
    var switchList      = null;
    var instanceList    = null;
    var workloadList     = 0;
    var ovsBridgeStatus = null;
    var pPathStatus     = null;

    resourceProvider.getpBoxList( function(error,boxobj){
		boxList = boxobj;
		//console.log( boxList);
		showView();
    })
    
	resourceProvider.getvSwitchList(function(error, switchobj){
    	switchList = switchobj;
        //console.log(switchList);
		showView();
    })

    resourceProvider.getvBoxList(function(error, instanceobj){
        instanceList = instanceobj;
        //console.log(instanceList);
        showView();
    })

    resourceProvider.getovsBridgeStatus(function(error, bridgestatusobj){
        ovsBridgeStatus = bridgestatusobj;
        //console.log(ovsBridgeStatus);
        showView();
    })

    function showView(){
        if(boxList !== null && switchList !== null && instanceList !== null && workloadList !==null &&  ovsBridgeStatus !== null){
		    console.log('Resource-Centric View Rendering');
			//console.log(ovsBridgeStatus);
			
			res.render('resourcecentricviewops.jade', {title: 'Resource-Centric Topological View',
				boxList         : JSON.stringify(boxList),
				switchList      : JSON.stringify(switchList),
				instanceList    : JSON.stringify(instanceList),
				workloadList     : JSON.stringify(workloadList),
				ovsBridgeStatus : JSON.stringify(ovsBridgeStatus)
				}, 
				function(err, html){
					if (err) { console.err("ERR", err) };
					//console.log(html);
					res.status(200).send(html);
				}
			);
		}
	}
});*/


module.exports = router;