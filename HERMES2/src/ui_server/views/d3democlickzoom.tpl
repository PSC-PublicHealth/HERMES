%rebase outer_wrapper title_slogan=_("GeoJson Test"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultId=resultsId
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
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/d3/topojson.v1.min.js"></script>
<script src="{{rootPath}}static/queue.min.js"></script>
<script src="{{rootPath}}static/hermes_info_dialogs.js"></script>
<script src="{{rootPath}}static/rainbowvis.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/rickshaw-master/rickshaw.css"/>
<link rel="stylesheet" href="{{rootPath}}static/linechart-widgets/linechart.css"/>
<script src="{{rootPath}}static/rickshaw-master/rickshaw.js"></script>
<script src="{{rootPath}}static/linechart-widgets/linechart.js"></script>
<script src="{{rootPath}}static/dimple.v2.1.2/dimple.v2.1.2.min.js"></script>
<script src="{{rootPath}}static/barchart-widgets/vaccine_availability_barchart.js"></script>

<script>
$(function() {
	$.ajax({
		url: '{{rootPath}}json/dialoghtmlforstore',
		dataType:'json',
		data:{name:'model_store_info',geninfo:1,utilinfo:1,popinfo:1,storedev:1,transdev:1,vacavail:1,fillratio:1,invent:1,availplot:1},
		success:function(data){
			console.log(data.htmlString);
			$(document.body).append(data.htmlString);
		}
	})
});
</script>
<div id="geo_map3d">
<!--<div id="geo_buttons">
<div id="geo_layers">
<table>
<tr><td colspan=3>
<p style="font-size:large;">Layers:</p>
</td></tr>
<tr>
<p style="font-size:medium;">
<td width="50px"></td><td>Population:</td><td width:"100px"> <input type="checkbox" id="ge_show_population" checked /></td></tr>
<td width="50px"></td><td>Utilization:</td><td width:"100px"> <input type="checkbox" id="ge_show_utilization" value="On"/></td></tr>
<td width="50px"></td><td>Vaccines:</td><td width:"100px"> <input type="checkbox" id="ge_show_vaccine" value="On"/></td></tr>
<td width="50px"></td><td>Routes:</td><td width:"100px"> <input type="checkbox" id="ge_show_routes" value="On"/></td></tr>
</table>
</p>
</div>
</div>-->
<div class="map-container"></div>
</div>


<style>
#geo_map3d { 
  position: relative;
  top: 10px;
  left: 10px;
  height: 500px;
  width:  600px;
  z-index: 2;
  float: left;
  visibility:visible;
}

#geo_buttons { 
  position: relative;
  top: 10px;
  height: 500px;
  width: 300px;
  z-index: 2;
  visibility: visible;
  border-style:solid;
  border-width: 2px;
  float: right;
  border-radius:2px;
}

#map-container {
	width:400px;
	height:400px;
}

.ge_layer_button_table { 
  width:100%;
}

.ge_layer_button_table .td { 
  padding:10px;
}

#geo_layers {
  position:absolute;
  top:10px;
  left:10px;
  width:280px;
  height:200px;
  border-style:solid;
  border-width:1px;
  border-radius:3px;

}

.ge_layer_button_container { 
  align: center;
}

.ge_layer_button { 
  width:125px;
  height:75px;
}
.graticule {
	  fill: none;
	  stroke: #777;
	  stroke-opacity: .5;
	  stroke-width: .5px;
	  pointer-events: none;
	}

.land {
	fill: grey;
	stroke: none;
	pointer-events: none;
	//cursor:pointer;
}

.land.active {
	fill: orange;
	//cursor: pointer;
}

.country-border {
	fill: none;	
	stroke: black;
	stroke-width: 1.0px;
}

.road {
	fill: none;	
	stroke: red;
	stroke-width: 0.1px;
}

.state-border {
	fill: none;
	stroke:white;
	stroke-width: .25px;
	color-rendering: optimizeSpeed;
	shape-rendering: optimizeSpeed;
}

