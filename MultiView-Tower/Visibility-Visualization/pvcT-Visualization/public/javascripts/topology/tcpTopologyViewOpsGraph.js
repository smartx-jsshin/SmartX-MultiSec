var session_username = sessionStorage.getItem('ss_user_name');
if (session_username === null) {
    window.location.replace("http://" + vCenterHost + ":" + vCenterPort + "/login");
}

// Receive Active Boxes List
var nodes = null, edges = null, network = null;
var DIR = 'images/';
var EDGE_LENGTH_MAIN = 350, EDGE_LENGTH_SUB = 150;
var BridgeLinkColor = 'BLACK', BridgeNodeColor = '#3399ff';
var LENGTH_SERVER = 150, LENGTH_SUB = 50, WIDTH_SCALE = 2;
const GREEN = 'green', RED = '#C5000B', ORANGE = 'orange', GRAY = 'gray', BLACK = '#2B1B17';

function decodeHtmltoJson(text){
    var textArea = document.createElement('textarea');
    textArea.innerHTML = text;
    jsonFromText = JSON.parse(textArea.value)
    return jsonFromText;
}

// Called when the Visualization API is loaded.
function draw() {
    var boxListJson = decodeHtmltoJson(boxList);
    console.log(boxListJson);

    // Create a data table with nodes.
    nodes = [];
    // Create a data table with links.
    edges = [];
    //Get source and destination Box IDs separatley from the List
    var srcIDArray = [], destIDArray = [], boxLabel = '';
    var srcMap = new Object();
    var destMap = new Object();
    // console.log(boxList);
    // console.log(JSON.parse(boxList));
    for (i = 0; i < boxListJson.length; i++) {
        // console.log(boxList[i]);
        
        srcIDArray.push(boxListJson[i].srcBoxID);
        destIDArray.push(boxListJson[i].destBoxID);
        srcMap[boxListJson[i].srcBoxID] = boxListJson[i].srcBoxname;
        destMap[boxListJson[i].destBoxID] = boxListJson[i].destBoxname;
    }

    //Distinct nodes List
    var uniqueNodes = [...new Set([...srcIDArray, ...destIDArray])];
    console.log(uniqueNodes);
    // console.log(uniqueNodes.length);
    //Draw the Nodes
    for (i = 0; i < uniqueNodes.length; i++) {
        boxLabel = srcMap[uniqueNodes[i]];

        if (!boxLabel)
            boxLabel = destMap[uniqueNodes[i]];

        nodes.push({
            id: uniqueNodes[i], 
            label: boxLabel, 
            box: uniqueNodes[i], 
            value: 3, 
            fixed: false, 
            physics: false, 
            borderWidth: 2, 
            borderWidthSelected: 4, 
            color: { 
                border: '#2B7CE9', 
                background: '#97C2FC', 
                highlight: { 
                    border: '#2B7CE9', 
                    background: 
                    '#D2E5FF' 
                }, 
                hover: { 
                    border: '#2B7CE9', 
                    background: '#D2E5FF' 
                }
            } 
        });
    }

    //Draw the Edges
    for (var i in boxListJson) {
        console.log(boxListJson[i].srcBoxID + ' ' + boxListJson[i].destBoxID);

        if (boxListJson[i].score <= 20)
            EDGE_LENGTH_SUB = 80;
        else if (boxListJson[i].score > 20 && boxListJson[i].score <= 40)
            EDGE_LENGTH_SUB = 120;
        else if (boxListJson[i].score > 40 && boxListJson[i].score <= 60)
            EDGE_LENGTH_SUB = 160;
        else if (boxListJson[i].score > 60 && boxListJson[i].score <= 80)
            EDGE_LENGTH_SUB = 200;
        else
            EDGE_LENGTH_SUB = 240;

        //	nodes.push({id: boxList[i].srcBoxID, label: boxList[i].srcBoxname, box: boxList[i].srcBoxname, group: 'desktop', value: 3, fixed: false, physics:false, color: BridgeNodeColor});
        edges.push({ 
            from: boxListJson[i].srcBoxID, 
            to: boxListJson[i].destBoxID, 
            arrows: { 
                to: { 
                    enabled: true, 
                    type: 'circle' 
                } 
            }, 
            length: EDGE_LENGTH_SUB, 
            color: BridgeLinkColor 
        });
    }

    // legend
    var mynetwork = document.getElementById('mynetwork');
    var x = - mynetwork.clientWidth / 2 + 50;
    var y = - mynetwork.clientHeight / 2 + 50;
    var step = 70;

    // create a visualization network
    var container = document.getElementById('mynetwork');
    var data = {
        nodes: nodes,
        edges: edges
    };
    var options = {
        nodes: {
            //shape: 'dot',
            size: 20,
            borderWidth: 2,
            font: {
                size: 16,
                color: '#000000'
            },
            scaling: {
                min: 16,
                max: 32,
            }
        },
        edges: {
            color: GRAY,
            smooth: true,
            width: 2
        },
        layout: {
            randomSeed: 1,
            improvedLayout: true,
        },
        physics: {
            "enabled": true,
            "minVelocity": 0.75
        },
        interaction: {
            navigationButtons: true,
            hover: true,
            keyboard: true
        },
        groups: {
            'switch': {
                shape: 'triangle',
                color: '#FF9900' // orange
            }
        }
    };

    network = new vis.Network(container, data, options);
    network.on("click", function (params) {
        console.log(params);
        params.event = "[original event]";
        if (params.nodes == "") {
        }
        else {
            var nodeId = params.nodes;
            //window.parent.receiveValueBox(nodes[i]);
        }
    });

    var myInput = $("#mynetwork");
    var inputOpentip = new Opentip(myInput, { showOn: null, style: 'glass' });
    var count = 0;

    network.on("hoverNode", function (params) {
        params.event = "[original event]";
        var nodeId = params.node;
        for (var i = 0; i < nodes.length; i++) {
            if (nodes[i].id == nodeId) {
                count = i;
                break;
            }
        }

        inputOpentip.setContent("Node label: " + nodes[count].label + " Id: " + nodes[count].id);
        inputOpentip.show();
    });
    
    network.on("blurNode", function (params) {
        inputOpentip.hide();
    });
}