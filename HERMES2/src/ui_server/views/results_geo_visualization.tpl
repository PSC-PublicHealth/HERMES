%rebase outer_wrapper title_slogan=_("Geographic Visualization"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultId=resultsId

<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/d3/topojson.v1.min.js"></script>
<script src="{{rootPath}}static/queue.min.js"></script>
<script src="{{rootPath}}static/hermes_info_dialogs.js"></script>
<script src="{{rootPath}}static/rainbowvis.js"></script>
<script type="text/javascript" src='{{rootPath}}static/Highcharts-3.0.5/js/highcharts.js'></script>

<script>

function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

</script>
<div id="geo_map3d">
	<div class="map-container"></div>
	<div id="geo_layers">
		<table>
			<tr>
				<td colspan=3>
					<p style="font-size:large;">Layers:</p>
				</td>
			</tr>
			<tr>
				<p style="font-size:medium;">
				<td width="50px"></td>
				<td>Population:</td>
				<td width:"100px"> 
					<input type="checkbox" id="show_population"/>
				</td>
			</tr>
			<tr>
				<td width="50px"></td>
				<td>Utilization:</td>
				<td width:"100px"> 
					<input type="checkbox" id="show_utilization" value="On"/>
				</td>
			</tr>
			<tr>
				<td width="50px"></td>
				<td>Vaccines:</td>
				<td width:"100px"> 
					<input type="checkbox" id="show_vaccine" value="On"/>
				</td>
			</tr>
			<tr>
				<td width="50px"></td>
				<td>Routes:</td>
				<td width="100px"></td>
			</tr>
			<tr>
				<td width=50px"></td>
				<td style="padding-left:2em;width:100px;">Color By Route</td>
				<td width="100px"> 
					<input type="checkbox" id="show_routes" value="On"/>
				</td>
			</tr>
			<tr>
				<td width=50px"></td>
				<td style="padding-left:2em;width:100px;">Color By Utilization</td>
				<td width="100px"> 
					<input type="checkbox" id="show_routes_util" value="On"/>
				</td>
				</p>
			</tr>
		</table>
	</div>
	<div id="poplegend" style="float:right;position:relative;bottom:43%;right:50px;background:white;">
		<img height="300px" src="{{rootPath}}static/images/PopLegend.PNG">
	</div>
	<div id="storelegend" style="float:right;position:relative;bottom:43%;right:50px;background:white;">
		<img height="300px" src="{{rootPath}}static/images/StoreLegend.PNG">
	</div>
	<div id="valegend" style="float:right;position:relative;bottom:43%;right:50px;background:white;">
		<img height="300px" src="{{rootPath}}static/images/VALegend.PNG">
	</div>
	<div id="translegend" style="float:right;position:relative;bottom:43%;right:50px;background:white;">
		<img height="300px" src="{{rootPath}}static/images/TransLegend.PNG">
	</div>
</div>


<style>
#geo_map3d { 
  position: relative;
  top: 10px;
  left: 10px;
  height: 650px;
  width: 100%;
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
	width:100%;
	height:650px;
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
  width:200px;
  height:auto;
  border-style:solid;
  border-width:1px;
  border-radius:3px;
  background-color: white;

}

.ge_layer_button_container { 
  align: center;
}

.ge_layer_button { 
  width:125px;
  height:75px;
}

.land {
	fill: grey;
	stroke: none;
	pointer-events: none;
}

.country-border {
	fill: none;	
	stroke: black;
	stroke-width: 1.0px;
}

.road {
	fill: none;
	stroke: #707070;
	stroke-width: 0.1px;
	shape-rendering: 
}

.state-border {
	fill: none;
	stroke:white;
	stroke-width: .25px;
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
	  fill: white;
	  fill-opacity: 0.30;
	  font-size: 1px;
	  font-weight: bold;
	  text-anchor: middle;
	  visibility: visible;
	  pointer-events:none;
	}

.state-label {
	  fill: white;
	  fill-opacity: .50;
	  font-size: .2px;
	  font-weight: 300;
	  text-anchor: middle;
	  visibility: visible;
	  pointer-events:none;
	}

.pp-label {
	  fill: #000;
	  fill-opacity: 1.0;
	  font-size: 0.15px;
	  font-weight: 300;
	  text-anchor: right;
	  visibility: visible;
	  pointer-events:none;
	}
.store-circle {
	visibility: visible;
	cursor:pointer;
}

