var ge;
var kmlObject;
var kmlString;
//var mainHref= getMainUrl() + '/static/visualization.10.kml';
//var kmlString = getKmlString();
//console.log($.getJSON('json/google-earth-kmlstring',{modelId:3,resultsId:1}));
google.load("earth","1",{"other_params":"sensor=false"});

function init() {
	google.earth.createInstance('ge_map3d',initCB,failureCB);
}

function initCB(instance) {

	ge = instance;
	ge.getWindow().setVisibility(true);
	
	//Enable the border layer
	ge.getLayerRoot().enableLayerById(ge.LAYER_BORDERS, true);
	// #Fix to ensure that the plugin comes back up if something is popped up in front
	getKMLString(ge);
	google.earth.addEventListener(ge.getWindow(), 'mousedown', function() {
		refreshAllIframeShims();
	});

	$("#ge_show_population").click(function() {
		if ($("#ge_content-for-iframe").is(':ui-dialog')) {
			if ($("#ge_content-for-iframe").dialog("isOpen") == true) {
				$('#ge_content-for-iframe').dialog('close');
			}
		}
		if ($("#ge_show_population").is(':checked')) {
			togglePlacemarks('pop', true);
		} else {
			togglePlacemarks('pop', false);
		}
	});

	$("#ge_show_vaccine").click(function() {
		if ($("#ge_content-for-iframe").is(':ui-dialog')) {
			if ($("#ge_content-for-iframe").dialog("isOpen") == true) {
				$('#ge_content-for-iframe').dialog('close');
			}
		}
		if ($("#ge_show_vaccine").is(':checked')) {
			togglePlacemarks('vac', true);
		} else {
			togglePlacemarks('vac', false);
		}
	});

	$("#ge_show_utilization").click(function() {
		if ($("#ge_content-for-iframe").is(':ui-dialog')) {
			if ($("#ge_content-for-iframe").dialog("isOpen") == true) {
				$('#ge_content-for-iframe').dialog('close');
			}
		}
		if ($("#ge_show_utilization").is(':checked')) {
			togglePlacemarks('uti', true);
		} else {
			togglePlacemarks('uti', false);
		}
	});

	$("#ge_show_routes").click(function() {
		if ($("#ge_content-for-iframe").is(':ui-dialog')) {
			if ($("#ge_content-for-iframe").dialog("isOpen") == true) {
				$('#ge_content-for-iframe').dialog('close');
			}
		}
		if ($("#ge_show_routes").is(':checked')) {
			togglePlacemarks('rou', true);
		} else {
			togglePlacemarks('rou', false);
		}
	});


	// set up the event listener to bypass balloon popups

	google.earth.addEventListener(ge.getWindow(), 'click', function(event) {
		var plotData = [[0.0, 0.0]];
		var genInfoData = [];
		var deviceData = [];
		var utilData = [];
		var vehicleData = [];
		var allVacAvalData = [];
		var vaccAvailPlotData = [];
		var popInfoData = [];
		var routeInfoData = [];
		var routeUtilInfoData = [];
		var tripManifestInfo = [];

		if (event.getTarget().getType() == 'KmlPlacemark') {
			// Make sure the dialog box closes if there is one already open.
			if ($("#ge_content-for-iframe").is(':ui-dialog')) {
				$("#ge_content-for-iframe").dialog('close');
			}
			var placemark = event.getTarget();
			event.preventDefault();
			//prevent the bubble from coming up
			var content = placemark.getBalloonHtmlUnsafe();
			var _in = document.getElementById('ge_content');
			//Get DIV to display results (see google_earth_demo.tpl
			_in.innerHTML = content;
			// Set content DIV's html
			var title = _in.getElementsByTagName('h3')[0];

			console.log("title: " + title.innerHTML);
			title.remove();

			var codes = _in.getElementsByTagName('script');
			// anything in scripts won't run if put in innerHTML
			for (var i = 0; i < codes.length; i++) {
				eval(codes[i].text);
				//Run a loop to evaluate all script language in description
			}
			// jQuery Dialog box for data

			$('#ge_content-for-iframe').dialog({
				bgiframe : true,
				width : 'auto',
				height : 'auto',
				title : title.innerHTML.replace('&gt;','>') ,
				open : function() {
					// See function below, sets up the jqGrid table
					if (placemark.getId().substr(0, 4) == "util") {
						createStorageInfoDialog(genInfoData, utilData, deviceData, vehicleData, plotData);
					} else if (placemark.getId().substr(0, 3) == "vac") {
						createVaccineInfoDialog(genInfoData, allVacAvalData, vaccAvailPlotData);
					} else if (placemark.getId().substr(0, 3) == "pop") {
						createPopulationInfoDialog(genInfoData, popInfoData);
					} else if (placemark.getId().substr(0, 3) == "rou") {
						createRouteInfoDialog(routeInfoData, routeUtilInfoData, tripManifestInfo);
					}

					// This part setups the iFrame Shim so this stuff works in Chrome
					// there is an iframe in the tpl file that is a child of body
					// Here, based on the dialog setup, we where this thing should be.
					var diParent = $(this).parent();
					var offset = diParent.offset();
					$("#content-iframe").css("border", 0 + "px");
					$("#content-iframe").css("left", offset.left + "px");
					$("#content-iframe").css("top", offset.top + "px");
					$("#content-iframe").css("width", diParent.outerWidth() + "px");
					$("#content-iframe").css("height", diParent.outerHeight() + "px");
					$("#content-iframe").css("visibility", "visible");
				},
				drag : function() {
					// Move the iFrame Shim with the dialog box.  I cannot believe this shit works.
					var diParent = $(this).parent();
					var offset = diParent.offset();
					$("#content-iframe").css("border", 0 + "px");
					$("#content-iframe").css("left", offset.left + "px");
					$("#content-iframe").css("top", offset.top + "px");
					$("#content-iframe").css("width", diParent.outerWidth() + "px");
					$("#content-iframe").css("height", diParent.outerHeight() + "px");
				},
				resize : function() {
					//Resize the iFrame Shim with the dialog box.
					var diParent = $(this).parent();
					var offset = diParent.offset();
					$("#content-iframe").css("border", 0 + "px");
					$("#content-iframe").css("left", offset.left + "px");
					$("#content-iframe").css("top", offset.top + "px");
					$("#content-iframe").css("width", diParent.outerWidth() + "px");
					$("#content-iframe").css("height", diParent.outerHeight() + "px");
				},
				resizeStop : function() {
					var diParent = $(this).parent();
					var offset = diParent.offset();
					$("#content-iframe").css("border", 0 + "px");
					$("#content-iframe").css("left", offset.left + "px");
					$("#content-iframe").css("top", offset.top + "px");
					$("#content-iframe").css("width", diParent.outerWidth() + "px");
					$("#content-iframe").css("height", diParent.outerHeight() + "px");
				},
				close : function() {
					$('#ge_content').tabs();
					// For some reason, if you don't create them first, they aren't there from before, stupid javascript
					$('#ge_content').tabs('destroy');
					$('#ge_content').innerHtml = "";
					$('#content-iframe').css('visibility', 'hidden');
				},
			});

			$('#ge_content').click(function() {
				var diParent = $("#ge_content-for-iframe").parent();
				var offset = diParent.offset();
				$("#content-iframe").css("border", 0 + "px");
				$("#content-iframe").css("left", offset.left + "px");
				$("#content-iframe").css("top", offset.top + "px");
				$("#content-iframe").css("width", diParent.outerWidth() + "px");
				$("#content-iframe").css("height", diParent.outerHeight() + "px");
			});
			$('#ge_content').css('visibility', 'visible');
		}
	});
};

