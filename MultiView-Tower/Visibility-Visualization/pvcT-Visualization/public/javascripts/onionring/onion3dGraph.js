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
        this.securityColorPallete = [ 0xD0D0D0, 0x00FF000, 0x66FF000, 0x99FF000, 0xCCFF000, 0xFFFF00, 0xFFCC00, 0xFF9900, 0xFF6600, 0xFF3300, 0xFF0000 ] // DarkGray, WhiteGray, Green, Yellow, Red
        this.fixedColorPallete = [0x505050];
        
        // Instance Attributes for onion-ring topology
        this.tierDef = null;
        this.pgTopo = null;
        this.fixedTiers = ["tower", "core-cloud", "edge-cloud"];
        
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

    getTierNum(tierName){
        var matchedTierNum = 0;
        this.tierDef.some( function(tier, idx){
            if (tier === tierName){
                matchedTierNum = idx + 1;
                return true;
            }
        });
        return matchedTierNum;
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
            depth: ringHeight, 
            bevelEnabled: true, 
            steps: 1, 
            bevelSize: 0, 
            bevelThickness: 1, 
            curveSegments: 100 };
        return extrudeSetting;
    }

    createTextMeshes (txt, posX, posY, posZ){
        console.log("[createTextMeshes]" + " txt: " + txt + " txtPosX: " + posX + " txtPosY: " + posY + " txtPosZ: " + posZ);

        var loader = new THREE.FontLoader();
        var font = loader.parse(fontJSON);
        var txtPieces = [];

        if (txt.length > 7){
            const ts = txt.split("-");
            var txtPiece = ""
            ts.forEach(t => {
                if (txtPiece === ""){
                    txtPiece = t;
                }
                else if ((txtPiece.length + t.length + 1) > 7){
                    txtPieces.push(txtPiece);
                    txtPiece = "-" + t;
                }
                else{
                    txtPiece = txtPiece + "-" + t;
                }
            });
            txtPieces.push(txtPiece);
        } else{
            txtPieces.push(txt);
        }

        var txtMeshes = [];
        var txtYoffsets = [];
        var offsetIdx = 0;

        for (var i=txtPieces.length-1; i>= ((txtPieces.length-1) *-1); i=i-2 ) {
            txtYoffsets.push( (0.5 * i) - 0.5 )
        }

        txtPieces.forEach(txtPiece => {
            var txtGeometry = new THREE.TextGeometry( txtPiece, {
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

            var textWidth = txtGeometry.boundingBox.max.x - txtGeometry.boundingBox.min.x;
            var textHeight = txtGeometry.boundingBox.max.y - txtGeometry.boundingBox.min.y;
    
            var txtMaterial = new THREE.MeshPhongMaterial({color:0x000000});
            var txtMesh = new THREE.Mesh(txtGeometry, txtMaterial);
            txtMesh.position.x = posX + (textWidth * -0.5);
            txtMesh.position.y = posY + (textHeight * (txtYoffsets[offsetIdx]*1.2));
            txtMesh.position.z = posZ;
            txtMeshes.push(txtMesh);

            offsetIdx = offsetIdx + 1;
        });

        return txtMeshes;
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

        // Create object abstract
        const extrudeSetting = this.getExtrudeSetting(height);
        const geometry = new THREE.ExtrudeGeometry( centerCircleShape, extrudeSetting );

        // Create boundary line of the object
        const edges = new THREE.EdgesGeometry( geometry );
        const line = new THREE.LineSegments( edges, new THREE.LineBasicMaterial( { color: 0xffffff } ) );
        this.scene.add(line);

        // Create actual shape of the object
        const centerCircleMesh = new THREE.Mesh ( geometry, new THREE.MeshPhongMaterial( { color: pieceColor }) );
        centerCircleMesh.name = pieceName;

        // Create texts drawn on the object
        const txtPosX = 0
        const txtPosY = 0
        const txtPosZ = height + 1;
        const txtRotation = 0;
        const txtMeshes = this.createTextMeshes(pieceName, txtPosX, txtPosY, txtPosZ);

        txtMeshes.forEach(txtMesh => {
            centerCircleMesh.add(txtMesh);
        });

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

        // Create 3D object
        const extrudeSetting = this.getExtrudeSetting(height);
        const geometry = new THREE.ExtrudeGeometry( ringPieceShape, extrudeSetting );

        // Create boundary line of the object
        const edges = new THREE.EdgesGeometry( geometry );
        const line = new THREE.LineSegments( edges, new THREE.LineBasicMaterial( { color: 0xFF0000, linewidth: 5 } ) );
        this.scene.add(line);

        // Create actual shape of the object
        var ringPieceMesh = new THREE.Mesh( geometry, new THREE.MeshPhongMaterial( { color: pieceColor } ) );
        ringPieceMesh.name = pieceName;

        const midRadius = (outerRadius + innerRadius) / 2;
        const midRadian = (endRadian + startRadian) / 2;
        const txtPosX = this.getCircleX(0, midRadius, midRadian);
        const txtPosY = this.getCircleY(0, midRadius, midRadian);
        const txtPosZ = height + 1;
        // const txtMesh = this.createTextMesh(pieceName, txtPosX, txtPosY, txtPosZ);
        const txtMeshes = this.createTextMeshes(pieceName, txtPosX, txtPosY, txtPosZ);
        
        txtMeshes.forEach(txtMesh => {
            ringPieceMesh.add(txtMesh);
        });

        

        return ringPieceMesh;
    }

    drawRingSegments(listVar, startDegree, endDegree){
        // Implementing Main Logic
        // Layer, Start Radian, End Radian
        var curElemCount = listVar.length;
        var degreePerElem = (endDegree - startDegree) / curElemCount;

        var curStartDegree = startDegree;
        var curEndDegree = startDegree + degreePerElem;

        console.log("[drawRingSegments]", "RingSegments", listVar);

        listVar.forEach(curElem => {
            //
            // Calculate the height and the color of a ring piece
            //
            var pieceColor, height, layerNum;

            
            if ("securityLevel" in curElem){
                height = (curElem.securityLevel) / 10 * this.pieceHeightScale + this.defaultHeight;

                var palleteIdx = Math.ceil( (curElem.securityLevel) / (100 / (this.securityColorPallete.length - 1)) );
                if (palleteIdx == 0) palleteIdx = 1;

                pieceColor = this.securityColorPallete[palleteIdx];
            } else {
                height = this.defaultHeight;
                if (this.fixedTiers.includes(curElem.tier)){
                    pieceColor = this.fixedColorPallete[0];
                } else{
                    pieceColor = this.securityColorPallete[0];
                }
            }

            //
            // Get the tier of this element from the definition
            //
            layerNum = this.getTierNum(curElem.tier);
            console.log("[drawRingSegments]" + " name: "+ curElem.name + "curStartDegree: " + curStartDegree + " curEndDegree: " + curEndDegree + " degreePerElem: " + degreePerElem + " height: " + height + " layerNum: " + layerNum);

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
                    if (childElement.tier in children){
                        children[childElement.tier].push(childElement);
                    } else {
                        children[childElement.tier] = [];
                        children[childElement.tier].push(childElement);
                    }
                });
                
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