.util-circle {
	visibility: hidden;
	cursor:pointer;
}

.pop-circle {
	visibility: hidden;
	cursor:pointer;
}

.va-circle {
	visibility: hidden;
	cursor:pointer;
}

.route-line{
	visibility:hidden;
	cursor:pointer;
}
.route-util-line{
	visibility:hidden;
	cursor:pointer;
}

</style>

<script>
var dialogBoxName = "model_store_info";
var rainbow = new Rainbow();
rainbow.setSpectrum('blue','red');
//var routeRain = new Rainbow();
//routeRain.setSpectrum('white','black');
//routeColors = ["black","red","blue","orange","green","purple","white","gold","aqua","maroon"];

var levelColors = ["silver","gold","orange","pink","white","black","green"];
var routeColors = [];
for (var i=0; i < 10000; i++){
	routeColors.push(getRandomColor());
}
console.log(rainbow.colorAt(.52));
var curr_scale = 1.0;

console.log("Results");

$(function() {
	$("#valegend").hide();
	$("#poplegend").hide();
	$("#storelegend").hide();
	$("#translegend").hide();
	$('#ajax_busy_image').show();
});

function doneLoading(){
	$('#ajax_busy_image').hide();
}

var width = 1000;
var height = 600;
var area;


var velocity = 0.01;
var then = Date.now();

var path;

var projection = d3.geo.mercator()
	.clipAngle(90)
	.scale(width / 2 / Math.PI)
	.translate([width / 2, height / 2]);
	//.clipExtent([[451.976725,269.0266997478569],[459.5239275,284.35415601204215]]);
	//.clipExtent([[482.10850666666664-10,450.9618130643807-10],[490.158856+10,463.3110997461783+10]]);
	
var path = d3.geo.path()
	.projection(projection)
	.pointRadius(0.025);

var zoom = d3.behavior.zoom()
	.translate([0,0])
	.scale(1)
	.on("zoom", zoomed);
	
var svg = d3.select(".map-container").append("svg")
	.attr("width", width)
	.attr("height", height)
	.attr("overflow","hidden");
	//.attr("viewbox","0 0 "+ width + " " + height);

svg.append("rect")
	.attr("class","overlay")
	.attr("width",width)
	.attr("height",height)
	.call(zoom)
	
var features = svg.append("g");

queue()
	.defer(d3.json,"{{rootPath}}static/world.10m.states.json")
	.defer(d3.json,"{{rootPath}}static/world.50m.countries.json")
	.defer(d3.json,"{{rootPath}}static/world.10m.pp.json")
	.defer(d3.json,"{{rootPath}}static/world.roads.json")
	.defer(d3.json,"{{rootPath}}json/storeresultslocations?modelId={{modelId}}&resultsId={{resultsId}}")
	.defer(d3.json,"{{rootPath}}json/routeresultslines?modelId={{modelId}}&resultsId={{resultsId}}")
	.await(ready);


$(document).on('keydown', 'body', function(event) { 
    if ((event.keyCode == 109)||(event.keyCode == 173 && event.shiftKey == false)) {
        // numpad minus OR numrow minus pressed
        zoomByFactor(0.8);
    } else if ((event.keyCode == 107)||(event.keyCode == 61 && event.shiftKey == true)) {
        // numpad plus OR numrow plus pressed
        zoomByFactor(1.2);
    }
});

/* factor == 1 to center, factor > 1 to zoom in, factor < 1 to zoom out */
function zoomByFactor(factor) {
    var scale = zoom.scale();
    var newScale = scale * factor;
    var t = zoom.translate();
    var c = [width / 2, height / 2];
    zoom
        .scale(newScale)
        .translate(
            [c[0] + (t[0] - c[0]) / scale * newScale, 
            c[1] + (t[1] - c[1]) / scale * newScale])
    .event(svg.transition().duration(350));
}

