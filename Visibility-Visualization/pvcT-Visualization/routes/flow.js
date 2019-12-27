var express = require('express');
var router = express.Router();

//Route for Flow Rules View
router.get('/flowrulesviewops', function(req, res){
    console.log('Flow Rules and Statistics View Rendering');
    //res.render('flowrulesviewops.jade', {title: 'Flow-Centric View'})
    var boxList         = null;
    var switchList      = null;
    var instanceList    = null;
    var workloadList     = 0;
    var ovsBridgeStatus = null;
    var pPathStatus     = null;
    resourceProvider.getpBoxList( function(error,boxobj)
    {
        boxList = boxobj;
        console.log( boxList);
        showView();
    })
    resourceProvider.getvSwitchList(function(error, switchobj)
    {
        switchList = switchobj;
        console.log(switchList);
        showView();
    })

    resourceProvider.getvBoxList(function(error, instanceobj)
    {
        instanceList = instanceobj;
        console.log(instanceList);
        showView();
    })

	resourceProvider.getovsBridgeStatus(function(error, bridgestatusobj)
    {
        ovsBridgeStatus = bridgestatusobj;
        console.log(ovsBridgeStatus);
        showView();
    })

    function showView()
    {
        if(boxList !== null && switchList !== null && instanceList !== null && workloadList !==null &&  ovsBridgeStatus !== null)
        {
                console.log('Flow Rules and Statistics View Rendering');
                
				res.render('flowrulesviewops.jade', {title: 'Flow Rules and Statistics View Rendering',
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
});

// Route for Flow Path Tracing View
router.get('/flowtracingviewops/*', function(req, res){
	//Wait for 1 minute before requesting again
	req.connection.setTimeout(60*1000);
	
	console.log('Flow Path Tracing View Rendering');
    
	var tenantID=req.originalUrl;
	var vlanID=tenantID;
	
	tenantID=tenantID.substring(20, tenantID.indexOf("&"));
	vlanID=vlanID.substring(vlanID.indexOf("&")+1, vlanID.length);
	console.log(tenantID);
	console.log(vlanID);
	
    var boxList           = null;
    var switchList        = null;
    var instanceList      = null;
    var workloadList      = 0;
    var ovsBridgeStatus   = 0;
	var bridgevlanmapList = null;
    
	resourceProvider.getpBoxList( function(error,boxobj)
    {
        boxList = boxobj;
        showView();
    })
    resourceProvider.getvSwitchList(function(error, switchobj)
    {
        switchList = switchobj;
        showView();
    })

    resourceProvider.getTenantvBoxList(tenantID, function(error, instanceobj)
    {
        instanceList = instanceobj;
        showView();
    })

	resourceProvider.getbridgevlanmapList(vlanID, function(error, bridgevlanmapobj)
    {
       	bridgevlanmapList = bridgevlanmapobj;
       	showView();
    })

    function showView()
    {
        if(boxList !== null && switchList !== null && instanceList !== null && workloadList !==null &&  ovsBridgeStatus !== null && bridgevlanmapList !==null)
        {
                res.render('flowtracingviewops.jade', {title: 'Flow Tracing View Rendering',
                        boxList           : JSON.stringify(boxList),
                        switchList        : JSON.stringify(switchList),
                        instanceList      : JSON.stringify(instanceList),
                        workloadList      : JSON.stringify(workloadList),
                        ovsBridgeStatus   : JSON.stringify(ovsBridgeStatus),
                        bridgevlanmapList : JSON.stringify(bridgevlanmapList)
                    }
                )
        }
	}
});

// Route for Flows/Playground Measurements View
router.get('/flowmeasureviewops', function(req, res){
    console.log('Flow Measure View Rendering');
    //res.render('flowcentricviewops.jade', {title: 'Flow-Centric View'})
    var boxList         = null;
    var switchList      = null;
    var instanceList    = null;
    var workloadList     = 0;
    var ovsBridgeStatus = null;
    var pPathStatus     = null;
    resourceProvider.getpBoxList( function(error,boxobj)
    {
        boxList = boxobj;
        console.log( boxList);
        showView();
    })
    resourceProvider.getvSwitchList(function(error, switchobj)
    {
        switchList = switchobj;
        console.log(switchList);
        showView();
    })

    resourceProvider.getvBoxList(function(error, instanceobj)
    {
        instanceList = instanceobj;
        console.log(instanceList);
        showView();
    })

	resourceProvider.getovsBridgeStatus(function(error, bridgestatusobj)
    {
        ovsBridgeStatus = bridgestatusobj;
        console.log(ovsBridgeStatus);
        showView();
    })

    function showView()
    {
        if(boxList !== null && switchList !== null && instanceList !== null && workloadList !==null &&  ovsBridgeStatus !== null)
        {
			console.log('Flow Measure View Rendering');
			res.render('flowmeasureviewops.jade', {title: 'Flow Measure View', 
					boxList         : JSON.stringify(boxList),
					switchList      : JSON.stringify(switchList),
					instanceList    : JSON.stringify(instanceList),
					workloadList     : JSON.stringify(workloadList),
					ovsBridgeStatus : JSON.stringify(ovsBridgeStatus)
			}
			);
        }
    }
});

// Route for Packets/Box IO-Visor View
router.get('/flowiovisorviewops', function(req, res){
    //res.render('flowiovisorviewops.jade', {title: 'Flow-Centric View'})
    var boxList         = null;
    var switchList      = null;
    var instanceList    = null;
    var workloadList     = 0;
    var ovsBridgeStatus = null;
    var pPathStatus     = null;
    resourceProvider.getpBoxList( function(error,boxobj)
    {
        boxList = boxobj;
        console.log( boxList);
        showView();
    })
    resourceProvider.getvSwitchList(function(error, switchobj)
    {
        switchList = switchobj;
        console.log(switchList);
        showView();
    })

    resourceProvider.getvBoxList(function(error, instanceobj)
    {
        instanceList = instanceobj;
        console.log(instanceList);
        showView();
    })

	resourceProvider.getovsBridgeStatus(function(error, bridgestatusobj)
    {
        ovsBridgeStatus = bridgestatusobj;
        console.log(ovsBridgeStatus);
        showView();
    })

    function showView()
    {
        if(boxList !== null && switchList !== null && instanceList !== null && workloadList !==null &&  ovsBridgeStatus !== null)
        {
			console.log('Packets/Box View Rendering');
			res.render('flowiovisorviewops.jade', {title: 'Flow Measure View', 
					boxList         : JSON.stringify(boxList),
					switchList      : JSON.stringify(switchList),
					instanceList    : JSON.stringify(instanceList),
					workloadList     : JSON.stringify(workloadList),
					ovsBridgeStatus : JSON.stringify(ovsBridgeStatus)
			}
			);
        }
    }
});

// Route for TCP Throughput-based Data API
router.get('/getamdatatcpperDay/', function(req, res){
    //Wait for 1 minute before requesting again
	req.connection.setTimeout(60*1000);
	
	var boxID=req.originalUrl;
	var filterdate=boxID;
	
	boxID=filterdate.substring(20, filterdate.indexOf("&"));
	filterdate=boxID.substring(boxID.indexOf("&")+1, boxID.length);
	console.log(boxID);
	console.log(filterdate);
	
	resourceProvider.getAMDataTCPperDay(boxID, filterdate, function(error, data){
        if (err)
			res.send(err);
		res.json(data);
    })
});

module.exports = router;