function failureCB(errorCode){
//STB put something here!!!
};

function parseKmlWrapper(ge,kmlString){
	kmlObj = ge.parseKml(kmlString);
	kmlFinishedLoading(kmlObj);
}  
     
function togglePlacemarks(type, cond) {
	var placemarks = kmlObject.getElementsByType('KMLPlacemark');
	for (var i = 0; i < placemarks.getLength(); ++i) {
		var placemark = placemarks.item(i);
		if (placemark.getId().substr(0, 3) == type) {
			placemark.setVisibility(cond);
		}
	}
};

function kmlFinishedLoading(obj) {
	kmlObject = obj;
	if (kmlObject) {
		coordinates = new Array();
		//Array to hold all of the coordinates to compute the flyTo
		ge.getFeatures().appendChild(kmlObject);
		// As we are creating the KML elements, attach a click event handler to each to handle bringing up information
		var placemarks = kmlObject.getElementsByType('KMLPlacemark');
		for (var i = 0; i < placemarks.getLength(); ++i) {
			var placemark = placemarks.item(i);
			if(placemark.getId().substr(0,3) != 'rou'){
				coordinates.push(getPlacemarkLatLonCentroid(placemark));
			}
		}

		var centroidForKML = computeCentroid(coordinates);
		//compute centroid of all points on the map
		var lookAt = ge.createLookAt('');
		// move to the viz
		lookAt.setLatitude(centroidForKML[0]);
		lookAt.setLongitude(centroidForKML[1]);
		lookAt.setRange(500000.0);
		// need to figure out how to get this to be calculated
		ge.getView().setAbstractView(lookAt);

		if ($("#ge_show_population").is(':checked')) {
			togglePlacemarks('pop', true);
		}
		if ($("#ge_show_vaccine").is(':checked')) {
			togglePlacemarks('vac', true);
		}
		if ($("#ge_show_utilization").is(':checked')) {
			togglePlacemarks('uti', true);
		}
		if ($("#ge_show_route").is(':checked')) {
			togglePlacemarks('rou', true);
		}
	}
};