.border {
	fill: none;
	stroke: black;
	stroke-width: .5px;
}

.overlay {
	  fill: none;
	  pointer-events: all;
	}
.country-label {
	  fill: black;
	  fill-opacity: 0.30;
	  font-size: 1px;
	  font-weight: bold;
	  text-anchor: middle;
	  visibility: hidden;
	  pointer-events:none;
	  text-rendering: optimizeSpeed;
	}

.state-label {
	  fill: black;
	  fill-opacity: .50;
	  font-size: .2px;
	  font-weight: 300;
	  text-anchor: middle;
	  visibility: hidden;
	  pointer-events:none;
	  text-rendering: optimizeSpeed;
	}

.pp-label {
	  fill: #000;
	  fill-opacity: 1.0;
	  font-size: 0.15px;
	  font-weight: 300;
	  text-anchor: right;
	  visibility: hidden;
	  pointer-events:none;
	  text-rendering: optimizeSpeed;
	}
.store-circle {
	fill: red;
	fill-opacity:.50;
}
.route-line {
	shape-rendering: optimizeSpeed;
}
//
//
//.place-label {
//	  fill: "black";
//	  fill-opacity: 1.0;
//	  font-size: 10px;
//	}
</style>

<script>
var dialogBoxName = "model_store_info";
var rainbow = new Rainbow();
rainbow.setSpectrum('blue','red');

var curr_scale = 1.0;

console.log("Results");

$(function() {
	$('#ajax_busy_image').show();
});

function doneLoading(){
	$('#ajax_busy_image').hide();
}

var width = 960,
    height = 960;
//active = d3.select(null);
	
var visibleArea;
var invisibleArea;
var area;
var scale = 1;
var translate = [0,0];

var velocity = 0.01;
var then = Date.now();

var path;

var projection = d3.geo.mercator()
	.scale(width / 2 / Math.PI)
	.translate([width / 2, height / 2])
	.clipExtent([[482.10850666666664-10,450.9618130643807-10],[490.158856+10,463.3110997461783+10]])
	//.translate([0,0])
	.precision(1);

//var projection = d3.geo.orthographic()
//	.scale(width / 2.1)
//	.rotate([0,0])
//	.translate([width / 2, height / 2])
//	.precision(.5)
//	.clipAngle(90);



var path = d3.geo.path()
	//.projection({stream: function(s) { return simplify.stream(clip.stream(s)); }})
	.projection(projection)
	.pointRadius(0.025);

var zoom = d3.behavior.zoom()
	.translate([0,0])
	.scale(1)
	//.scale(curr_scale)
	.on("zoom", zoomed);
	
var svg = d3.select(".map-container").append("svg")
	.attr("width", width)
	.attr("height", height);
	//.on("click",stopped,true);

svg.append("rect")
	.attr("class","overlay")
	.attr("width",width)
	.attr("height",height)
	.call(zoom)
	//.call(clip);
	//.on("zoom",zoom);
	//.on("click",reset);
	
var features = svg.append("g");
	//.call(zoom);

queue()
	.defer(d3.json,"{{rootPath}}static/world.10m.states.json")
	.defer(d3.json,"{{rootPath}}static/world.50m.countries.json")
	.defer(d3.json,"{{rootPath}}static/world.10m.pp.json")
	//.defer(d3.json,"{{rootPath}}static/world.roads.json")
	.defer(d3.json,"{{rootPath}}json/storeutilizationlocations?modelId={{modelId}}&resultsId={{resultsId}}")
	.defer(d3.json,"{{rootPath}}json/routelines?modelId={{modelId}}")
	.await(ready);


