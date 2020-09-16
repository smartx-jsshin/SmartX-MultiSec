function decodeHtmltoJson(text){
    // console.log("Before Decoding: " + onionRingData);

    var textArea = document.createElement('textarea');
    textArea.innerHTML = text;
    var jsonFromText = JSON.parse(textArea.value);

    // console.log("After Decoding: ");
    // console.log(jsonFromText);

    return jsonFromText;
}

function draw() {
    // Configuration Variables for Onion-ring
    console.log("Start onion3dGraph.Draw()");

    const ringSize = 5;
    const pieceHeightScale = 3;
    const defaultHeight = 0.2 * pieceHeightScale;
    const resourceColorPallete = [ 0xC0C0C0, 0xC0C0C0, 0x008000, 0x008000, 0x008000, 0xFFFF00, 0xFFFF00, 0x0000FF ] // Silver, Silver, Green, Green, Green, Yellow, Yellow, Blue
    const securityColorPallete = [ 0x808080, 0x00FF000, 0x66FF000, 0x99FF000, 0xCCFF000, 0xFFFF00, 0xFFCC00, 0xFF9900, 0xFF6600, 0xFF3300, 0xFF0000 ] // Gray, Green, Yellow, Red
    
    const onionRing3DDataJson = decodeHtmltoJson(onionRing3DData);
    console.log(onionRing3DDataJson);

    const tierDef = onionRing3DDataJson.tier_definition;
    const pgTopo = onionRing3DDataJson.playground_topology;
    console.log(tierDef);
    console.log(pgTopo);

    const radiusMargin = 0.2;
    const angleMargin = 0.15;


    //Document Management
    var container;
    container = document.createElement( 'div' );
    document.body.appendChild( container );


    // Basic ThreeJS Configuration (Scene, Camera, Light)
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera( 50, window.innerWidth / window.innerHeight, 1, 1000 );
    camera.position.set( 0, 0, 100 );
    scene.add( camera );

    const light = new THREE.PointLight( 0xffffff, 0.9 );
    camera.add( light );


    // Creating a piece of onion-ring
    function degreeToRadian(degree){
        const radian = Math.PI * degree / 180;
        return radian;
    }

    function getCircleX(xCenter, radius, radian){
        const x = xCenter + radius * Math.cos(radian);
        //console.log("xCenter:" + xCenter + " x: " + x + " r:" + radius + " radian:" + radian);
        return x;
    }

    function getCircleY(yCenter, radius, radian){
        const y = yCenter + radius * Math.sin(radian);
        //console.log("yCenter:" + yCenter + " y: " + y + " r:" + radius + " radian:" + radian);
        return y;
    }

    function getExtrudeSetting( ringHeight ){
        const extrudeSetting = { 
            amount: ringHeight, 
            bevelEnabled: true, 
            steps: 1, 
            bevelSize: 0, 
            bevelThickness: 1, 
            curveSegments: 100 };
        return extrudeSetting;
    }

    function createTextMesh ( txt, posX, posY, posZ ){
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

    function createCenterCircle( layerNum, pieceColor, height, pieceName ){
        if (layerNum != 1){
            return null;
        }
        console.log("[createCenterCircle]" + " layerNum: " + layerNum + " pieceColor: " + pieceColor + " height: " + height);

        const radius = ringSize - radiusMargin;
        const centerCircleShape = new THREE.Shape();
        centerCircleShape.moveTo(0, 0);
        centerCircleShape.absarc(0, 0, radius, degreeToRadian(0), degreeToRadian(360), false);

        const extrudeSetting = getExtrudeSetting(height);
        const geometry = new THREE.ExtrudeGeometry( centerCircleShape, extrudeSetting );
        const centerCircleMesh = new THREE.Mesh ( geometry, new THREE.MeshPhongMaterial( { color: pieceColor }) );

        const txtPosX = 0
        const txtPosY = 0
        const txtPosZ = height + 1;
        const txtRotation = 0;
        const txtMesh = createTextMesh(pieceName, txtPosX, txtPosY, txtPosZ);
        centerCircleMesh.add(txtMesh);

        return centerCircleMesh;
    }

    function createRingPiece( layerNum, pieceColor, height, startDegree, endDegree, pieceName ){
        if (layerNum < 2 || startDegree < 0 || endDegree > 360){
            return null;
        }

        const innerRadius = (ringSize * (layerNum - 1)) + radiusMargin;
        const outerRadius = (ringSize * layerNum) - radiusMargin;
        const startRadian = degreeToRadian(startDegree + angleMargin);
        const endRadian = degreeToRadian(endDegree - angleMargin);

        console.log("[createRingPiece]" + " layerNum: " + layerNum + " pieceColor: " + pieceColor + " height: " + height + " startDegree: "+ startDegree + " endDegree: " + endDegree);

        const ringPieceShape = new THREE.Shape();
        ringPieceShape.moveTo(getCircleX(0, innerRadius, startRadian), getCircleY(0, innerRadius, startRadian));
        ringPieceShape.absarc(0, 0, innerRadius, startRadian, endRadian, false);
        ringPieceShape.lineTo(getCircleX(0, outerRadius, endRadian), getCircleY(0, outerRadius, endRadian));
        ringPieceShape.absarc(0, 0, outerRadius, endRadian, startRadian, true);
        ringPieceShape.lineTo(getCircleX(0, innerRadius, startRadian), getCircleY(0, innerRadius, startRadian));

        const extrudeSetting = getExtrudeSetting(height);
        const geometry = new THREE.ExtrudeGeometry( ringPieceShape, extrudeSetting );
        var ringPieceMesh = new THREE.Mesh( geometry, new THREE.MeshPhongMaterial( { color: pieceColor } ) );


        const midRadius = (outerRadius + innerRadius) / 2;
        const midRadian = (endRadian + startRadian) / 2;
        const txtPosX = getCircleX(0, midRadius, midRadian);
        const txtPosY = getCircleY(0, midRadius, midRadian);
        const txtPosZ = height + 1;
        const txtMesh = createTextMesh(pieceName, txtPosX, txtPosY, txtPosZ);
        ringPieceMesh.add(txtMesh);

        return ringPieceMesh;
    }

    function drawRingSegments(listVar, startDegree, endDegree){
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
                height = (curElem.securityLevel) / 10 * pieceHeightScale + defaultHeight;
                var palleteIdx = Math.ceil( (curElem.securityLevel) / (100 / (securityColorPallete.length - 1)) );
                if (palleteIdx == 0) palleteIdx = 1;
                pieceColor = securityColorPallete[palleteIdx];
            } else {
                height = defaultHeight;
                pieceColor = securityColorPallete[0];
            }
            console.log("height: " + height + " palleteIdx: " + palleteIdx);

            //
            // Get the tier of this element from the definition
            //
            if (curElem.tier in tierDef){
                layerNum = tierDef[curElem.tier];
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
                const center = createCenterCircle(layerNum, pieceColor, height, curElem.name);
                group.add(center);
            } else {
                const piece = createRingPiece(layerNum, pieceColor, height, curStartDegree, curEndDegree, curElem.name);
                group.add(piece);
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
                    drawRingSegments(children[nextTierName], curStartDegree, curEndDegree);
                })
            }
            
            //
            // Increase start and end degrees for the next element
            //
            curStartDegree = curStartDegree + degreePerElem;
            curEndDegree = curEndDegree + degreePerElem;
        });
    }

    const group = new THREE.Group();
    scene.add( group );

    console.log(pgTopo);
    pgTopo.forEach(element =>{
        drawRingSegments(element, 0, 360);
    });

    // Rendering Configuration
    const renderer = new THREE.WebGLRenderer( { antialias: true } );
    renderer.setClearColor( 0xf0f0f0 );
    renderer.setPixelRatio( window.devicePixelRatio );
    renderer.setSize( window.innerWidth, window.innerHeight );
    renderer.shadowMapEnabled = true;
    renderer.shadowMapType = THREE.PCFSoftShadowMap;
    
    //group.castShadow = true;
    //group.receiveShadow = false;

    container.appendChild( renderer.domElement );
    var controls = new THREE.OrbitControls( camera, renderer.domElement );
    renderer.setSize( window.innerWidth, window.innerHeight );

    function animate() {

        requestAnimationFrame( animate );
    
        render();
    
    }
    
    function render() {
    
        renderer.render( scene, camera );
    
    }

    animate();
}

draw()