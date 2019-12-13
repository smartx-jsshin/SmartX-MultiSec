/**
 * Module dependencies.
 */

var http = require("http");
var express = require('express');
var async = require('async');
var path = require('path')

var favicon = require('serve-favicon')
var logger = require('morgan')
var methodOverride = require('method-override')
var session = require('express-session')
var bodyParser = require('body-parser')
var multer = require('multer')
var errorHandler = require('errorhandler')

var BoxProvider = require('./MultiView-DataAPI').BoxProvider;
var client = require('socket.io').listen(8080).sockets;
var host = "";

var app = express();

app.set('view engine', 'pug');
app.use(express.json());
app.use(logger('dev'))
app.use(methodOverride());
app.use(require('stylus').middleware({ src: __dirname + '/public' }));
app.set('views', path.join(__dirname, '/views'))
app.use(session({ resave: true,
                  saveUninitialized: true,
                  secret: 'uwotm8' }))
//app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }))
//app.use(multer())
app.use(express.static(path.join(__dirname, '/public')))
//Before starting application run below command in public directory
//ln -s /opt/KONE-MultiView/pvcT-Visualization/node_modules/ /opt/KONE-MultiView/pvcT-Visualization/public/

//Define Application Routes
var resourceProvider = new ResourceProvider();

var playgroundTopologyRouter = require('./routes/topology');
var controllerRouter = require('./routes/controller');
var resourceLayerRouter = require('./routes/resource');
var sliceLayerRouter = require('./routes/slice');
var flowLayerRouter = require('./routes/flow');
var workloadLayerRouter = require('./routes/workload');
var onionRingRouter = require('./routes/onionring');

//app.use('/layer/resource', resourceLayerRouter);


//the dictionary key is user name and value is
var userwithip = null;

// Route for Login View
app.get('/', function(req, res){
    res.redirect('/login');
});

// Route for Menu View
app.get('/menu', function(req, res){
    console.log('Menu Rendering');
	userwithip = {name:username , ip : req.connection.remoteAddress};
	console.log(userwithip);
	res.render('menu.jade',{locals: {}, title: 'Multi-View Menu'})
});

app.get('/login', function(req, res){
    res.render('login.jade',{ title: 'MultiView Login'})
});

// error handling middleware should be loaded after the loading the routes
if (app.get('env') === 'production') {
  app.use(errorHandler())
}

// Web Autentication & Validation
client.on('connection', function (socket) {
    socket.on('login', function(login_info){
        var this_user_name = login_info.user_name,
            this_user_password = login_info.user_password;
        if (this_user_name === '' || this_user_password === '') {
                socket.emit('alert', 'You must fill in both fields');
        } else {
            resourceProvider.getUsers(function (err, listusers){
                if(err) throw err;
                var found = false,
                    location =-1;
                  if (listusers.length) {
                        for (var i in listusers) {
                            if (listusers[i].username === this_user_name) {
                                found = true;
                                if (listusers[i].password === this_user_password) {
                                    //todo: get priority and send to menu page.
									username = this_user_name;
                                    if(listusers[i].role === 'operator'){
                                        socket.emit('redirect', 'operator');
                                    }
                                    else{
                                        socket.emit('redirect', 'developer');
                                    }
                                } else {
                                    socket.emit('alert', 'Please retry password');
                                }
                                break;
                            }
                        }

                        if (!found) {
                            socket.emit('alert', 'Sorry, We could not find you.');
                        }
                    }
            })
        }
    });
});

app.set('domain', '0.0.0.0')
app.listen(3011, () => console.log("Express Server Running..."))
//console.log("Express server listening on port %d in %s mode", app.address().port, app.settings.env);