// Function that computes the centroid of a visualization using COM calc
function computeCentroid(coorArray) {
	var centroid = [0.0, 0.0];
	for (var i = 0; i < coorArray.length; ++i) {
		var coordinate = coorArray[i];
		centroid[0] += coordinate[0];
		centroid[1] += coordinate[1];
	}
	centroid[0] = centroid[0] / coorArray.length;
	centroid[1] = centroid[1] / coorArray.length;
	return centroid;
};

// Function that returns the latlon of the centroid of a placemark.
function getPlacemarkLatLonCentroid(placemark) {	
	if (placemark.getType() != 'KmlPlacemark') {
		console.log("getPlacemarkLatLonCentroid: can't compute centroid of anything other than KMLPlacemark");
		return [0.0, 0.0];
	}
	var geometry = placemark.getGeometry();
	var type = geometry.getType();
	var coordinates = new Array();
	switch(type) {
		case 'KmlPoint':
			coordinates.push(geometry.getLatitude());
			coordinates.push(geometry.getLongitude());
			break;
		case 'KmlPolygon':
			var PolyCoordinates = geometry.getOuterBoundary().getCoordinates();
			var coordArray = new Array();
			for (var i = 0; i < PolyCoordinates.getLength(); ++i) {
				coordArray[i] = new Array(2);
				coordArray[i][0] = PolyCoordinates.get(i).getLatitude();
				coordArray[i][1] = PolyCoordinates.get(i).getLongitude();
			}
			coordinates = computeCentroid(coordArray);
			break;
		default:
			console.log("Not a supported KML Geometry");
			coordinates.push(0.0);
			coordinates.push(0.0);
	}
	return coordinates;
};

