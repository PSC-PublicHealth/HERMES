%rebase outer_wrapper title_slogan=_("GeoJson Test"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultId=resultsId

<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/d3/topojson.v1.min.js"></script>
<script src="{{rootPath}}static/queue.min.js"></script>
<script src="{{rootPath}}static/hermes_info_dialogs.js"></script>
<script src="{{rootPath}}static/rainbowvis.js"></script>

<div id="model_store_info_dialog" title="This should get replaced">
<div id = "model_store_info_content">
	<ul>
		<li style="font-size:small">
			<a href='#tab-1'>General Info</a>
		</li>
		<li style="font-size:small">
			<a href='#tab-2'>Population Info</a>
		</li>
		<li style="font-size:small">
			<a href="#tab-3">Storage Devices</a>
		</li>
	</ul>
	<div id='tab-1'><table id='GenInfo'></table></div>
	<div id='tab-2'><table id='PopInfo'></table></div>
	<div id='tab-3'><table id='StoreDevInfo'></table></div>
</div>
</div>

<div class="map-container"></div>

<style>

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
	  fill: #fff;
	  fill-opacity: 0.30;
	  font-size: 1px;
	  font-weight: bold;
	  text-anchor: middle;
	  visibility: hidden;
	  pointer-events:none;
	}

.state-label {
	  fill: #FFF;
	  fill-opacity: .50;
	  font-size: .2px;
	  font-weight: 300;
	  text-anchor: middle;
	  visibility: hidden;
	  pointer-events:none;
	}

.pp-label {
	  fill: #000;
	  fill-opacity: 1.0;
	  font-size: 0.15px;
	  font-weight: 300;
	  text-anchor: right;
	  visibility: hidden;
	  pointer-events:none;
	}
.store-circle {
	fill: red;
	fill-opacity:.50;
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

var rainbow = new Rainbow();
rainbow.setSpectrum('blue','red');

var curr_scale = 1.0;

$(function() {
	initStoreInfoDialogNoResults("model_store_info_dialog");
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
	
var projection = d3.geo.mercator()
	.scale(width / 2 / Math.PI)
	.translate([width / 2, height / 2])
	.clipAngle(180)
	//.translate([0,0])
	.precision(1);

//var projection = d3.geo.orthographic()
//	.scale(width / 2.1)
//	.rotate([0,0])
//	.translate([width / 2, height / 2])
//	.precision(.5)
//	.clipAngle(90);

var zoom = d3.behavior.zoom()
	//.translate()
	//.scale(curr_scale)
	.on("zoom", zoomed);

var path = d3.geo.path()
	.projection(projection);

var svg = d3.select(".map-container").append("svg")
	.attr("width", width)
	.attr("height", height);
	//.on("click",stopped,true);

svg.append("rect")
	.attr("class","overlay")
	.attr("width",width)
	.attr("height",height)
	.call(zoom);
	//.on("zoom",zoom);
	//.on("click",reset);



var velocity = 0.01;
var then = Date.now();

var features = svg.append("g")
	//.call(zoom);

queue()
	.defer(d3.json,"{{rootPath}}static/world.10m.states.json")
	.defer(d3.json,"{{rootPath}}static/world.50m.countries.json")
	.defer(d3.json,"{{rootPath}}static/world.10m.pp.json")
	.defer(d3.json,"{{rootPath}}json/storeutilizationlocations?modelId={{modelId}}&resultsId={{resultsId}}")
	.await(ready);

function ready(error, stateJSON, countryJSON, ppJSON, storeJSON){
	$('#ajax_busy_image').hide();
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
				return "translate(" + projection(coordinates) + ")"; })
				.attr("dy",".35em")
				.attr("dx",".55em")
			.text(function(d) {console.log(d.properties.name); return d.properties.name;});

	features.append("path")
		.datum(topojson.mesh(stateJSON,states, function(a,b){return a!==b;}))
		.attr("class","state-border")
		.attr("d",path);
	
	features.append("path")
		.datum(topojson.mesh(countryJSON,countries,function(a,b){return a!==b;}))
		.attr("class","country-border")
		.attr("d",path);
	
	features
	.selectAll("circle")
		.data(topojson.feature(ppJSON,ppJSON.objects.populated_places).features)
	.enter()
		.append("circle")
			.attr("cx",function(d){
				var coordinates = [d.properties.lon,d.properties.lat]
				console.log(projection(coordinates));
				console.log(coordinates);
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
			.style("stroke-width",0.025+"px")
			.on("click",clickDialog);
					
	zoomToCollection(storeJSON.geoFC);
	
	
}

function clickDialog(d) {
	d3.event.preventDefault();
	if ($("#model_store_info_dialog").is(':ui-dialog')) {
		$("#model_store_info_dialog").dialog('close');
	}
	populateStoreInfoDialogNoResults("{{rootPath}}","model_store_info_content","{{modelId}}",d.id);
	$("#model_store_info_dialog").dialog("option","title","Information for Location " + d.name);
	$("#model_store_info_dialog").dialog("open");
}


function zoomToCollection(d) {
	var b = path.bounds(d),
	s =  s = .95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
    t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];

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
	  console.log(d3.event.translate);
	  features.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
	  features.select(".land").style("stroke-width", 1.5 / d3.event.scale + "px");
	  features.select(".state-border").style("stroke-width", .25 / d3.event.scale + "px");
	  features.select(".country-border").style("stroke-width", 1.0 / d3.event.scale + "px");
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
		  console.log("SHOULD");
		  features.selectAll(".pp-label").style("visibility","visible");
	  }
	  else{
		  console.log("HIDE");
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