function ready(error, stateJSON, countryJSON, ppJSON,storeJSON,routesJSON){


//var clip = d3.geo.clipExtent()
//	.extent([[0,0],[width/2,height/2]]);

//var simplify = d3.geo.transform({
//	point: function(x,y,z){
//		if (z >= area) this.stream.point(x*scale + translate[0], y*scale + translate[1]);
//	}
//});



	
	//var b = d3.path.bounds(storeJSON.geoFC);
//d3.json("{{rootPath}}static/world.comb.simp.json", function(error,world){
	var states = stateJSON.objects.state;
	var countries = countryJSON.objects.countries;
	var cTJSON = topojson.feature(countryJSON,countryJSON.objects.countries);
	var smCTJSON = cTJSON.features.filter(function(d) { return d.properties.name == "Benin";});
	
//	features
//		.selectAll(".land")
//		.data(cTJSON.features)
//		.enter()
//			.append("path")
//			.attr("class","land")
//			.attr("d",path)
			
	features
		.append("path")
		.datum(topojson.merge(countryJSON,countryJSON.objects.countries.geometries))
		.attr("class","land")
		.attr("d",path)
		//.call(zoom);

//	features
//		.selectAll("path")
//		.data(topojson.feature(roadsJSON,roadsJSON.objects.roads).features)
//		.enter()
//			.append("path")
//			.attr("class","road")
//			.attr("d",path);
//	
	features
		.selectAll(".country-label")
		.data(topojson.feature(countryJSON,countries).features)
			.enter().append("text")
				.attr("class", "country-label")
				.attr("transform",function(d) { return "translate(" + path.centroid(d) + ")"; })
				//.attr("dy",".35em")
				.text(function(d) {return d.properties.name;});
	
	features
		.selectAll(".state-label")
			.data(topojson.feature(stateJSON,states).features)
		.enter().append("text")
			.attr("class", "state-label")
			.attr("transform",function(d) { return "translate(" + path.centroid(d) + ")"; })
			//.attr("dy",".35em")
			.text(function(d) {
				return d.properties.name;
				}
			);

	features
		.selectAll(".pp-label")
			.data(topojson.feature(ppJSON,ppJSON.objects.populated_places).features)
		.enter().append("text")
			.attr("class", "pp-label")
			.attr("transform",function(d) { 
				var coordinates = [d.properties.lon,d.properties.lat]
				return "translate(" + path.centroid(d) + ")"; })
			.attr("dy",".35em")
			.attr("dx",".55em")
			.text(function(d) {return d.properties.name;});
			
	features.append("path")
		.datum(topojson.mesh(stateJSON,states, function(a,b){return a!==b;}))
		.attr("class","state-border")
		.attr("d",path);
	
	features.append("path")
		.datum(topojson.mesh(countryJSON,countries,function(a,b){return a!==b;}))
		.attr("class","country-border")
		.attr("d",path);
	
//	features.append("path")
//		.datum(topojson.mesh(roadsJSON,roadsJSON.objects.roads,function(a,b){return a!==b;}))
//		.attr("class","road")
//		.attr("d",path);
	
	features
		.selectAll("path")
			.data(topojson.feature(ppJSON,ppJSON.objects.populated_places).features)
		.enter()
			.append("path")
			.datum( function(d) {
						//console.log(d.properties.lon); 
						return {
							type:"Point",
							coordinates:[d.properties.lon,d.properties.lat]};
				})
			.attr("d",path);
	/*
	features
	.selectAll("circle")
		.data(topojson.feature(ppJSON,ppJSON.objects.populated_places).features)
	.enter()
		.append("circle")
			.attr("cx",function(d){
				var coordinates = [d.properties.lon,d.properties.lat]
				//console.log(projection(coordinates));
				//console.log(coordinates);
				return projection(coordinates)[0];
			})
			.attr("cy",function(d) {
				var coordinates = [d.properties.lon,d.properties.lat]
				return projection(coordinates)[1];
			})
			.attr("r",function(d) {
				return 0.05;
			})
			.style("fill","black")
			.style("fill-opacity",1);

	*/
	
	features
		.selectAll(".store-circle")
			.data(storeJSON.geoFC.features)
		.enter()
			.append("circle")
			.attr("class","store-circle")
			.attr("cx",function(d){
				return projection([d.geometry.coordinates[0], d.geometry.coordinates[1]])[0];
			})
			.attr("cy",function(d) {
				return projection([d.geometry.coordinates[0],d.geometry.coordinates[1]])[1];
			})
			.attr("r",function(d) {
				return 0.2/(d.level+1);
			})
			.style("fill",function(d){
				return rainbow.colourAt(100*d.util);
			})
			.style("fill-opacity",1.0)
			.style("stroke","black")
			.style("stroke-width",0.010+"px")
			.on("click",clickDialog);
			
	/*
	features
		.selectAll('.route-line')
			.data(routesJSON.geoFC.features)
		.enter()
			.append("path")
		.attr("d",path)
			.style("stroke","red")
			.style("stroke-width",0.000+"px")
			.style("fill-opacity",0.0);
	*/
	//console.log("BOUNDS " + path.bounds(storeJSON.geoFC));
	zoomToCollection(storeJSON.geoFC);
	//d3.geo.clipExtent([[482.10850666666664,450.9618130643807],[490.158856,463.3110997461783]]);
	//
	//d3.geo.clipExtent()
		//.extent([[b[0][0],b[0][1]],[b[1][0],b[1][1]]]);
	
}

