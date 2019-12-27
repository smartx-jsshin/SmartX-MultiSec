/**
 * Module dependencies.
 */

// var http = require("http");
var express = require('express');
// var async = require('async');
var path = require('path')
// var favicon = require('serve-favicon')
var logger = require('morgan')
// var methodOverride = require('method-override')
var session = require('express-session')
var bodyParser = require('body-parser')
// var multer = require('multer')
var errorHandler = require('errorhandler')

var resourceProvider = require('./MultiView-DataAPI').ResourceProvider;
var vCenterConfig = require('./MultiView-DataAPI').VisibilityCenterConfig;
var playgroundConfig = require('./MultiView-DataAPI').PlaygroundConfig;

//
//Express App Setting
//
var app = express();
app.set('view engine', 'pug');
app.use(express.json());
app.use(logger('dev'))
// app.use(methodOverride());
app.use(require('stylus').middleware({ src: __dirname + '/public' }));
app.set('views', path.join(__dirname, '/views'));
app.use(session({ resave: true,
                  saveUninitialized: true,
                  secret: 'uwotm8' }));
//app.use(bodyParser.json())
app.use(bodyParser.urlencoded({ extended: true }));
//app.use(multer())
app.use("/public", express.static(path.join(__dirname, '/public')));
app.use("/node_modules", express.static(path.join(__dirname, "node_modules")));

//
// Loading Routers for visualization types
//
var playgroundTopologyRouter = require('./routes/topology');
// var controllerRouter = require('./routes/controller');
// var resourceLayerRouter = require('./routes/resource');
// var sliceLayerRouter = require('./routes/slice');
// var flowLayerRouter = require('./routes/flow');
// var workloadLayerRouter = require('./routes/workload');
// var onionRingRouter = require('./routes/onionring');

app.use('/topology', playgroundTopologyRouter);


//the dictionary key is user name and value is
var userwithip = null;

// Route for Login View
app.get('/', function(req, res){
    // resourceProvider.getUsers( function(err, listusers){
    //     res.render('test.pug', {userlist: listusers});
    // });
    res.redirect("/login");
});

// Route for Menu View
app.get('/menu', function(req, res){
    console.log('Menu Rendering');
    res.render('menu.pug',{
        locals: {}, 
        title: 'Multi-View Menu',
        onionRingUrl: "http://" + vCenterConfig.getHost() + ":" + vCenterConfig.getPort() + "/onionringviewops"
    })
});

app.get('/login', function(req, res){
    res.render('login.pug',{
        title: 'MultiView Login',
        vCenterHost: vCenterConfig.getHost(),
        vCenterPort: vCenterConfig.getPort(),
        vCenterAuthPort: vCenterConfig.getAuthPort()
    })
});

// error handling middleware should be loaded after the loading the routes
if (app.get('env') === 'production') {
  app.use(errorHandler())
}


// Web authentication at server side (by using socket.io libray)
// ToDo: Replace this code to use PassportJS library
// https://steemit.com/utopian-io/@upmeboost/nodejs--socketio--creating-a-login-system-nvlrmaoy

var client = require('socket.io').listen(8080).sockets;
client.on('connection', function (socket) {
    socket.on('login', function(login_info){
        var this_user_name = login_info.user_name,
            this_user_password = login_info.user_password;
        if (this_user_name === '' || this_user_password === '') {
                socket.emit('alert', 'You must fill in both fields');
        } else {
            resourceProvider.getUsers(function (err, listUsers){
                if(err) throw err;
                var found = false;
                    location =-1;
                  if (listUsers.length) {
                        for (var i in listUsers) {
                            if (listUsers[i].username === this_user_name) {
                                found = true;
                                if (listUsers[i].password === this_user_password) {
                                    //todo: get priority and send to menu page.
                                    username = this_user_name;

                                    var resp = {};
                                    resp.name = listUsers[i].username;
                                    resp.role = listUsers[i].role;
                                    resp.nextPage = "menu";
                                    console.log(resp);
                                    socket.emit("loginSuccess", resp);

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