function createRouteInfoDialog(routeInfoData,routeUtilInfoData,tripManifestInfo){
	$("#ge_content").tabs();
	$("#RouteInfo").jqGrid({
		data : routeInfoData,
		datatype : "local",
		height : 'auto',
		width : 300,
		scroll : false,
		scollOffset : 0,
		colNames : ['Feature', 'Value'],
		colModel : [{
			name : 'feature',
			id : 'feature',
			width : '30%',
			sortable : false
		}, {
			name : 'value',
			id : 'value',
			width : '70%',
			sortable : false
		}],
		caption : 'Route Information'
	}); 

	
	 // Hides the column headings
  	$("#RouteInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();
  		
	$("#RouteUtil").jqGrid({
		data : routeUtilInfoData,
		datatype : "local",
		height : 'auto',
		width : 400,
		scroll : false,
		scollOffset : 0,
		colNames : ['Name', 'Net Volume (L)', 'Maximum Utilization Percent', 'Number Of Trips'],
		colModel : [{
			name : 'name',
			id : 'name',
			width : 150
		}, {
			name : 'storage',
			id : 'storage',
			width : 100,
			align : 'right',
			formatter : "number",
			formatoptions : {  
				decimalPlaces : 2
			}
		}, {
			name : 'util',
			id : 'util',
			width : 100,
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}, {
			name : 'trips',
			id : 'trips',
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 0
			}
		}],
		caption : 'Vehicles'
	}); 
	
	$("#RouteMan").jqGrid({
		data : tripManifestInfo,
		datatype : "local",
		height : 'auto',
		width : 500,
		scroll : false,
		scollOffset : 0,
		colNames : ['Segment', 'Start', 'End', 'Volume Carried (L)'],
		colModel : [{
			name : 'segment',
			id : 'segment',
			width : 200,
			sortable : false
		}, {
			name : 'start',
			id : 'start',
			width : 100,
			sortable : false
		}, {
			name : 'end',
			id : 'end',
			width : 100,
			sortable : false
		}, {
			name : 'vol',
			id : 'vol',
			sortable : false,
			formatter : "number",
			formatoptions : {
				decimalPlaces : 0
			}
		}],
		caption : 'Trips'
	}); 
};

