var express = require('express');
var router = express.Router();

// Route for Flow Rules View
router.get('/opsflowrules/*', function(req, res){
    var configList = null;
    var statList = null;
    var boxID=req.originalUrl;
    boxID=boxID.substring(14,boxID.length);
    resourceProvider.getOpsSDNConfigList(boxID, function(error,configobj)
    {
       	configList = configobj;
       	showView();
    })
    resourceProvider.getOpsSDNStatList(boxID, function(error,statobj)
    {
        statList = statobj;
        console.log(statList);
        showView();
    })
    function showView()
    {
       	if(configList !== null && statList !== null)
       	{
        	console.log('Operator Controller Flow Rules');
		console.log(statList);
		res.render('opssdncontconfig.jade', { title: 'Operator Controller Flow Rules', configList: configList, statList: statList });
               // res.render('opssdncontconfig.jade',{locals: {
               //        	configList : JSON.stringify(configList),
               // },
               // title: 'Operator Controller Flow Rules'}
               // )
        }
    }    
});

// Route for Flow Statistics View
router.get('/opsflowstat', function(req, res){
    var statList = null;
    resourceProvider.getOpsSDNStatList( function(error,statobj)
    {
        statList = statobj;
        console.log(statList);
        showView();
    })
    function showView()
    {
        if(statList !== null)
        {
                console.log('Operator Controller Flow Stats');
                res.render('opssdncontstat.jade', { title: 'Operator Controller Flow Statistics', statList: statList });
        }
    }
});

module.exports = router;