function ready(error, stateJSON, countryJSON, ppJSON, roadsJSON, storeJSON,routesJSON){
	var states = stateJSON.objects.state;
	var countries = countryJSON.objects.countries;
	
	//var smCTJSON = cTJSON.features.filter(function(d) { return d.properties.name == "Benin";});
	
	var bounds = path.bounds(storeJSON.geoFC);
	
	// Create a new bounding Box that is some percent larger than the stores
	var newBounds = [[0.0,0.0],[0.0,0.0]];
	var yDiff = bounds[1][0]-bounds[0][0]
	var xDiff = bounds[1][1]-bounds[0][1];
	var perDiff = 3.0;
	newBounds[0][0] = bounds[0][0] - perDiff*yDiff;
	newBounds[1][0] = bounds[1][0] + perDiff*yDiff;
	newBounds[0][1] = bounds[0][1] - perDiff*xDiff;
	newBounds[1][1] = bounds[1][1] + perDiff*xDiff;
	//console.log(bounds);
	//console.log(newBounds);
	var centroid = path.centroid(storeJSON.geoFC);
	//console.log(centroid);
	
	// Create reduced jsons based on proximity to the actual visualization.
	var ctIds = [];
	var ctjson = countryJSON.objects.countries.geometries.filter(function(d){
		thisCentroid = path.centroid(topojson.feature(countryJSON,d));
		//console.log("this Cent" + thisCentroid);
		var flag = ((thisCentroid[0] >= newBounds[0][0] && thisCentroid[0] <= newBounds[1][0]) && 
				(thisCentroid[1] >= newBounds[0][1] && thisCentroid[1] <= newBounds[1][1]));
		if (flag) {
			ctIds.push(d.properties.name);
		}
		return flag;
	});
	
	var ctgjson = topojson.feature(countryJSON,countryJSON.objects.countries).features.filter(
			function(d) { 
				console.log(d.properties.name);
				return ctIds.indexOf(d.properties.name) > -1;
			});
	console.log(ctgjson);
	var stIds = [];
	var stjson = stateJSON.objects.state.geometries.filter(function(d){
		thisCentroid = path.centroid(topojson.feature(stateJSON,d));
		var flag = ((thisCentroid[0] >= newBounds[0][0] && thisCentroid[0] <= newBounds[1][0]) && 
				(thisCentroid[1] >= newBounds[0][1] && thisCentroid[1] <= newBounds[1][1]));
		if (flag) {
			stIds.push(d.properties.name);
		}
		return flag;
	});
	
	var stgjson = topojson.feature(stateJSON,stateJSON.objects.state).features.filter(
			function(d) { 
				console.log(d.properties.name);
				return stIds.indexOf(d.properties.name) > -1;
			});
	
	var ppgjson = topojson.feature(ppJSON,ppJSON.objects.populated_places).features.filter(
			function(d){
				var coordinates = projection(d.geometry.coordinates);
				return ((coordinates[0] >= newBounds[0][0] && coordinates[0] <= newBounds[1][0]) && 
						(coordinates[1] >= newBounds[0][1] && coordinates[1] <= newBounds[1][1]));
				
			});
	
	
	var roadgjson = topojson.feature(roadsJSON,roadsJSON.objects.roads).features.filter(
			function(d){
				thisCentroid = path.centroid(d.geometry);
				return ((thisCentroid[0] >= newBounds[0][0] && thisCentroid[0] <= newBounds[1][0]) && 
						(thisCentroid[1] >= newBounds[0][1] && thisCentroid[1] <= newBounds[1][1]));
			});
	
	features
		.append("path")
		.datum(topojson.merge(countryJSON,ctjson))
		.attr("class","land")
		.attr("d",path);

	features
		.selectAll("path")
		.data(roadgjson)
		.enter()
			.append("path")
			.attr("class","road")
			.attr("d",path);
	
	features.append("path")
		.datum(topojson.mesh(stateJSON,states, function(a,b){
			return ((a!==b) && (stIds.indexOf(a.properties.name)>-1) && (stIds.indexOf(b.properties.name)> -1));}))
		.attr("class","state-border")
		.attr("d",path);
	
	features.append("path")
		.datum(topojson.mesh(countryJSON,countries,function(a,b){
			return ((a!==b) && (ctIds.indexOf(a.properties.name)>-1) && (ctIds.indexOf(b.properties.name)> -1));}))
		.attr("class","country-border")
		.attr("d",path);
	
	features
		.selectAll(".country-label")
		.data(ctgjson)
			.enter().append("text")
				.attr("class", "country-label")
				.attr("transform",function(d) { return "translate(" + path.centroid(d) + ")"; })
				.text(function(d) { return d.properties.name;});
	
	features
		.selectAll(".state-label")
			.data(stgjson)
		.enter().append("text")
			.attr("class", "state-label")
			.attr("transform",function(d) { return "translate(" + path.centroid(d) + ")"; })
			.text(function(d) {return d.properties.name;});
	
	features
		.selectAll(".pp-label")
			.data(ppgjson)
		.enter().append("text")
			.attr("class", "pp-label")
			.attr("transform",function(d) { 
				return "translate(" + path.centroid(d) + ")"; })
			.attr("dy",".35em")
			.attr("dx",".55em")
			.text(function(d) {
				coordinates = path.centroid(d);
				if ((coordinates[0] >= newBounds[0][0] && coordinates[0] <= newBounds[1][0]) &&
					(coordinates[1] >= newBounds[0][1] && coordinates[1] <= newBounds[1][1])){
				return d.properties.name;
				}
			});

	features
		.selectAll("path")
			.data(ppgjson)
		.enter()
			.append("path")
			.datum( function(d) {
				return {
						type:"Point",
						coordinates:[d.properties.lon,d.properties.lat]
					};
				})
			.attr("d",path);

	features
		.selectAll('.route-util-line')
			.data(routesJSON.geoFC.features)
		.enter()
			.append("path")
			.attr("d",path)
			.attr("class","route-util-line")
			.style("stroke",function(d){
				//console.log(routeColors[d.rindex]);
				//return routeColors[d.rindex];
				return "#"+rainbow.colorAt(100*d.util);
			})
			.style("stroke-width",0.025+"px")
			.style("fill-opacity",1.0)
			.on("click",clickRouteDialog);
	features
		.selectAll('.route-line')
			.data(routesJSON.geoFC.features)
		.enter()
			.append("path")
			.attr("d",path)
			.attr("class","route-line")
			.style("stroke",function(d){
				//console.log(routeColors[d.rindex]);
				return routeColors[d.rindex];
				//return "#"+rainbow.colorAt(100*d.util);
			})
			.style("stroke-width",0.025+"px")
			.style("fill-opacity",1.0)
			.on("click",clickRouteDialog);
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
				return 0.5/(d.level+1);
			})
			.style("fill",function(d){
				return levelColors[d.level];
				//"#"+rainbow.colourAt(100*d.util);
			})
			.style("fill-opacity",0.75)
			.style("stroke",function(d){
				return levelColors[d.level];
			})
			.style("visibility","visible")
			.style("stroke-width",0.010+"px")
			.on("click",clickStoreDialog);
	
	features
		.selectAll(".util-circle")
			.data(storeJSON.geoFC.features)
		.enter()
			.append("circle")
			.attr("class","util-circle")
			.attr("cx",function(d){
				return projection([d.geometry.coordinates[0], d.geometry.coordinates[1]])[0];
			})
			.attr("cy",function(d) {
				return projection([d.geometry.coordinates[0],d.geometry.coordinates[1]])[1];
			})
			.attr("r",function(d) {
				return 0.5/(d.level+1);
			})
			.style("fill",function(d){
				return "#"+rainbow.colourAt(100*d.util);
			})
			.style("fill-opacity",1.0)
			.style("stroke",function(d){
				return "black";
				//return levelColors[d.level];
			})
			.style("visibility","hidden")
			.style("stroke-width",0.010+"px")
			.on("click",clickStoreDialog);
	
	features
		.selectAll(".pop-circle")
			.data(storeJSON.geoFC.features)
		.enter()
			.append("circle")
			.attr("class","pop-circle")
			.attr("cx",function(d){
				return projection([d.geometry.coordinates[0], d.geometry.coordinates[1]])[0];
			})
			.attr("cy",function(d) {
				return projection([d.geometry.coordinates[0],d.geometry.coordinates[1]])[1];
			})
			.attr("r",function(d) {
				//console.log(d);
				return 0.005*((100*d.pop));
			})
			.style("fill",function(d){
				return "#"+rainbow.colourAt(100*d.pop);
			})
			.style("fill-opacity",1.0)
			.style("stroke","black")
			.style("stroke-width",0.010+"px")
			.on("click",clickStoreDialog);
	
	features
	.selectAll(".va-circle")
		.data(storeJSON.geoFC.features)
	.enter()
		.append("circle")
		.attr("class","va-circle")
		.attr("cx",function(d){
			return projection([d.geometry.coordinates[0], d.geometry.coordinates[1]])[0];
		})
		.attr("cy",function(d) {
			return projection([d.geometry.coordinates[0],d.geometry.coordinates[1]])[1];
		})
		.attr("r",function(d) {
			if (d.va == 0.0){
				return 0.0;
			}
			else {
			//console.log(d);
				return 0.1;
			}
		})
		.style("fill",function(d){
			console.log(d.va);
			return "#"+rainbow.colourAt(100.0-d.va);
		})
		.style("fill-opacity",1.0)
		.style("stroke","black")
		.style("stroke-width",0.010+"px")
		.on("click",clickStoreDialog);
	zoomToCollection(storeJSON.geoFC);
	doneLoading();
}

