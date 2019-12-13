var express = require('express');
var router = express.Router();

// Route for TCP Throughput-based Topology View
router.get('/tcptopologyviewops', function(req, res){
    var boxList = null;
	//console.log('Topology Visualization Rendering.');
    resourceProvider.getTCPTopologyList( function(error, boxobj){
        boxList = boxobj;
        showView();
    })
    function showView(){
        if(boxList !== null){
            console.log('Topology Visualization Rendering.');
			//console.log(boxList);
            res.render('tcptopologyviewops.jade', { title: 'Playground Topology View', boxList: JSON.stringify(boxList) });
        }
    }
});

module.exports = router;