function clickDialog(d) {
	d3.event.preventDefault();
	if($("#model_store_info_dialog").length > 0){
		if ($("#model_store_info_dialog").is(':ui-dialog')) {
			$("#model_store_info_dialog").dialog('close');
		}
		var meta_data = eval(dialogBoxName+"_meta");
		var resId = -1;
		if (meta_data['getResults'] == true){ resId = {{resultsId}};}
		populateStoreInfoDialog("{{rootPath}}","model_store_info",meta_data,"{{modelId}}",d.id,resId);
		$("#model_store_info_dialog").dialog("option","title","Information for Location " + d.id);
		$("#model_store_info_dialog").dialog("open");
	}
}


function zoomToCollection(d) {
	
	var b = path.bounds(d),
	s =  s = .95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
    t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];

	//d3.geo.clipExtent([[b[0][0],b[0][1]],[b[1][0],b[1][1]]]);
	//console.log("bounds" + b);
	svg.transition()
		.duration(750)
		.call(zoom.translate(t).scale(s).event);
}

//function reset(){
//	active.classed("active", false);
//	active = d3.select(null);
//
//	 svg.transition()
//	    .duration(750)
//	    .call(zoom.translate([0, 0]).scale(1).event);
//}

function zoomed() { 
	  //console.log(d3.event.translate);
	  translate = d3.event.translate
	  scale = d3.event.scale
	  area = 1/scale/scale;
	  
	  features.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
	  features.selectAll(".land").style("stroke-width", 1.5 / d3.event.scale + "px");
	  features.selectAll(".state-border").style("stroke-width", .25 / d3.event.scale + "px");
	  features.selectAll(".country-border").style("stroke-width", 1.0 / d3.event.scale + "px");
	  features.selectAll(".road").style("stroke-width", .25 / d3.event.scale + "px");
	  if (d3.event.scale > 1.5){
		  //console.log("SHOULD");
		  features.selectAll(".country-label").style("visibility","visible");
	  }
	  else{
		  //console.log("HIDE");
		  features.selectAll(".country-label").style("visibility","hidden");
	  }
	  if (d3.event.scale > 1.5){
		  //console.log("SHOULD");
		  features.selectAll(".state-label").style("visibility","visible");
	  }
	  else{
		  //console.log("HIDE");
		  features.selectAll(".state-label").style("visibility","hidden");
	  }
	  if (d3.event.scale > 1.5){
		  //console.log("SHOULD");
		  features.selectAll(".pp-label").style("visibility","visible");
	  }
	  else{
		  //console.log("HIDE");
		  features.selectAll(".pp-label").style("visibility","hidden");
	  }
	  curr_scale = d3.event.scale;
}


//If the drag behavior prevents the default click,
//also stop propagation so we don’t click-to-zoom.
function stopped() {
if (d3.event.defaultPrevented) d3.event.stopPropagation();
}


d3.select(self.frameElement).style("height", height + "px");

</script>