// Turn on and off the elements
$("#show_population").click(function(){
	if ($("#show_population").is(':checked')){
		features.selectAll(".store-circle").style('visibility','hidden');
		features.selectAll(".pop-circle").style('visibility','visible');
		$("#poplegend").width("100px");
		$("#poplegend").show();
	}
	else {
		features.selectAll(".pop-circle").style('visibility','hidden');
		features.selectAll(".store-circle").style('visibility','visible');
		$("#poplegend").width("0px");
		$("#poplegend").hide();
	}
});
$("#show_routes").click(function(){
	if ($("#show_routes").is(':checked')){
		if($("#show_routes_util").is(':checked')){
			$("#show_routes_util").click();
		}
		features.selectAll(".route-line").style('visibility','visible');
		//$("#translegend").width("100px");
		//$("#translegend").show();
	}
	else {
		features.selectAll(".route-line").style('visibility','hidden');
		//$("#translegend").width("0px");
		//$("#translegend").hide();
	}
});
$("#show_routes_util").click(function(){
	if ($("#show_routes_util").is(':checked')){
		if($("#show_routes").is(':checked')){
			$("#show_routes").click();
		}
		features.selectAll(".route-util-line").style('visibility','visible');
		$("#translegend").width("100px");
		$("#translegend").show();
	}
	else {
		features.selectAll(".route-util-line").style('visibility','hidden');
		$("#translegend").width("0px");
		$("#translegend").hide();
	}
});


