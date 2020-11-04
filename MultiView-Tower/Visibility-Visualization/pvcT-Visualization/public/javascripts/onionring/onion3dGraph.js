class OnionRing3DVisualizer{
    constructor(ringSize, heightScale) {
        // Sizing variables for ring segments
        this.ringSize = 5;
        this.pieceHeightScale = 3;
        this.defaultHeight = 0.2 * this.pieceHeightScale;
        this.radiusMargin = 0.2;
        this.angleMargin = 0.15;

        // Color definition for ring segments
        this.resourceColorPallete = [ 0xC0C0C0, 0xC0C0C0, 0x008000, 0x008000, 0x008000, 0xFFFF00, 0xFFFF00, 0x0000FF ] // Silver, Silver, Green, Green, Green, Yellow, Yellow, Blue
        this.securityColorPallete = [ 0x808080, 0x00FF000, 0x66FF000, 0x99FF000, 0xCCFF000, 0xFFFF00, 0xFFCC00, 0xFF9900, 0xFF6600, 0xFF3300, 0xFF0000 ] // Gray, Green, Yellow, Red
        
        // Instance Attributes for onion-ring topology
        this.tierDef = null;
        this.pgTopo = null;
        
        this.scene = null;      
        this.camera = null;
        this.renderer = null;
    }

    decodeHtmltoJson(text){
        var textArea = document.createElement('textarea');
        textArea.innerHTML = text;
        var jsonFromText = JSON.parse(textArea.value);
    
        return jsonFromText;
    }
    
    loadTopology(topologyJson){
        const onionRing3DDataJson = this.decodeHtmltoJson(topologyJson);
        this.tierDef = onionRing3DDataJson.tier_definition;
        this.pgTopo = onionRing3DDataJson.playground_topology;
    }

    // Creating a piece of onion-ring
    degreeToRadian(degree){
        const radian = Math.PI * degree / 180;
        return radian;
    }

    getCircleX(xCenter, radius, radian){
        const x = xCenter + radius * Math.cos(radian);
        //console.log("xCenter:" + xCenter + " x: " + x + " r:" + radius + " radian:" + radian);
        return x;
    }

    getCircleY(yCenter, radius, radian){
        const y = yCenter + radius * Math.sin(radian);
        //console.log("yCenter:" + yCenter + " y: " + y + " r:" + radius + " radian:" + radian);
        return y;
    }

    getExtrudeSetting( ringHeight ){
        const extrudeSetting = { 
            amount: ringHeight, 
            bevelEnabled: true, 
            steps: 1, 
            bevelSize: 0, 
            bevelThickness: 1, 
            curveSegments: 100 };
        return extrudeSetting;
    }

    createTextMesh ( txt, posX, posY, posZ ){
        console.log("[createTextMesh]" + " txt: " + txt + " txtPosX: " + posX + " txtPosY: " + posY + " txtPosZ: " + posZ);

        var loader = new THREE.FontLoader();
        var font = loader.parse(fontJSON);
        console.log(font);
        var txtGeometry = new THREE.TextGeometry( txt, {
            font: font,
            size: 1,
            height: 0.5,
            curveSegments: 12,
            bevelEnabled: false,
            bevelThickness: 0.1,
            bevelSize: 0.1,
            bevelSegments: 0.1
        } );
        txtGeometry.computeBoundingBox();
        var xOffset = (txtGeometry.boundingBox.max.x - txtGeometry.boundingBox.min.x) * -0.5;
        var yOffset = (txtGeometry.boundingBox.max.y - txtGeometry.boundingBox.min.y) * -0.5;

        var txtMaterial = new THREE.MeshPhongMaterial({color:0x000000});
        var txtMesh = new THREE.Mesh(txtGeometry, txtMaterial);
        txtMesh.position.x = posX + xOffset;
        txtMesh.position.y = posY + yOffset;
        txtMesh.position.z = posZ;

        return txtMesh;
    }

    createCenterCircle( layerNum, pieceColor, height, pieceName ){
        if (layerNum != 1){
            return null;
        }
        console.log("[createCenterCircle]" + " layerNum: " + layerNum + " pieceColor: " + pieceColor + " height: " + height);

        const radius = this.ringSize - this.radiusMargin;
        const centerCircleShape = new THREE.Shape();
        centerCircleShape.moveTo(0, 0);
        centerCircleShape.absarc(0, 0, radius, this.degreeToRadian(0), this.degreeToRadian(360), false);

        const extrudeSetting = this.getExtrudeSetting(height);
        const geometry = new THREE.ExtrudeGeometry( centerCircleShape, extrudeSetting );
        const centerCircleMesh = new THREE.Mesh ( geometry, new THREE.MeshPhongMaterial( { color: pieceColor }) );
        centerCircleMesh.name = pieceName;

        const txtPosX = 0
        const txtPosY = 0
        const txtPosZ = height + 1;
        const txtRotation = 0;
        const txtMesh = this.createTextMesh(pieceName, txtPosX, txtPosY, txtPosZ);
        centerCircleMesh.add(txtMesh);

        return centerCircleMesh;
    }

    createRingPiece( layerNum, pieceColor, height, startDegree, endDegree, pieceName ){
        if (layerNum < 2 || startDegree < 0 || endDegree > 360){
            return null;
        }

        const innerRadius = (this.ringSize * (layerNum - 1)) + this.radiusMargin;
        const outerRadius = (this.ringSize * layerNum) - this.radiusMargin;
        const startRadian = this.degreeToRadian(startDegree + this.angleMargin);
        const endRadian = this.degreeToRadian(endDegree - this.angleMargin);

        console.log("[createRingPiece]" + " layerNum: " + layerNum + " pieceColor: " + pieceColor + " height: " + height + " startDegree: "+ startDegree + " endDegree: " + endDegree);

        const ringPieceShape = new THREE.Shape();
        ringPieceShape.moveTo(this.getCircleX(0, innerRadius, startRadian), this.getCircleY(0, innerRadius, startRadian));
        ringPieceShape.absarc(0, 0, innerRadius, startRadian, endRadian, false);
        ringPieceShape.lineTo(this.getCircleX(0, outerRadius, endRadian), this.getCircleY(0, outerRadius, endRadian));
        ringPieceShape.absarc(0, 0, outerRadius, endRadian, startRadian, true);
        ringPieceShape.lineTo(this.getCircleX(0, innerRadius, startRadian), this.getCircleY(0, innerRadius, startRadian));

        const extrudeSetting = this.getExtrudeSetting(height);
        const geometry = new THREE.ExtrudeGeometry( ringPieceShape, extrudeSetting );
        var ringPieceMesh = new THREE.Mesh( geometry, new THREE.MeshPhongMaterial( { color: pieceColor } ) );
        ringPieceMesh.name = pieceName;

        const midRadius = (outerRadius + innerRadius) / 2;
        const midRadian = (endRadian + startRadian) / 2;
        const txtPosX = this.getCircleX(0, midRadius, midRadian);
        const txtPosY = this.getCircleY(0, midRadius, midRadian);
        const txtPosZ = height + 1;
        const txtMesh = this.createTextMesh(pieceName, txtPosX, txtPosY, txtPosZ);
        ringPieceMesh.add(txtMesh);

        return ringPieceMesh;
    }

    drawRingSegments(listVar, startDegree, endDegree){
        // Implementing Main Logic
        // Layer, Start Radian, End Radian
        var curElemCount = listVar.length;
        var degreePerElem = (endDegree - startDegree) / curElemCount;

        var curStartDegree = startDegree;
        var curEndDegree = startDegree + degreePerElem;

        console.log("curElemCount: " + curElemCount + " degreePerElem: " + degreePerElem);

        console.log("listVar");
        console.log(listVar);

        listVar.forEach(curElem => {
            //
            // Calculate the height and the color of a ring piece
            //
            console.log("curElem");
            console.log(curElem);

            var pieceColor, height, layerNum;
            if ("securityLevel" in curElem){
                height = (curElem.securityLevel) / 10 * this.pieceHeightScale + this.defaultHeight;
                var palleteIdx = Math.ceil( (curElem.securityLevel) / (100 / (this.securityColorPallete.length - 1)) );
                if (palleteIdx == 0) palleteIdx = 1;
                pieceColor = this.securityColorPallete[palleteIdx];
            } else {
                height = this.defaultHeight;
                pieceColor = this.securityColorPallete[0];
            }
            console.log("height: " + height + " palleteIdx: " + palleteIdx);

            //
            // Get the tier of this element from the definition
            //
            if (curElem.tier in this.tierDef){
                layerNum = this.tierDef[curElem.tier];
            } else{
                layerNum = 0
            }

            console.log("[drawRingSegments]" + " name: "+ curElem.name + "curStartDegree: " + curStartDegree + " curEndDegree: " + curEndDegree + " height: " + height + " layerNum: " + layerNum);

            //
            // Create a visualization piece
            //
            if (layerNum == 0){
                // Do not draw this element
            } else if (layerNum == 1){
                const center = this.createCenterCircle(layerNum, pieceColor, height, curElem.name);
                this.scene.add(center);
            } else {
                const piece = this.createRingPiece(layerNum, pieceColor, height, curStartDegree, curEndDegree, curElem.name);
                this.scene.add(piece);
            }

            //
            // For Children Elements
            //
            if (curElem.childElements){
                var children = {};
                curElem.childElements.forEach(childElement => {
                    console.log("childElement");
                    console.log(childElement);
                    if (childElement.tier in children){
                        children[childElement.tier].push(childElement);
                    } else {
                        children[childElement.tier] = [];
                        children[childElement.tier].push(childElement);
                    }
                });
                
                console.log(children);
                Object.keys(children).forEach(nextTierName => {
                    this.drawRingSegments(children[nextTierName], curStartDegree, curEndDegree);
                })
            }
            
            //
            // Increase start and end degrees for the next element
            //
            curStartDegree = curStartDegree + degreePerElem;
            curEndDegree = curEndDegree + degreePerElem;
        });
    }

    animate() {
        requestAnimationFrame( this.animate.bind(this) );
        this.renderer.render( this.scene, this.camera );
        // this.render();
    }
    
    render() {
        this.renderer.render( this.scene, this.camera );
    }

    draw(){
        // Basic ThreeJS Configuration (Scene, Camera, Light)
        if (this.scene === null){ this.scene = new THREE.Scene(); }

        if (this.camera === null){
            this.camera = new THREE.PerspectiveCamera( 50, window.innerWidth / window.innerHeight, 1, 1000 );
            this.camera.position.set( 0, 0, 100 );
            const light = new THREE.PointLight( 0xffffff, 0.9 );
            this.camera.add( light );
            this.scene.add( this.camera );
        }

        this.pgTopo.forEach(element =>{
            this.drawRingSegments(element, 0, 360);
        });

        // Rendering Configuration
        if (this.renderer === null){
            this.renderer = new THREE.WebGLRenderer( { antialias: true } );
            this.renderer.setClearColor( 0xf0f0f0 );
            this.renderer.setPixelRatio( window.devicePixelRatio );
            this.renderer.setSize( window.innerWidth, window.innerHeight );
            this.renderer.shadowMapEnabled = true;
            this.renderer.shadowMapType = THREE.PCFSoftShadowMap;
            this.renderer.setSize( window.innerWidth, window.innerHeight );
        }

        //Document Management
        var container;
        container = document.createElement( 'div' );
        document.body.appendChild( container );
        container.appendChild( this.renderer.domElement );
        var controls = new THREE.OrbitControls( this.camera, this.renderer.domElement );

        this.animate();
    }

    httpGetAsync(theUrl, callback)
    {
        var xmlHttp = new XMLHttpRequest();
        xmlHttp.onreadystatechange = function() { 
            if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
                callback(xmlHttp.responseText);
        }
        xmlHttp.open("GET", theUrl, true); // true for asynchronous 
        xmlHttp.send(null);
    }
}

var vis = new OnionRing3DVisualizer(5, 3);
vis.loadTopology(onionRing3DData);
vis.draw();

const source = new EventSource('/onionring/onionring3d/update');
source.addEventListener('message', function(message) {
    console.log('I have got a message', message);
    // var piece = vis.scene.getObjectByName("K-ONE");
    // console.log(vis.scene);
    // console.log(piece);
    // vis.scene.remove(piece);
    // vis.animate();
});
