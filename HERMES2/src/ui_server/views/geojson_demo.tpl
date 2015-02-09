%rebase outer_wrapper title_slogan=_("GeoJson Test"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId
<!---
###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################
-->
<link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet-0.6.4/leaflet.css" />
<script src="http://cdn.leafletjs.com/leaflet-0.6.4/leaflet.js"></script>
<script src="http://d3js.org/d3.v3.min.js" charset="utf-8"></script>
<script src="http://d3js.org/queue.v1.min.js"></script>
<script src="http://maps.google.com/maps/api/js?v=3.2&sensor=false"></script>
<script src="http://matchingnotes.com/javascripts/leaflet-google.js"></script>
<script src="{{rootPath}}static/leaflet-layerjson.js"></script>
<style>

.leaflet-google-layer{
	z-index:0;
}
.leaflet-map-pane{
	z-index:100;
}
#leafmap {
	height:800px;
	width:800px;
}
	
.legend {
    padding: 0px 0px;
    font: 10px sans-serif;
    background: white;
    background: rgba(255,255,255,0.8);
    box-shadow: 0 0 15px rgba(0,0,0,0.2);
    border-radius: 5px;
}

.key path {
  display: none;
}

</style>
</head>
<body>

	<div id="leafmap"></div>

<script>
var geojsonFeature = [
{
    "type": "Feature",
    "properties": {
        "name": "Coors Field",
        "amenity": "Baseball Stadium",
        "popupContent": "This is where the Rockies play!"
    },
    "geometry": {
        "type": "Point",
        "coordinates": [2.31, 9.22]
    }
},
{
    "type": "Feature",
    "properties": {
        "name": "Coors Field",
        "amenity": "Football Stadium",
        "popupContent": "This is where the Rockies play!"
    },
    "geometry": {
        "type": "Point",
        "coordinates": [2.22, 9.12]
    }
}
];

function onEachFeature(feature,layer){
	if(feature.properties && feature.properties.popupContent){
		layer.bindPopup(feature.properties.popupContent);
	}
}

$(function() {
	
	/*L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    	attribution: 'Map data (c) <a href="http://openstreetmap.org">OpenStreetMap</a> contributors',
    	maxZoom: 18
	}).addTo(map);
	*/
	var googleRoadLayer = new L.Google('ROADMAP');
	var googleSatelliteLayer = new L.Google('SATELLITE');
	
	var myLayer = L.geoJson(null,{onEachFeature: onEachFeature});
	
	$.getJSON("{{rootPath}}json/utilgeojson?modelId={{modelId}}")
		.done(function(data){
			if(data.success){
				myLayer.addData(data.features);
			}
			else{
    			alert('{{_("Failed: ")}}'+data.msg);
			}
		})
		.fail(function(jqxhr, textStatus, error) {
			alert('{{_("Error: ")}}'+jqxhr.responseText);
		});	
		
	var map = L.map('leafmap', {
		center: [9.22,2.31],
		zoom: 0,
		layers:[googleRoadLayer,myLayer],
		enableHighAccuracy: true
	});
	//map.fitBounds(myLayer);
	map.on('overlayadd',function(e) {
		map.fitBounds(e.layer);
	});
	
	var baseMaps = {
		"Roadmap":googleRoadLayer,
		"Satellite":googleSatelliteLayer
	};
	
	var overlayMaps = {
		"Locations":myLayer
	}
	L.control.layers(baseMaps, overlayMaps).addTo(map);
	
	
})	




/*
function makeMap(error, gjson_1) {
    function matchKey(datapoint, key_variable){
        return(parseFloat(key_variable[0][datapoint]));
    };
    var map = L.map('map').setView([9.22, 2.31], 10);
    L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: 'Map data (c) <a href="http://openstreetmap.org">OpenStreetMap</a> contributors'
    }).addTo(map);
 	
    function style_1(feature) {
    	return {
        	fillColor: 'blue',
        	weight: 1,
        	opacity: 1,
        	color: 'black',
        	fillOpacity: 0.6
    	};
    }	
};
*/

</script>
</body>