$("#show_vaccine").click(function(){
	if ($("#show_vaccine").is(':checked')){
		features.selectAll(".store-circle").style('visibility','hidden');
		features.selectAll(".va-circle").style('visibility','visible');
		$("#valegend").width("100px");
		$("#valegend").show();
	}
	else {
		features.selectAll(".va-circle").style('visibility','hidden');
		features.selectAll(".store-circle").style('visibility','visible');
		$("#valegend").width("0px");
		$("#valegend").hide();
	}
});
$("#show_utilization").click(function(){
	if ($("#show_utilization").is(':checked')){
		features.selectAll(".store-circle").style('visibility','hidden');
		features.selectAll(".util-circle").style('visibility','visible');
		$("#storelegend").width("100px");
		$("#storelegend").show();
	}
	else {
		features.selectAll(".util-circle").style('visibility','hidden');
		features.selectAll(".store-circle").style('visibility','visible');
		$("#storelegend").width("0px");
		$("#storelegend").hide();
	}
});

function clickStoreDialog(d) {
	d3.event.preventDefault();
	open_store_info_box('{{rootPath}}',{{modelId}},d.id,d.name,{{resultsId}});
}

function clickRouteDialog(d) { 
	d3.event.preventDefault();
	open_route_info_box('{{rootPath}}',{{modelId}},d.id,{{resultsId}});
}

function zoomToCollection(d) {
	
	var b = path.bounds(d),
	s =  s = .95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
    t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];
	console.log(b);

	svg.transition()
		.duration(750)
		.call(zoom.translate(t).scale(s).event);
}

function zoomed() { 
	  //console.log(d3.event.translate);
	  translate = d3.event.translate
	  scale = d3.event.scale
	  area = 1/scale/scale;
	  
	  features.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
	  features.selectAll(".land").style("stroke-width", 1.5 / d3.event.scale + "px");
	  features.selectAll(".state-border").style("stroke-width", 0.5 / d3.event.scale + "px");
	  features.selectAll(".country-border").style("stroke-width", 1.0 / d3.event.scale + "px");
	  features.selectAll(".road").style("stroke-width", function(d){ var sc = (.25 / d3.event.scale); if(sc < 0.010){return 0.025+"px"}else{ return sc + "px"}});
	  curr_scale = d3.event.scale;
}


//If the drag behavior prevents the default click,
//also stop propagation so we don’t click-to-zoom.
function stopped() {
if (d3.event.defaultPrevented) d3.event.stopPropagation();
}


d3.select(self.frameElement).style("height", height + "px");
</script>
