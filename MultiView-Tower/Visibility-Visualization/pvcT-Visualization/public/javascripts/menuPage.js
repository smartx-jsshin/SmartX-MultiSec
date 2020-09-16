// In this file, we add event handlers to buttons on the menu bar


//redirect to login page if user is not logged
var session_username = sessionStorage.getItem('ss_user_name');
var session_userrole = sessionStorage.getItem('ss_role');

if (session_username === null) {
    window.location.replace("http://" + vCenterHost + ":" + vCenterPort + "/login");
}
//Resource-level Functions Start
//receive Box objects
function receiveValueBox(boxs) {
    var iframe = document.getElementById('secondIFrame');
    // console.log(boxs);
    // iframe.src = 'http://' + vCenterHost + ':3000/dashboard/db/resource-dashboard-' + boxs.label;
}

//receive tenant objects
function receiveTenantID(data) {
    //- console.log("Receive Data Success " + data.info);
    var iframe = document.getElementById('secondIFrame');
    // iframe.src = 'http://' + vCenterHost + ':3000/dashboard/db/resource-dashboard-' + data.boxID;
}

//receive tenant objects
function receiveSampledFlows(data) {
    //- console.log("Receive Data Success " + data.info);
    var iframe = document.getElementById('secondIFrame');
    // iframe.src = 'http://' + vCenterHost + ':8008/app/dashboard-example/html/';
}

//receive tenant objects
function receiveTracedPkts(data) {
    //- console.log("Receive Data Success " + data.info);
    var iframe = document.getElementById('secondIFrame');
    // iframe.src = 'http://' + vCenterHost + ':8008/agents/html';
}

//receive brCap Objects
function receiveValueBrCap(brCaps) {
    var iframe = document.getElementById('secondIFrame');
    // console.log(brCaps);
    ////iframe.src = 'http://'+serverIP+':3000/dashboard/db/flow-dashboard-'+brCaps.label+'-'+brCaps.box;
    //iframe.src = 'http://'+serverIP+':'+serverPort+'/opsflowrules/'+brCaps.box;
}

//receive VM Objects
function receiveValueVM(vms) {
    var iframe = document.getElementById('secondIFrame');
    // console.log(vms);
    //iframe.src = 'http://'+serverIP+':3000/dashboard/db/flow-dashboard-instance-'+vms.label+'-'+vms.box;
}

//Resource-level Functions End
//Flow-level Functions Start
//Route to Network Flow View
function getNetworkFlow(network) {
    var iframe = document.getElementById('secondIFrame');
    // iframe.src = 'http://' + vCenterHost + ':8008/app/dashboard-example/html/';
}

//Route to Box Flow View
function getBoxFlow(boxs) {
    var iframe = document.getElementById('secondIFrame');
    //console.log(boxs);
    if (boxs.id === 1)
        iframe.src = "http://" + vCenterHost + ":5601/app/kibana#/dashboard/dab0b840-c90a-11e7-9140-dfb68f1deddf?_g=(refreshInterval%3A('%24%24hashKey'%3A'object%3A344'%2Cdisplay%3A'5%20seconds'%2Cpause%3A!f%2Csection%3A1%2Cvalue%3A5000)%2Ctime%3A(from%3Anow-30m%2Cmode%3Aquick%2Cto%3Anow))";
    else
        iframe.src = 'http://' + vCenterHost + ':3000/dashboard/db/iovisortracing-' + boxs.label;
    console.log('http://' + vCenterHost + ':3000/dashboard/db/iovisortracing-' + boxs.label);
    /*if (boxs.label === 'GIST-WAN-Box')
    iframe.src = 'http://'+serverIP+':3000/dashboard/db/iovisortracing-'+boxs.label;
    else if (boxs.label === 'GIST-Cloud-Box')
    iframe.src = 'http://'+serverIP+':5601/goto/48e591f431b051ae64b4ad3f451c36d9';
    else if (boxs.label === 'GIST-Access-Box')
    iframe.src = 'http://'+serverIP+':5601/goto/48e591f431b051ae64b4ad3f451c36d9';*/
}

//Route to Flow Rules + Stats View
function getBrCapFlow(brCaps) {
    var iframe = document.getElementById('secondIFrame');
    // console.log(brCaps);
    // iframe.src = 'http://' + vCenterHost + ':' + vCenterPort + '/opsflowrules/' + brCaps.box;
}

//Route to VM Flow View
function getVMFlow(vms) {
    var iframe = document.getElementById('secondIFrame');
    // console.log(vms);
    //iframe.src = 'http://'+serverIP+':'+serverPort+'/opsflowrules/'+brCaps.box;
}

//Route to Flow Path Trace View
function getFlowPathTrace(vlan) {
    var iframe = document.getElementById('firstIFrame');
    // console.log('In Menu ' + vlan);
    // iframe.src = 'http://' + vCenterHost + ':' + vCenterPort + '/flowtracingviewops/' + vlan;
}

