/*
*/
;(function($){
	var vizJson = {'levels':[],'allOn':true,'popOn':false,'utilOn':false,'vacOn':false,'routeUtilOn':false};
	
	$.widget("geographic-map.geographicResultsMap",{
		options:{
			rootPath:'',
			modelId:'',
			levelList:["Level1","Level2","Level3","Level4"],
			resultsId:null,
			width:1000,
			height:600,
			maxpop:null,
			trant:{
				title:"Geo Coordinate Editor"
			}
		},
		
		_create:function(){
			trant = this.options.trant;
			this.containerID = $(this.element).attr('id');
			var thiscontainerID = this.containerID;
			
			
			var thisoptions = this.options;
			var rootPath = this.options.rootPath;
			
			if(rootPath == ''){
				alert('Cannot use geographicResultsMap without a rootPath');
				return;
			}
			
			var modelId = this.options.modelId;
			if(modelId == ''){
				alert('Cannot use geographicResultsMap without a modelId');
			}
			
			var resultsId = this.options.resultsId;
			if(resultsId == ''){
				alert('Cannot use geographicResultsMap without a resultsId');
			}
			var levelList = this.options.levelList
			
			// Create all of the pertinent containers
			var mapContainerID = thiscontainerID + "_map-container";
			var layersLegendID = thiscontainerID + "_layers-container";
			var legendContainerID = thiscontainerID + "_legend-container";
			var popLegendID = thiscontainerID + "_poplegend";
			var vaLegendID = thiscontainerID + "_valegend";
			var storeLegendID = thiscontainerID + "_storelegend";
			var transLegendID = thiscontainerID + "_"+storeLegendID;
			
			
			$("#"+thiscontainerID).append("<div id='" + mapContainerID + "' class='geoContainer'></div>");
			$("#"+thiscontainerID).append("<div id='" + layersLegendID + "' class='geoLayerLeg'></div>");
			$("#"+thiscontainerID).append("<div id='" + legendContainerID) + "class='geoLegend'></div>";
			
		
			
			var rainbow = new Rainbow();
			rainbow.setSpectrum('blue','red');
			// var routeRain = new Rainbow();
			// routeRain.setSpectrum('white','black');
			// routeColors =
			// ["black","red","blue","orange","green","purple","white","gold","aqua","maroon"];

			var levelColors = ["silver","gold","orange","pink","white","black","green"];
			var provinceColors = {"01":"black","02":"red","03":"orange","04":"yellow","05":"green",
								  "06":"blue","07":"indigo","08":"violet","09":"maroon","10":"gold",
								  "11":"brown","12":"darkgrey"};
								 

			$("#"+mapContainerID).parent().height($(window).height()-250);
			$("#"+mapContainerID).height($("#"+mapContainerID).parent().height());
			$("#"+mapContainerID).parent().width($("#"+mapContainerID).parent().parent().width());
			$("#"+mapContainerID).width($("#"+mapContainerID).parent().width()-10);
			var width = $("#"+mapContainerID).width()-10;
			var height = $("#"+mapContainerID).height();
			
			$(function() {
				$('#ajax_busy_image').show();
				
			});
			
			function showLegend(whichLegend){
				$("#legendContainer").html("");
				$("#legendContainer").html("<img src='" + rootPath + "static/images/" + whichLegend+".png' width=170>");
			}
			function removeLegend(){
				$("#legendContainer").html("");
			}
			
			function showRouteLegend(){
				$("#routeLegendContainer").html("");
				$("#routeLegendContainer").html("<img src='" + rootPath + "static/images/util.png' width=170>");
			}
			
			function removeRouteLegend(){
				$("#routeLegendContainer").html("");
			}
			function doneLoading(){
				$('#ajax_busy_image').hide();
				
			
			}
			
			//$("#legendContainer").html("<img src='" + rootPath + "static/images/popserved.png' width=100>");
			//$("#legendContainer").html("");
			var projection = d3.geo.mercator()
			.clipAngle(90)
			.scale(width / 2 / Math.PI)
			.translate([width / 2, height / 2]);
		
			var path = d3.geo.path()
				.projection(projection)
				.pointRadius(0.025);
	
			var zoom = d3.behavior.zoom()
				.translate([0,0])
				.scale(1)
				.on("zoom", zoomed);
				
			var svg = d3.select(".geoContainer").append("svg")
				.attr("width", $("#"+mapContainerID).width()-10)
				.attr("height", $("#"+mapContainerID).height())
				.attr("overflow","hidden")
				//.call(zoom);
			
			console.log("Width = "+width+ " Height = "+height);
			
			svg.append("rect")
			.attr("class","overlay")
			.attr("width",svg.style("width"))
			.attr("height",svg.style("height"))
			.call(zoom);
			//var width = svg.style("width");
			//var height = svg.style("height");
			
			var features = svg.append("g");
	
			var storeTipDiv = d3.select("body")
				.append("div")
				.attr("class","tooltip")
				.style("opacity",0);
			
			var phrases = {
					0:'Stores',
					1:'Show/Hide Levels',
					2:'All Levels',
					3:'Show Indicators',
					4:'Population',
					5:'Utilization',
					6:'Vaccines',
					7:'Routes',
					8:'Color By Route',
					9:'Color By Utilization'
				}
			translate_phrases(phrases)
				.done(function(results){
					var tphrases = results.translated_phrases;
					$("#"+layersLegendID).append(createLayerTableHtmlString(levelList,tphrases));
					
				queue()
				.defer(d3.json,rootPath+"static/world.10m.states.json")
				.defer(d3.json,rootPath+"static/world.50m.countries.json")
				.defer(d3.json,rootPath+"static/world.10m.pp.json")
				.defer(d3.json,rootPath+"static/world.roads.json")
				.defer(d3.json,rootPath+"json/storeresultslocations?modelId="+modelId+"&resultsId="+resultsId)
				.defer(d3.json,rootPath+"json/routeresultslines?modelId="+modelId+"&resultsId="+resultsId)
				.await(ready);
				
				var zoomIn = $("#zoomIn").button();
				zoomIn.click(function(){
					zoomByFactor(1.2);
				});
				var zoomOut = $("#zoomOut").button();
				zoomOut.click(function(){
					zoomByFactor(0.8);
				});
				// Fix this bullshit	
				$(document).on('keydown', 'body', function(event) { 
				    if ((event.keyCode == 109)||(event.keyCode == 173 && event.shiftKey == false)) {
				        // numpad minus OR numrow minus pressed
				        zoomByFactor(0.8);
				    } else if ((event.keyCode == 107)||(event.keyCode == 61 && event.shiftKey == true)) {
				        // numpad plus OR numrow plus pressed
				        zoomByFactor(1.2);
				    }
				});
	
				/*
				 * factor == 1 to center, factor > 1 to zoom in, factor < 1 to
				 * zoom out
				 */
				function zoomByFactor(factor) {
				    var scale = zoom.scale();
				    var newScale = scale * factor;
				    var t = zoom.translate();
				    var c = [width / 2, height / 2];
				    console.log("C = "+c);
				    zoom
				        .scale(newScale)
				        .translate(
				            [c[0] + (t[0] - c[0]) / scale * newScale, 
				            c[1] + (t[1] - c[1]) / scale * newScale])
				    .event(svg.transition().duration(350));
				}
	
				var in_count = 0;
			
				function ready(error, stateJSON, countryJSON, ppJSON, roadsJSON, storeJSON,routesJSON){
					drawMap(stateJSON, countryJSON, ppJSON, roadsJSON, storeJSON,routesJSON,height,width);
					console.log(vizJson);			
					// RESIZE MAP IF WINDOW RESIZES	
					$(window).resize(function(){
						d3.select(".geoContainer").select("svg").remove();
						$("#"+mapContainerID).parent().height($(window).height()-250);
						$("#"+mapContainerID).height($("#"+mapContainerID).parent().height());
						$("#"+mapContainerID).parent().width($("#"+mapContainerID).parent().parent().width());
						$("#"+mapContainerID).width($("#"+mapContainerID).parent().width()-10);
						width = $("#"+mapContainerID).width()-10;
						height = $("#"+mapContainerID).height();
						
						// recreate all the visulization (move to function)
						
						projection = d3.geo.mercator()
						.clipAngle(90)
						.scale(width / 2 / Math.PI)
						.translate([width / 2, height / 2]);
						
						path = d3.geo.path()
						.projection(projection)
						.pointRadius(0.025);
						
						zoom = d3.behavior.zoom()
						.translate([0,0])
						.scale(1)
						.on("zoom", zoomed);
						
						svg = d3.select(".geoContainer").append("svg")
							.attr("width", $("#"+mapContainerID).width()-10)
							.attr("height", $("#"+mapContainerID).height())
							.attr("overflow","hidden")
						
						svg.append("rect")
							.attr("class","overlay")
							.attr("width",svg.style("width"))
							.attr("height",svg.style("height"))
							.call(zoom);
						
						features = svg.append("g");
						drawMap(stateJSON, countryJSON, ppJSON, roadsJSON, storeJSON,routesJSON,height,width);
						zoomToCollection(storeJSON.geoFC);
						restoreFromVizJson(vizJson);
						
					});
				}
				
				//$("#legendContainer").html("<img src='" + rootPath + "static/images/popserved.png' width=180>")
				$("#show_all_levels").change(function(){
					$("[id^=show_level_]").prop("checked",false);
					if($(this).is(':checked')){
						showAllStores();
						vizJson.allOn = true;
						vizJson.levels = [];
					}
					else{
						hideAllStores();
						vizJson.allOn = false;
					}
					console.log(vizJson);
				});

				$("[id^=show_level_]").change(function(){
					var thisLevNum = parseInt($(this).prop('id').match(/\d+/));
					if($('#show_all_levels').is(':checked')){
						$("#show_all_levels").prop("checked",false);
						hideAllStores();
					}
					if(!$(this).is(":checked")){
						hideStoresForLevel(thisLevNum);
						var index = vizJson.levels.indexOf(thisLevNum);
						if(index > -1){
							vizJson.levels.split(index,1);
						}
						
					}
					else{
						showStoresForLevel(thisLevNum);
						var index = vizJson.levels.indexOf(thisLevNum);
						if(index == -1){
							vizJson.levels.push(thisLevNum);
						}
						vizJson.allOn = false;
						//vizJson.levels = thisLevNum;
					}
					console.log(vizJson);
				});

				$("#show_population").click(function(){
					if ($("#show_population").is(':checked')){
						if($("#show_vaccine").is(':checked')){
							$("#show_vaccine").click();
						}
						if($("#show_utilization").is(':checked')){
							$("#show_utilization").click();
						}
						features.selectAll(".store-circle").style('visibility','hidden');
						features.selectAll(".pop-circle").style('visibility','visible');
						showLegend("popserved");
						vizJson.popOn = true;
					}
					else {
						features.selectAll(".pop-circle").style('visibility','hidden');
						features.selectAll(".store-circle").style('visibility','visible');
						removeLegend();
						vizJson.popOn = false;
					}
					if (!$("#show_all_levels").is(":checked")){
						$("#show_all_levels").click();
					}
					showAllStores();
					console.log(vizJson);
				});
				
				$("#show_routes_util").click(function(){
					if ($("#show_routes_util").is(':checked')){
						features.selectAll(".route-util-line").style('visibility','visible');
						features.selectAll(".route-line").style('visibility','hidden');
						showRouteLegend();
						vizJson.routeUtilOn = true;
					}
					else {
						features.selectAll(".route-util-line").style('visibility','hidden');
						features.selectAll(".route-line").style('visibility','visible');
						removeRouteLegend();
						vizJson.routeUtilOn = false;
					}
					console.log(vizJson);
				});


				$("#show_vaccine").click(function(){
					if ($("#show_vaccine").is(':checked')){
						if($("#show_utilization").is(':checked')){
							$("#show_utilization").click();
						}
						if($("#show_population").is(':checked')){
							$("#show_population").click();
						}
						features.selectAll(".store-circle").style('visibility','hidden');
						features.selectAll(".va-circle").style('visibility','visible');
						showLegend("vaccAvail");
						vizJson.vacOn = true;
					}
					else {
						features.selectAll(".va-circle").style('visibility','hidden');
						features.selectAll(".store-circle").style('visibility','visible');
						removeLegend();
						vizJson.vacOn = false;
					}
					if (!$("#show_all_levels").is(":checked")){
						$("#show_all_levels").click();
					}
					showAllStores();
					console.log(vizJson);
				});
				$("#show_utilization").click(function(){
					if ($("#show_utilization").is(':checked')){
						if($("#show_vaccine").is(':checked')){
							$("#show_vaccine").click();
						}
						if($("#show_population").is(':checked')){
							$("#show_population").click();
						}
						features.selectAll(".store-circle").style('visibility','hidden');
						features.selectAll(".util-circle").style('visibility','visible');
						showLegend("util");
						vizJson.utilOn = true;
					}
					else {
						features.selectAll(".util-circle").style('visibility','hidden');
						features.selectAll(".store-circle").style('visibility','visible');
						removeLegend()
						vizJson.utilOn = false;
					}
					if (!$("#show_all_levels").is(":checked")){
						$("#show_all_levels").click();
					}
					showAllStores();
					console.log(vizJson);
				});

				$( document ).on("doneStore",function(event, divId, storeId){
					$("#"+divId+"_dialog").on("dialogclose",function(){
						if(selectedStore.indexOf(storeId)>-1){
							selectedStore.splice(selectedStore.indexOf(storeId),1);
							if((selectedRoute.length == 0) && (selectedStore.length == 0)){
								restoreEverything();
							}
							else{
								highlightStores(selectedStore);
								highlightRoutes(selectedRoute);
							}
						}
					});
				});

				$( document ).on("doneRoute",function(event, divId, routeId){
					$("#"+divId+"_dialog").on("dialogclose",function(){
						if(selectedRoute.indexOf(routeId)>-1){
							selectedRoute.splice(selectedStore.indexOf(routeId),1);
							if((selectedRoute.length == 0) && (selectedStore.length == 0)){
								restoreEverything();
							}
							else{
								highlightStores(selectedStore);
								highlightRoutes(selectedRoute);
							}
						}
					});
				});
			
		}); // Done Translate Phrases
			
			
			// / Helper Functions
			
			function getRandomColor() {
			    var letters = '0123456789ABCDEF'.split('');
			    var color = '#';
			    for (var i = 0; i < 6; i++ ) {
			        color += letters[Math.floor(Math.random() * 16)];
			    }
			    return color;
			}
			
			function clickStoreDialog(d) {
				d3.event.preventDefault();
				
				if(selectedStore.indexOf(d.id)>-1){
					console.log("already there");
				}
				else{
					selectedStore.push(d.id);
					highlightStores(selectedStore);
					open_store_info_box(rootPath,modelId,d.id,d.name,resultsId);
				}
			};

			function clickRouteDialog(d) { 
				d3.event.preventDefault();
				if(selectedRoute.indexOf(d.id)>-1){
					console.log("route already here");
				}
				else{
					selectedRoute.push(d.id);
					highlightRoutes(selectedRoute);
					open_route_info_box(rootPath,modelId,d.id,resultsId);
				}
			};

			
			function zoomToCollection(d) {
/*				for(var i=0;i<d.features.ngth;++i){
					if(d.features[i].geometry.coordinates[0] == 0.0){
						console.log(d)
					}
				}
				*/
				//	console.log(d[p].geometry.coordinates);
				//})
				
				console.log("HERE = "+width+" " + height);
				
				var b = path.bounds(d),
				s =  s = 0.95 / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
			    t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];

				svg.transition()
					.duration(750)
					.call(zoom.translate(t).scale(s).event);
			};

			function restoreFromVizJson(vizJson){
				/// first which level was on
				console.log(selectedStore);
				
				if(vizJson.popOn){
					features.selectAll(".store-circle").style('visibility','hidden');
					features.selectAll(".pop-circle").style('visibility','visible');
					showLegend("popserved");
					//$("#"+popLegendID).width("100px");
					//$("#"+popLegendID).show();
				}
				if(vizJson.vacOn){
					features.selectAll(".store-circle").style('visibility','hidden');
					features.selectAll(".va-circle").style('visibility','visible');
					showLegend("vaccAvail");
					//$("#"+vaLegendID).width("100px");
					//$("#"+vaLegendID).show();
				}
				if(vizJson.utilOn){
					features.selectAll(".store-circle").style('visibility','hidden');
					features.selectAll(".util-circle").style('visibility','visible');
					showLegend("util");
					//$("#"+storeLegendID).width("100px");
					//$("#"+storeLegendID).show();
				}
				if(vizJson.routeUtilOn){
					features.selectAll(".route-util-line").style('visibility','visible');
					features.selectAll(".route-line").style('visibility','hidden');
					showRouteLegend("");
					//$("#"+transLegendID).width("100px");
					//$("#"+transLegendID).show();
				}
				if(vizJson.allOn){
					showAllStores();
				}
				else{
					hideAllStores();
					for(var i=0;i<vizJson.levels.length;i++){
						showStoresForLevel(vizJson.levels[i]);
					}
				}
				if(selectedStore.length > 0){
					highlightStores(selectedStore);
				}
				if(selectedRoute.length > 0){
					highlightRoutes(selectedRoute);
				}
			};
			
			function highlightStores(ds){
				features.selectAll(".store-circle")
				.style('opacity',function(a){
					if (ds.indexOf(a.id)>-1){
						return 1.0;
					}
					else{
						return 0.2;
					}
				});
				features.selectAll(".route-line")
					.style('opacity',function(a){
						var ops = 1.0;
						for(var i = 0;i<ds.length; i++){
							d = ds[i];
							if(a.onIds.indexOf(d) > -1){
								ops = 1.0;
							}
						}
						return ops;
					})
					.style('stroke-width',function(a){
						var ops = 0.5/currentScale;
						for(var i = 0;i<ds.length; i++){
							d = ds[i];
							if(a.onIds.indexOf(d) > -1){
								ops = 1.5/currentScale;
							}
						}
						return ops + "px";
					})
					.style('stroke',function(a){
						var ops = "white";
						for(var i = 0;i<ds.length; i++){
							d = ds[i];
							if(a.onIds.indexOf(d) > -1){
								ops = "gold";
							}
						}
						return ops;
					});
					features.selectAll(".route-util-line")
						.style('opacity',function(a){
							var ops = 1.0;
							for(var i = 0;i<ds.length; i++){
								d = ds[i];
								if(a.onIds.indexOf(d) > -1){
									ops = 1.0;
								}
							}
							return ops;
						})
						.style('stroke-width',function(a){
							var ops = 0.5/currentScale;
							for(var i = 0;i<ds.length; i++){
								d = ds[i];
								if(a.onIds.indexOf(d) > -1){
									ops = 1.5/currentScale;
								}
							}
							return ops + "px";
						});
				features.selectAll(".util-circle")
					.style('opacity',function(a){
						if (ds.indexOf(a.id)>-1){
							return 1.0;
						}
						else{
							return 0.2;
						}
					})
					.style('stroke-opacity',function(a){
						if (ds.indexOf(a.id)>-1){
							return 1.0;
						}
						else{
							return 0.2;
						}
					});
				features.selectAll(".va-circle")
					.style('opacity',function(a){
						if (ds.indexOf(a.id)>-1){
							return 1.0;
						}
						else{
							return 0.2;
						}
					})
					.style('stroke-opacity',function(a){
						if (ds.indexOf(a.id)>-1){
							return 1.0;
						}
						else{
							return 0.2;
						}
					});
				features.selectAll(".pop-circle")
				.style('opacity',function(a){
					if (ds.indexOf(a.id)>-1){
						return 1.0;
					}
					else{
						return 0.2;
					}
				})
				.style('stroke-opacity',function(a){
					if (ds.indexOf(a.id)>-1){
						return 1.0;
					}
					else{
						return 0.2;
					}
				});
			};
			function highlightRoutes(ds){
				features.selectAll(".route-line")
					// .each(function(a){
					// if(ds.indexOf(a.id) > -1){
							// console.log(a);
					// }
					// })
					.style('opacity',function(a){
						var ops = 0.3;
						if(ds.indexOf(a.id) > -1){
							ops = 1.0;
						}
						return ops;
					})
					.style('stroke-width',function(a){
						var ops = 0.5/currentScale
						if(ds.indexOf(a.id) > -1){
							ops = 1.5/currentScale;
						}
						return ops + "px";
					})
					.style('stroke',function(a){
						var ops = "white";
						if(ds.indexOf(a.id) > -1){
							ops = "gold";
						}
						return ops;
					});
				features.selectAll(".route-util-line")
					.style('opacity',function(a){
						var ops = 1.0;
						if(ds.indexOf(a.id) > -1){
							ops = 1.0;
						}
						return ops;
					})
					.style('stroke-width',function(a){
						var ops = 0.5/currentScale
						if(ds.indexOf(a.id) > -1){
							ops = 1.5/currentScale;
						}
						return ops + "px";
					});
			}
			
			function restoreEverything(){
				features.selectAll(".store-circle").style('opacity',1.0);
				features.selectAll(".route-line").style('opacity',1.0).style('stroke-width',(0.25/currentScale)+"px").style('stroke',"white");
				features.selectAll(".util-circle").style('opacity',1.0).style('stroke-opacity',1.0);
				features.selectAll(".pop-circle").style('opacity',1.0).style('stroke-opacity',1.0);
				features.selectAll(".va-circle").style('opacity',1.0).style('stroke-opacity',1.0);
				features.selectAll(".route-util-line").style('opacity',1.0).style('stroke-width',(0.25/currentScale)+"px");
			};

			function showAllStores(){
				if($("#show_population").is(":checked")){
					features.selectAll(".pop-circle").style('display','block');
				}
				else if($("#show_vaccine").is(":checked")){
					features.selectAll(".va-circle").style('display','block');
				}
				else if($("#show_utilization").is(":checked")){
					features.selectAll(".util-circle").style('display','block');
				}
				else{
					features.selectAll(".store-circle").style('display','block');
				}
			};

			function hideAllStores(){
				if($("#show_population").is(":checked")){
					features.selectAll(".pop-circle").style('display','none');
				}
				else if($("#show_vaccine").is(":checked")){
					features.selectAll(".va-circle").style('display','none');
				}
				else if($("#show_utilization").is(":checked")){
					features.selectAll(".util-circle").style('display','none');
				}
				else{
					features.selectAll(".store-circle").style('display','none');
				}
			};

			function showStoresForLevel(level_num){
				if($("#show_population").is(":checked")){
					features.selectAll(".pop-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == level_num){
							console.log("turning on "+d.id);
							return "inline";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
				else if($("#show_vaccine").is(":checked")){
					features.selectAll(".va-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == level_num){
							console.log("turning on "+d.id);
							return "inline";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
				else if($("#show_utilization").is(":checked")){
					features.selectAll(".util-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == level_num){
							console.log("turning on "+d.id);
							return "inline";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
				else{
					features.selectAll(".store-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == level_num){
							console.log("turning on "+d.id);
							return "inline";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
			};

			function hideStoresForLevel(level_num){
				if($("#show_population").is(":checked")){
					features.selectAll(".pop-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == (level_num)){
							return "none";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
				else if($("#show_vaccine").is(":checked")){
					features.selectAll(".va-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == (level_num)){
							return "none";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
				else if($("#show_utilization").is(":checked")){
					features.selectAll(".util-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == (level_num)){
							return "none";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
				else{
					features.selectAll(".store-circle").style('display',function(d){
						console.log(d.level + " " + level_num)
						if(d.level == (level_num)){
							return "none";
						}
						else{
							return d3.select(this).style('display');
						}
					});
				}
				;
			};

			
			function zoomed() { 
				  // console.log(d3.event.translate);
				  translate = d3.event.translate
				  scale = d3.event.scale
				  area = 1/scale/scale;
				  currentScale = d3.event.scale;
				  features.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
				  features.selectAll(".land").style("stroke-width", 1.5 / d3.event.scale + "px");
				  features.selectAll(".state-border").style("stroke-width", 0.5 / d3.event.scale + "px");
				  features.selectAll(".country-border").style("stroke-width", 1.0 / d3.event.scale + "px");
				  features.selectAll(".road").style("stroke-width", function(d){ var sc = (.25 / d3.event.scale); if(sc < 0.010){return 0.025+"px"}else{ return sc + "px"}});
				  features.selectAll(".store-circle")
				  	.attr('r',function(d){return 15.0/(d.level+1)/d3.event.scale;})
				  	.style('stroke-width',(1.0/d3.event.scale)+"px");
				  features.selectAll(".va-circle")
				  	.attr('r',function(d){
				  		var factor = 3.0/d3.event.scale;
				  		return Math.max(factor,0.04);
				  		// return 3.0/d3.event.scale})
				  	})
				  	.style('stroke-width',(1.0/d3.event.scale)+"px");
				  features.selectAll(".util-circle")
				  	.attr('r',function(d){return 3.0/d3.event.scale})
				  	.style('stroke-width',(1.0/d3.event.scale)+"px");
				  features.selectAll(".pop-circle")
				  	.attr('r',function(d){ 
				  		var factor = (0.5*(100.0*d.pop))
				  		if(factor < 3.0){
				  			factor = 3.0;
				  		}
				  		return factor/d3.event.scale;
				  	})
				  	.style('stroke-width',(1.0/d3.event.scale)+"px");
				  features.selectAll(".route-util-line").style("stroke-width",function(d){ 
					  var ops = 0.50/d3.event.scale;
					  if(selectedRoute.indexOf(d.id)>-1){
						  ops = 1.5/d3.event.scale;
					  }
					  return ops + "px";
				  });
				  features.selectAll(".route-line").style("stroke-width",function(d){ 
					  var ops = 0.50/d3.event.scale;
					  if(selectedRoute.indexOf(d.id)>-1){
						  ops = 1.5/d3.event.scale;
					  }
					  return ops + "px";
				  });
				  curr_scale = d3.event.scale;
			}


			// If the drag behavior prevents the default click,
			// also stop propagation so we don’t click-to-zoom.
			function stopped() {
			if (d3.event.defaultPrevented) d3.event.stopPropagation();
			}

			function createLayerTableHtmlString(levelsList,tphrases){

				htmlString = '<table class="legend-table">';
				htmlString += '<tr>';
				htmlString += '<td class="legend-title">'+tphrases[0]+'</td>';
				htmlString += '<td colspan=2 style="text-align:right;" width="160px">Zoom <button class="zoombut" id="zoomIn">+</button><button class="zoombut" id="zoomOut">-</button></td>'
				htmlString += '</tr>'
				htmlString += '<tr>';
				htmlString += '<td width="45px"></td>';
				htmlString += '<td></td>';
				htmlString += '<td width="120px"></td>';
				htmlString += '</tr>';
				htmlString += '<tr>';
				htmlString += '<td width="50px"></td>';
				htmlString += '<td colspan=2 class="legend-heading">'+tphrases[1] + ':</td>';
				htmlString += '</tr>';
				htmlString += '<tr>';
				htmlString += '<td width="50px"></td>';
				htmlString += '<td id="level_lab_all" class="legend-item">'+tphrases[2]+':</td>';
				htmlString += '<td width:"100px">';
				htmlString += '<input type="checkbox" id="show_all_levels" checked/>';
				htmlString += '</td>';
				htmlString += '</tr>';
				for(var i=0; i < levelsList.length;++i){
					htmlString += '<tr id="level_row_' + i + '" style="display:none">';
					htmlString += '<td width="50px"></td>';
					htmlString += '<td id="level_lab_{{i}}" class="legend-item">'+levelsList[i]+':</td>';
					htmlString += '<td width:"100px">';
					htmlString += '<input type="checkbox" id="show_level_' + i + '"/>';
					htmlString += '</td>';
					htmlString += '</tr>';
				}
				htmlString += '<tr>';
				htmlString += '<td width="50px"></td>';
				htmlString += '<td colspan=2 class="legend-heading"><br>' + tphrases[3] + ':</td>';
				htmlString += '</tr>';
				htmlString += '<tr>';
				htmlString += '<td width="50px"></td>';
				htmlString += '<td id="poplab" class="legend-item">' + tphrases[4] + ':</td>';
				htmlString += '<td width:"100px">';
				htmlString += '<input type="checkbox" id="show_population"/>';
				htmlString += '</td>';
				htmlString += '</tr>';
				htmlString += '<tr>';
				htmlString += '	<td width="50px"></td>';
				htmlString += '<td id ="utillab" class="legend-item">' + tphrases[5] + ':</td>';
				htmlString += '<td width:"100px"> ';
				htmlString += '<input type="checkbox" id="show_utilization" value="On"/>';
				htmlString += '</td>';
				htmlString += '</tr>';
				htmlString += '<tr>';
				htmlString += '<td width="50px"></td>';
				htmlString += '<td class="legend-item">' + tphrases[6] + ':</td>';
				htmlString += '<td width:"100px"> ';
				htmlString += '<input type="checkbox" id="show_vaccine" value="On"/>';
				htmlString += '</td>';
				htmlString += '</tr>';
				htmlString += '<tr>';
				htmlString += '<td colspan=2 class="legend-title"><br>' + tphrases[7] + ':</td>';
				htmlString += '<td width="100px"></td>';
				htmlString += '</tr>';
				htmlString += '<!--<tr>';
				htmlString += '<td width=50px"></td>';
				htmlString += '<td class="legend-item">' + tphrases[8] + '</td>';
				htmlString += '<td width="100px">';
				htmlString += '<input type="checkbox" id="show_routes" value="On"/>';
				htmlString += '</td>';
				htmlString += '</tr>-->';
				htmlString += '<tr>';
				htmlString += '<td width=50px"></td>';
				htmlString += '<td class="legend-item">' + tphrases[9] + '</td>';
				htmlString += '<td width="100px"> ';
				htmlString += '<input type="checkbox" id="show_routes_util" value="On"/>';
				htmlString += '</td>';
				htmlString += '</tr>';
				htmlString += '</table>';
				htmlString += '<table>';
				htmlString += '<tr>';
				htmlString += '<td><div id="legendContainer"></div></td>'
				htmlString += '</table>';
				htmlString += '<table>';
				htmlString += '<tr>';
				htmlString += '<td><div id="routeLegendContainer"></div></td>'
				htmlString += '</table>';

				return htmlString;
				
			}
			
	
		
		function drawMap(stateJSON, countryJSON,ppJSON,roadsJSON, storeJSON, routesJSON,height,width){
			var states = stateJSON.objects.state;
			var countries = countryJSON.objects.countries;
			for(var i=0; i < storeJSON.geoFC.features.length;i++){
				levelHere = levelList[storeJSON.geoFC.features[i].level];
				
				$("#level_row_"+storeJSON.geoFC.features[i].level).show()
			}
			
			var bounds = path.bounds(storeJSON.geoFC);

			// Create a new bounding Box that is some percent larger
			// than the stores
			var newBounds = [[0.0,0.0],[0.0,0.0]];
			var yDiff = bounds[1][0]-bounds[0][0]
			var xDiff = bounds[1][1]-bounds[0][1];
			var perDiff = 5.0;
			newBounds[0][0] = bounds[0][0] - perDiff*yDiff;
			newBounds[1][0] = bounds[1][0] + perDiff*yDiff;
			newBounds[0][1] = bounds[0][1] - perDiff*xDiff;
			newBounds[1][1] = bounds[1][1] + perDiff*xDiff;
			var centroid = path.centroid(storeJSON.geoFC);
			
			// Create reduced jsons based on proximity to the actual
			// visualization.
			var ctIds = [];
			var ctjson = countryJSON.objects.countries.geometries.filter(function(d){
				thisCentroid = path.centroid(topojson.feature(countryJSON,d));
				var flag = ((thisCentroid[0] >= newBounds[0][0] && thisCentroid[0] <= newBounds[1][0]) && 
						(thisCentroid[1] >= newBounds[0][1] && thisCentroid[1] <= newBounds[1][1]));
				if (flag) {
					ctIds.push(d.properties.name);
				}
				return flag;
			});
			
			var ctgjson = topojson.feature(countryJSON,countryJSON.objects.countries).features.filter(
					function(d) { 
						return ctIds.indexOf(d.properties.name) > -1;
					});
			
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
						return "#"+rainbow.colorAt(100*d.util);
					})
					.style("stroke-width",0.25+"px")
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
						return "white";
					})
					.style("stroke-width",function(d){
						if(d.bold == "true"){
							return 0.1+"px";
						}
						else{
							return 0.010 +"px";
						}
					})
					.style("fill-opacity",function(d){
						if(d.bold == "true"){
							return 1.0;
		}
						else{
							return 0.0;
						}
					})
					.style("visibility",function(d){
						//console.log(d);
						if((d.geometry.coordinates[0][0] == -1.0 && d.geometry.coordinates[0][1]==-1.0) ||
								(d.geometry.coordinates[1][0] == -1.0 && d.geometry.coordinates[1][1]==-1.0)){
							//console.log("hidden");
							return "hidden";
						}
						else return "visible";                                                         
					})
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
					.style("fill",function(d){
						if(d.bold == "true"){
							in_count++;
							return "red";
						}
						if("{{leila}}"=="true"){
							var idstr = (''+d.id).substring(1,3);
							return provinceColors[idstr];
						}
						else{
							return levelColors[d.level];
						}
					})
					.style("fill-opacity",0.75)
					.style("stroke",function(d){
						return "black";
						return levelColors[d.level];
					})
					.style("visibility",function(d){
							if(d.geometry.coordinates[0] == -1.0 && d.geometry.coordinates[1] == -1.0) return "hidden";
							else return "visible";
					})			
					.style("stroke-width",0.010+"px")
					.on("click",clickStoreDialog)
					.on("mouseover",function(d){
						storeTipDiv.transition()
							.duration(200)
							.style("opacity",0.9);
						storeTipDiv.html("Name: "+ d.name + "<br>Level: "+levelList[d.level]+"<br>Lat,Lon: " +
								d.geometry.coordinates[1] + "," + d.geometry.coordinates[0])
							.style("left",(d3.event.pageX)+"px")
							.style("top",(d3.event.pageY - 28) + "px");
					})
					.on("mouseout",function(d){
						storeTipDiv.transition()
							.duration(500)
							.style("opacity",0);
					});
			
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
					.style("fill",function(d){
						return "#"+rainbow.colourAt(100*d.util);
					})
					.style("fill-opacity",1.0)
					.style("stroke",function(d){
						return "black";
					})
					.style("visibility","hidden")
					.style("stroke-width",0.010+"px")
					.on("click",clickStoreDialog)
					.on("mouseover",function(d){
						console.log(d);
						storeTipDiv.transition()
							.duration(200)
							.style("opacity",1.0);
						storeTipDiv.html("Name: "+ d.name + "<br>Level: "+levelList[d.level]+"<br>Maximum Storage Utilization: " +
								parseFloat(d.util*100.0).toFixed(2) + "%")
							.style("left",(d3.event.pageX)+"px")
							.style("top",(d3.event.pageY - 28) + "px");
					})
					.on("mouseout",function(d){
						storeTipDiv.transition()
							.duration(500)
							.style("opacity",0);
					});
			
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
					.style("fill",function(d){
						return "#"+rainbow.colourAt(100*d.pop);
					})
					.style("fill-opacity",1.0)
					.style("stroke","black")
					.style("stroke-width",0.010+"px")
					.on("click",clickStoreDialog)
					.on("mouseover",function(d){
						console.log(d);
						storeTipDiv.transition()
							.duration(200)
							.style("opacity",1.0);
						storeTipDiv.html("Name: "+ d.name + "<br>Level: "+levelList[d.level]+"<br>Percent of Population: " +
								parseInt(d.pop*thisoptions.maxpop))
							.style("left",(d3.event.pageX)+"px")
							.style("top",(d3.event.pageY - 28) + "px");
					})
					.on("mouseout",function(d){
						storeTipDiv.transition()
							.duration(500)
							.style("opacity",0);
					});
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
				.style("fill",function(d){
					return "#"+rainbow.colourAt(100.0-d.va);
				})
				.style("fill-opacity",function(d){
					if(d.va<0.0){
						return 0.0;
					}
					else{
						return 1.0;
					}
				})
				.style("stroke","black")
				.style("stroke-width",function(d){if(d.va<0.0){return 0.0+"px";}else{return 0.010+"px";}})
				.style("stroke-opacity",function(d){if(d.va<0.0){return 0.0;}else{return 1.0;}})
				.on("click",clickStoreDialog)
				.on("mouseover",function(d){
					if(d.va < 0.0){return;}
					storeTipDiv.transition()
						.duration(200)
						.style("opacity",1.0);
					storeTipDiv.html("Name: "+ d.name + "<br>Level: "+levelList[d.level]+"<br>Vaccine Availability: " +
							parseFloat(d.va).toFixed(2) + "%")
						.style("left",(d3.event.pageX)+"px")
						.style("top",(d3.event.pageY - 28) + "px");
				})
				.on("mouseout",function(d){
					storeTipDiv.transition()
						.duration(500)
						.style("opacity",0);
				});
			zoomToCollection(storeJSON.geoFC);
			doneLoading();
		};
		
		d3.select(self.frameElement).style("height", height + "px");
	}
		
		
	});
})(jQuery);
