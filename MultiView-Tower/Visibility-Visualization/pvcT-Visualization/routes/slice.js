var express = require('express');
var router = express.Router();

// Route for Tenant-Vlan Mappings View
router.get('/tenantvlanmapops', function(req, res){
	var tenantList = null;
    //var tenantID=req.originalUrl;
    //tenantID=tenantID.substring(14, tenantID.length);
    //resourceProvider.gettenantvlanmapList(tenantID, function(error, tenantObj)
	resourceProvider.gettenantvlanmapList(function(error, tenantObj)
    {
       	tenantList = tenantObj;
       	showView();
    })
    
    function showView()
    {
       	if(tenantList !== null)
       	{
        	console.log('Tenant-Vlan Flow Path Tracing');
			console.log(tenantList);
			res.render('tenantvlanmapops.jade', { title: 'Tenant Vlan Mappings View', tenantList: tenantList });
		}
    }    
});

// Route for Tenant-Vlan Mappings View
router.get('/tenantvlanmaponionring', function(req, res){
	var tenantList = null;
    resourceProvider.gettenantvlanmapList(function(error, tenantObj)
    {
       	tenantList = tenantObj;
       	showView();
    })
    
    function showView()
    {
       	if(tenantList !== null)
       	{
        	console.log('Tenant-Vlan Onion-ring');
			//console.log(tenantList);
			res.render('tenantvlanmaponionring.jade', { title: 'Tenant Vlan Mappings View', tenantList: tenantList });
		}
    }    
});

module.exports = router;