function createPopulationInfoDialog(genInfoData, popInfoData) {
	$("#ge_content").tabs();
	$("#GenInfo").jqGrid({
		data : genInfoData,
		datatype : "local",
		height : 'auto',
		width : 300,
		scroll : false,
		scrollOffset : 0,
		colNames : ['Feature', 'Value'],
		colModel : [{
			name : 'feature',
			id : 'feature',
			width : '30%',
			sortable : false
		}, {
			name : 'value',
			id : 'value',
			width : '70%',
			sortable : false
		}],
		caption : 'General Information'
	});

	// Hides the column headings
	$("#GenInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();

	$("#Population").jqGrid({
		data : popInfoData,
		datatype : "local",
		height : 'auto',
		width : 300,
		scroll : false,
		scrollOffset : 0,
		colNames : ['Category', 'Count'],
		colModel : [{
			name : 'class',
			id : 'class',
			width : 200
		}, {
			name : 'count',
			id : 'count',
			align : 'right'
		}],
		caption : 'Population Information'
	});
};

function createVaccineInfoDialog(genInfoData, allVacAvalData, vaccAvailPlotData) {
	$("#ge_content").tabs();
	$("#GenInfo").jqGrid({
		data : genInfoData,
		datatype : "local",
		height : 'auto',
		width : 300,
		scroll : false,
		scrollOffset : 0,
		colNames : ['Feature', 'Value'],
		colModel : [{
			name : 'feature',
			id : 'feature',
			width : '30%',
			sortable : false
		}, {
			name : 'value',
			id : 'value',
			width : '70%',
			sortable : false
		}],
		caption : 'General Information'
	});

	// Hides the column headings
	$("#GenInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();

	$("#Availability").jqGrid({
		data : allVacAvalData,
		datatype : 'local',
		height : 'auto',
		width : 500,
		scroll : false,
		scrollOffset : 0,
		colNames : ['Vaccine', 'Doses Demanded', 'Doses Administered', 'Availability'],
		colModel : [{
			name : 'name',
			id : 'name',
			width : 100
		}, {
			name : 'patients',
			id : 'patients',
			align : 'right',
			width : 100
		}, {
			name : 'treated',
			id : 'treated',
			align : 'right',
			width : 100
		}, {
			name : 'avail',
			id : 'avail',
			align : 'right'
		}],
		caption : 'Vaccine Availabilities'
	});

	createVaccineAvailPlot("AvailPlot", vaccAvailPlotData);
};

function createStorageInfoDialog(genInfoData, utilData, deviceData, vehicleData, plotData) {
	$("#ge_content").tabs();
	$("#GenInfo").jqGrid({
		data : genInfoData,
		datatype : "local",
		height : 'auto',
		width : 300,
		scroll : false,
		scrollOffset : 0,
		colNames : ['Feature', 'Value'],
		colModel : [{
			name : 'feature',
			id : 'feature',
			width : '30%',
			sortable : false
		}, {
			name : 'value',
			id : 'value',
			width : '70%',
			sortable : false
		}],
		caption : 'General Information'
	});

	// Hides the column headings
	$("#GenInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();

	$("#Utilization").jqGrid({
		data : utilData,
		datatype : 'local',
		height : 'auto',
		width : 500,
		scroll : false,
		scrollOffset : 0,
		colNames : ['Information', 'Placemark', 'Category', 'Data'],
		colModel : [{
			name : 'info',
			id : 'info',
			sortable : false,
			hidden : true,
			width : 0
		}, {
			name : 'placemark',
			id : 'placemark',
			width : 50
		}, {
			name : 'category',
			id : 'category',
			sortable : false
		}, {
			name : 'value',
			id : 'value',
			sortable : false,
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}],
		grouping : true,
		groupingView : {
			groupField : ['info'],
			groupColumnShow : false,
			groupOrder : ['desc'],
		},
		caption : 'Utilization Statistics'
	});

	$("#Utilization").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();

	$("#Device").jqGrid({
		data : deviceData,
		datatype : 'local',
		height : 'auto',
		width : 'auto',
		scroll : false,
		scrollOffset : 0,
		colNames : ['Name', 'Count', '2-8C<br>Net Storage (L)', 'Below 2C<br>Net Storage (L)'],
		colModel : [{
			name : 'name',
			id : 'name',
			width : 200
		}, {
			name : 'count',
			id : 'count',
			align : 'right',
			width : 60,
			sortable : false
		}, {
			name : 'fridge',
			id : 'fridge',
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}, {
			name : 'freezer',
			id : 'freezer',
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}],
		caption : 'Storage Devices'
	});

	$("#Vehicles").jqGrid({
		data : vehicleData,
		datatype : 'local',
		height : 'auto',
		width : 'auto',
		scroll : false,
		scrollOffset : 0,
		colNames : ['Name', 'Count', '2-8C<br>Net Storage (L)', 'Below 2C<br>Net Storage (L)'],
		colModel : [{
			name : 'name',
			id : 'name',
			width : 200
		}, {
			name : 'count',
			id : 'count',
			align : 'right',
			width : 60,
			sortable : false
		}, {
			name : 'fridge',
			id : 'fridge',
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}, {
			name : 'freezer',
			id : 'freezer',
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}],
		caption : 'Vehicle Information'
	});
	
	createVialsPlot("VialsPlot", plotData);
};


function createVialsPlot(divName, plotData) {
	// Find maximum value??
	$('#' + divName).highcharts({
		chart : {
			type : 'line',
			height : 200,
			width : 500
		},
		title : {
			text : null
		},
		legend : {
			enabled : false
		},
		plotOptions : {
			series : {
				marker : {
					enabled : false
				}
			}
		},
		xAxis : {
			title : {
				text : 'Days'
			}
		},
		yAxis : {
			title : {
				text : 'Vials'
			},
			min : 0,
			endOnTick : false
		},
		credits : {
			enabled : false
		},
		series : [{
			data : plotData
		}]
	});
};



function createVaccineAvailPlot(divName, vaccAvailPlotData) {
	$('#' + divName).highcharts({
		chart : {
			type : 'bar',
			height : 200,
			width : 500
		},
		title : {
			text : 'Availabilty by Vaccine'
		},
		legend : {
			enabled : false
		},
		xAxis : {
			categories : vaccAvailPlotData['categories'],
			title : {
				text : 'Vaccines'
			}
		},
		yAxis : {
			min : 0,
			max : 100,
			title : {
				text : 'Percent Availability'
			}
		},
		plotOptions : {
			bar : {
				dataLabels : {
					enabled : true
				}
			}
		},
		credits : {
			enabled : false
		},
		series : [{
			data : vaccAvailPlotData["data"]
		}]
	});
};

// Make the visualization baby!!
google.setOnLoadCallback(init);