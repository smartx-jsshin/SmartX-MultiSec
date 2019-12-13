var express = require('express');
var router = express.Router();

// Route for Workload View
app.get('/servicecentricviewops', function(req, res){
    console.log('Workload-Centric View Rendering');
    res.render('servicecentricviewops.jade', {title: 'Workload Centric View'})
});

module.exports = router;