//Route to Onion-ring Multi-View for tenant
function getOnionRingTenant(vlan) {
    var iframe = document.getElementById('firstIFrame');
    // iframe.src = 'http://' + vCenterHost + ':' + vCenterPort + '/onionringviewtenant/' + vlan;
}

//Flow-level Functions End
//Show Panel on Click
function showPanel(itemID) {
    var iframe = document.getElementById('firstIFrame');
    // console.log(itemID);
    // iframe.src = 'http://' + vCenterHost + ':' + vCenterPort + '/' + itemID.label + '-' + itemID.box;
}

// Called when the Visualization API is loaded.
function draw() {
    console.log("Start adding event handlers to buttons")
    // document.getElementById('usertext').innerHTML = "Logged In User:  " + session_username;

    //Update********************************************************
    var iframe1 = document.getElementById('firstIFrame');
    // var iframe2 = document.getElementById('grafanaIframe');
    var tcptopology = document.getElementById('tcptopology');
    var onionops = document.getElementById('onionops');
    // var oniontenant = document.getElementById('oniontenant');
    var onion3d = document.getElementById('onion3d');
    // var resource = document.getElementById('resourcecentricviewops');
    // var flowrules = document.getElementById('flowrulesviewops');
    // var flowtracing = document.getElementById('flowtracingviewops');
    // var flowmeasure = document.getElementById('flowmeasureviewops');
    // var slicingviewops = document.getElementById('slicingviewops');
    // var service = document.getElementById('servicecentricviewops');
    // var sliceview = document.getElementById('sliceview');
    // var sliceviewtenant = document.getElementById('sliceviewtenant');

    tcptopology.addEventListener('click', function () {
        console.log("TCP Topology Button was clicked");
        document.getElementById('firstIFrameHeader').innerHTML = "Playground Overlay Topology View";
        iframe1.src =  rootUrl + '/topology/tcptopologyviewops';
        //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    });

    onionops.addEventListener('click', function () {
        document.getElementById('firstIFrameHeader').innerHTML = "Onion-ring-based Visualization (Operator)";
        iframe1.src = rootUrl + '/onionring/onionring2d';
        //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    });

    // oniontenant.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Onion-ring-based Visualization (Tenant)</p></b>';
    //     //iframe1.src = 'http://'+serverIP+':'+serverPort+'/onionringviewtenant';
    //     iframe2.src = 'http://' + vCenterHost + ':' + vCenterPort + '/tenantvlanmaponionring';
    // });

    onion3d.addEventListener('click', function () {
        document.getElementById('firstIFrameHeader').innerHTML = "3D Onion-ring Visualization for Multi-tier/-level Security";
        iframe1.src = rootUrl + '/onionring/onionring3d';
    });

    // resource.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Resource-Centric Topological View (Playground View)</p></b>';
    //     iframe1.src = 'http://' + vCenterHost + ':' + vCenterPort + '/resourcecentricviewops';
    //     //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    // });

    // flowrules.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Flow-Centric Topological View</p></b>';
    //     iframe1.src = 'http://' + vCenterHost + ':' + vCenterPort + '/flowrulesviewops';
    //     //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    // });

    // flowtracing.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Flow-Centric Topological View</p></b>';
    //     //iframe1.src = 'http://'+serverIP+':'+serverPort+'/flowtracingviewops';
    //     iframe2.src = 'http://' + vCenterHost + ':' + vCenterPort + '/tenantvlanmapops';
    // });

    // flowmeasure.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Flow-Centric Topological View (sFlow-based)</p></b>';
    //     iframe1.src = 'http://' + vCenterHost + ':' + vCenterPort + '/flowmeasureviewops';
    //     //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    // });

    // flowiovisorviewops.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Flow-Centric Topological View (IO Visor-based)</p></b>';
    //     iframe1.src = 'http://' + vCenterHost + ':' + vCenterPort + '/flowiovisorviewops';
    //     //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    // });

    // slicingviewops.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Slicing View</p></b>';
    //     iframe1.src = 'http://103.22.221.51:6126/';
    //     //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    // });

    // service.addEventListener('click', function () {
    //     document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Service-Centric Topological View</p></b>';
    //     iframe1.src = 'http://' + vCenterHost + ':' + vCenterPort + '/servicecentricviewops';
    //     //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    // });

    //
    // Below codes are not used. Remain them for reference.
    //
    /*flowboxviewops.addEventListener('click', function() {
    document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Flow-Centric Topological View (sFlow-based)</p></b>';
    iframe1.src = 'http://'+serverIP+':5601/goto/1cf86a106a8725db0f3ab9c33c72bf60';
    //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    });

    flowclusterviewops.addEventListener('click', function() {
    document.getElementById('panel-heading-id').innerHTML = '<b><p style="display:inline;font-size:12;color:#e6eeff;text-align:center;">Flow-Centric Topological View</p></b>';
    iframe1.src = 'http://'+serverIP+':5601/goto/20e35e15d09a942539b445badc77693c';
    //iframe2.src = 'http://'+serverIP+':'+serverPort+'/#';
    });*/
    
}