module.exports = function(provider){

    var router = require('express').Router();
    var resourceProvider = provider
    console.log(resourceProvider);

    // Route for TCP Throughput-based Topology View
    router.get('/tcptopologyviewops', function(req, res){
        console.log("[Router | topology/tcptopologyviewops] Route to /topology/tcptopologyviewops");

        var boxList = null;
        //console.log('Topology Visualization Rendering.');
        resourceProvider.getTCPTopologyList( function(error, boxobj){
            console.log("[Router | topology/tcptopologyviewops] getTCPTopologyList() was called");
            boxList = boxobj;
            showView();
        })
    
        function showView(){
            if(boxList !== null){
                console.log('[Router | topology/tcptopologyviewops] Topology Visualization Rendering.');
                //console.log(boxList);
                res.render('topology/tcptopologyviewops.pug', { title: 'Playground Topology View', boxList: JSON.stringify(boxList) });
            }
        }
    });
    
    // Route for Overall Playground Topology View
    router.get('/sitetopology', function(req, res){
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
                res.render('topology/tcptopologyviewops.pug', { title: 'Playground Topology View', boxList: JSON.stringify(boxList) });
            }
        }
    });
    
    return router;
};