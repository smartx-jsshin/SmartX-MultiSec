
function decodeHtmltoJson(text){
    console.log("Before Decoding: " + onionRingData);

    var textArea = document.createElement('textarea');
    textArea.innerHTML = text;
    jsonFromText = JSON.parse(textArea.value)

    console.log("After Decoding: ");
    console.log(jsonFromText);

    return jsonFromText;
}

var onionRingDataJson = decodeHtmltoJson(onionRingData);
// var controllerListJson = decodeHtmltoJson(controllerList);

//* Important Data is the data of psd3
var config = {
    containerId: "chartContainer",
    width: 850,
    height: 850,
    data: onionRingDataJson,
    label: function (d) {
        return d.data.label;
    },
    textBoder: function (d) {
        return d.data.colorBoder;
    },
    value: "resource",
    inner: "drilldown",
    tooltip: function (d) {
        return "<div style='background-color: #4a4; color: white; padding: 15px; text-align: middle; border: dotted 1px black;'><strong>" + d.info;
    },
    textColor: function (d) {
        return d.data.color;
    },
    transition: "linear",
    transitionDuration: 20,
    donutRadius: 0,
    gradient: true,
    colors: d3.scale.category20(),
    labelColor: "black",
    stroke: "#eee",
    strokeWidth: 2,
    drilldownTransition: "linear",
    drilldownTransitionDuration: 0,
    highlightColor: "#c00",
    rotateLabel: false
};

//Generate HTML for Controllers
// var rows = '';
// for (var controller in controllerListJson) {
//     //console.log(controllerList[controller].controllerName);
//     var color = controllerListJson[controller].controllerStatus;
//     console.log(rows);
//     rows += '<tr><td style=color:' + color + ';>' + controllerListJson[controller].controllerName + '</td></tr>';
// }

// document.getElementById('controllertable').innerHTML = rows;
var samplePie = new psd3.Pie(config);