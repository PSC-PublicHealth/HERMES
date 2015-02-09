/*
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
*/
;(function($) {
    $.widget("treelayout.diagram", {
    	options: {
    		file: 'static/tree-layout-diagram/readme.json',
    		jsonData: {'name':'Central','children':[{'name':'Region','children':[{'name':'District','children':[{'name':'Health Post'}]}]}]},
		    minWidth: 500,
		    minHeight: 300,
		    scrollable: false,
		    resizable: false,
		    selectedNode: -1,
		    hasChildrenColor: "steelblue",
		    noChildrenColor: "#adf",
		    trant: {
    			title: 'Tree Layout Diagram'
    		}
    	},
    	
    	bold_level: function(levelNum){
			console.log("making locname_"+levelNum+ " bold");
			$("#levelname_"+levelNum).attr("font-weight","bold");
			$('rect#rect_'+levelNum).attr("style","fill:lightsteelblue");
			$('#loctext_'+levelNum).attr("style","font-color:white;font-weight:bold");
		},

		unbold_level: function(levelNum){
				console.log("unbolding "+ levelNum);
				$("#levelname_"+levelNum).attr("font-weight","normal");
				$('rect#rect_'+levelNum).attr("style","fill:white");
				$('#loctext_'+levelNum).attr("style","font-color:black;font-weight:normal");
		},

    	
		flip_link_arrow: function(levelNum,flag){
			if(flag=="true"){
				if(($("#link_"+levelNum).attr('marker-start')=='url(#arrowhead-start)')||($("#link_"+levelNum).attr('marker-end')=='url(#arrowhead)')){
					$("#link_"+levelNum).attr('marker-start','url(#arrowhead-start)');
    			}
    			else{
    				$("#link_"+levelNum).attr('marker-start','url(#arrowhead-start-high)');
    			}
				$("#link_"+levelNum).attr('marker-end','');
			}	
    		else{				
				if(($("#link_"+levelNum).attr('marker-start')=='url(#arrowhead-start)')||($("#link_"+levelNum).attr('marker-end')=='url(#arrowhead)')){
					$("#link_"+levelNum).attr('marker-end','url(#arrowhead)');
    			}
    			else{
    				$("#link_"+levelNum).attr('marker-end','url(#arrowhead-high)');
    			}
				$("#link_"+levelNum).attr('marker-start','');
    		}
		},
		
		bold_link_arrow: function(levelNum){
			if(!$('#link_'+levelNum).attr('marker-start'))
				$("#link_"+levelNum).attr("style","stroke:black;stroke-width:3.0px;").attr("marker-end","url(#arrowhead-high)");
			else
				$("#link_"+levelNum).attr("style","stroke:black;stroke-width:3.0px;").attr("marker-start","url(#arrowhead-start-high)");
			
			$("#link_amt_"+levelNum).css('font-weight','bold');
			$("#link_freq_"+levelNum).css('font-weight','bold');
			$("#link_interv_"+levelNum).css('font-weight','bold');
			$("#link_transit_"+levelNum).css('font-weight','bold');
			$("#link_distance_"+levelNum).css('font-weight','bold');
		},

		unbold_link_arrow: function(levelNum){
			if(!$('#link_'+levelNum).attr('marker-start'))
				$("#link_"+levelNum).attr("style","stroke:#ccc;stroke-width:1.5px;").attr("marker-end","url(#arrowhead)");
			else
				$("#link_"+levelNum).attr("style","stroke:#ccc;stroke-width:1.5px;").attr("marker-start","url(#arrowhead-start)");
				
			$("#link_amt_"+levelNum).css('font-weight','normal');
			$("#link_freq_"+levelNum).css('font-weight','normal');
			$("#link_interv_"+levelNum).css('font-weight','normal');
			$("#link_transit_"+levelNum).css('font-weight','normal');
			$("#link_distance_"+levelNum).css('font-weight','normal');
		},


		change_level_name: function(levelNum, levelName){
			$("#levelname_"+levelNum).text(levelName);
		},

		change_location_text: function(levelNum, levelCount){
			$("#loctext_"+levelNum).text(levelCount);
		},

		zoomBy: function(factor){
			console.log("Zooming to " + factor);
			$("#treeSVG").attr("transform","scale(" + factor + ")");
		},

		change_route_amt: function(levelNum,flag){
			if(flag == 'true'){
				$("#link_amt_" + levelNum).text("fixed amount");
			}
			else{
				$("#link_amt_" + levelNum).text("demand based amount");
			}
		},
		
		change_route_freq: function(levelNum,flag){
			if(flag == 'true'){
				$("#link_freq_" + levelNum).text("fixed frequency");
			}
			else{
				$("#link_freq_" + levelNum).text("frequency as needed");
			}
		},
		
		change_route_interv: function(levelNum,interv,ymw){
			intervInt = parseInt(interv);
			intervFloat = parseFloat(interv);
			if (intervInt == intervFloat)
				$("#link_interv_" + levelNum).text(intervInt + " shipments per " + ymw);
			else
				$("#link_interv_" + levelNum).text(intervFloat + " shipments per " + ymw);
		},

		change_route_time: function(levelNum, timing, unit){
			var intervInt = parseInt(timing);
			var intervFloat = parseFloat(timing);
			if (intervFloat > 1.0)
				unit += "s";
			//STB TO DO, this will not translate yet...
			if (intervInt == intervFloat)
				$("#link_transit_"+levelNum).text("transit time: "+ intervInt + " " + unit);
			else
				$("#link_transit_"+levelNum).text("transit time: " +intervFloat + " " + unit);
			
		},

		change_route_distance: function(levelNum, distance){
			var intervInt = parseInt(distance);
			var intervFloat = parseFloat(distance);
			if(intervInt == intervFloat)
				$("#link_distance_"+levelNum).text("distance: "+ intervInt + " km");
			else
				$("#link_distance_"+levelNum).text("distance: "+ intervFloat + " km");	
		},

    	_create: function() {
    		trant = this.options.trant;
    		updateFixed = true;
    		this.containerID = $(this.element).attr('id');
    		
    		this.svgContainerID = this.containerID+"svgContainer";
    		d3.select("#"+this.containerID).append("svgContainer")
    			.attr("id",this.svgContainerID);
    			
    		var getDepth = function (obj) {
				var depth = 0;
				if (obj.children) {
					obj.children.forEach(function (d) {
							var tmpDepth = getDepth(d);
							if (tmpDepth > depth) {
								depth = tmpDepth;
							}
						});
				}
				return 1 + depth;
    		};
    		  		
            var margin = {
            		top: 0,
            		right: 0,
            		bottom: 0,
            		left: 0
            };
            
            var width = 375 - margin.right - margin.left;
            var height = 525 - margin.top - margin.bottom;

            var i = 0;
            var duration = 750; 
            var rectW = 100;
            var rectH = 40;
            
            var insertLinebreaks = function (d) {
            	var el = d3.select(this);
            	var words = d.split(' ');
            	el.text('');

            	for (var i = 0; i < words.length; i++) {
            		var tspan = el.append('tspan').text(words[i]);
            		if (i > 0)
            			tspan.attr('x', 0).attr('dy', '15');
            	}
            };
            
            var tree = d3.layout.tree().nodeSize([10,10]);
           // 
            var diagonal = d3.svg.diagonal()
            		.projection(function (d) {
            			return [d.x + rectW / 2, d.y + rectH / 2];
            		});
	
            var root = this.options.jsonData;

            var startX = (width-rectW)/2;///3.75;
            var startY = rectH;
            var svg = d3.select("#"+this.svgContainerID).append("svg")
            		.attr("width", width)
            		.attr("height", height)
            		.call(zm = d3.behavior.zoom().scaleExtent([0.1,3])
            		.on("zoom", redraw))
            		.attr("id","treeSVG")
            		.append("g")
            		.attr("transform", "translate(" + startX + "," + startY + ")");
            
            svg.append("defs").append("marker")
					.attr("id", "arrowhead")
					.attr("refX", rectH/2 - 5.75) /*must be smarter way to calculate shift*/
					.attr("refY", 0)
					.attr("markerWidth", 15)
					.attr("markerHeight", 15)
					.attr("stroke","#ccc")
					.attr("stoke-width",2)
					.attr("fill","#ccc")
					.attr("orient", "auto")
					.attr('viewBox',"0,-5 10 10")
					.append("path")
					.attr("d", 'M 0,0 m -5,-5 L 5,0 L -5,5 Z');
					
			svg.append("defs").append("marker")
					.attr("id", "arrowhead-high")
					.attr("refX", rectH/2 - 5.75) /*must be smarter way to calculate shift*/
					.attr("refY", 0)
					.attr("markerWidth", 7)
					.attr("markerHeight", 7)
					.attr("stroke","black")
					.attr("stoke-width",2)
					.attr("fill","black")
					.attr("orient", "auto")
					.attr('viewBox',"0,-5 10 10")
					.append("path")
					.attr("d", 'M 0,0 m -5,-5 L 5,0 L -5,5 Z');
					 //this is actual shape for arrowhead
			
			svg.append("defs").append("marker")
					.attr("id", "arrowhead-start")
					.attr("refX", -rectH/2+35) /*must be smarter way to calculate shift*/
					.attr("refY", 0)
					.attr("markerWidth", 15)
					.attr("markerHeight", 15)
					.attr("stroke","#ccc")
					.attr("stoke-width",2)
					.attr("fill","#ccc")
					.attr("orient","270")
					.attr('viewBox',"0,-5 10 10")
					
					.append("path")
					.attr("d", 'M 0,0 m -5,-5 L 5,0 L -5,5 Z');
					
			svg.append("defs").append("marker")
					.attr("id", "arrowhead-start-high")
					.attr("refX", -rectH/2+35) /*must be smarter way to calculate shift*/
					.attr("refY", 0)
					.attr("markerWidth", 7)
					.attr("markerHeight", 7)
					.attr("stroke","black")
					.attr("stoke-width",2)
					.attr("fill","black")
					.attr("orient","270")
					.attr('viewBox',"0,-5 10 10")
					
					.append("path")
					.attr("d", 'M 0,0 m -5,-5 L 5,0 L -5,5 Z');
            //necessary so that zoom knows where to zoom and unzoom from
            //zm.translate([startX,startY]);
            // necessary so that zoom knows where to zoom and unzoom from
            root.x0 = 0;
            root.y0 = height / 2;
            
            //root.children.forEach(collapse);
            update(root);
            //centerNode(root);
	        
            function collapse(d) {
				if (d.children) {
					d._children = d.children;
					d._children.forEach(collapse);
					d.children = null;
				}
			}

			function redraw() {
				//svg.attr("transform",
				//  "translate(" + d3.event.translate + ")"
				//  + " scale(" + d3.event.scale + ")");
			};
		
			function centerNode(source) {
		        var scale = zm.scale();
		        var x = -source.y0;
		        var y = -source.x0;
		        x = x * scale + parseInt(svg.style('width')) / 2;
		        y = y * scale + parseInt(svg.style('height')) / 2;
		        d3.select('g').transition()
		            .duration(duration)
		            .attr("transform", "translate(" + x + "," + y + ")scale(" + scale + ")");
		       zm.scale(scale);
		       zm.translate([x, y]);
		       return [x,y];
			};
			
			function update(source) {			
				var depthChart = [];
				var depthY = [];
				var levelNames = [];
				var linkY = [];
				var linkBools = [];
				var maxDepth = getDepth(root);
				for (var i=0;i < maxDepth;i++){
					depthChart.push(false);
					depthY.push(0);
					linkY.push(0);
					linkBools.push([]);
					levelNames.push("");
				}

				// Compute the new tree layout.
				
				var nodes = tree.nodes(root).reverse();
				var links = tree.links(nodes);
				// Normalize for fixed-depth.
							
				nodes.forEach(function (d) {
					//d.x = d.depth*20.0;//d.depth * 40*4/(getDepth(root));
				   d.y = d.depth * 120*4/(maxDepth);
				});
				
				// Update the nodes
				var node = svg.selectAll("g.node")
				    .data(nodes, function (d) {
				    	return d.id || (d.id = ++i);
				    });
				
				// Enter any new nodes at the parent's previous position.
				var nodeEnter = node.enter().append("g")
				    .attr("class", "node")
				    .attr("transform", function (d) {
				    	return "translate(" + source.x0 + "," + source.y0 + ")";
				});
				   // .on("click", click);
				
				nodeEnter.append("rect")
				    .attr("width",rectW) 
				    .attr("height", rectH)
				    .attr("stroke", "black")
				    .attr("stroke-width", 1)
				    .attr("id",function(d){
				    	return "rect_"+d.depth;
				    })
				    .style("fill", "#fff");
				    //}"function (d) {
				    //
				    //	return (d.depth == selectedNode) ? "lightsteelblue" : "#fff";
				    //});
				
				if(updateFixed){
					nodeEnter.append("text")
					    .attr("x", rectW / 2)
					    .attr("y", rectH / 2)
					    .attr("dy", ".35em")
					    .attr("text-anchor", "middle")
					    .attr("id",function(d){
					    	return "loctext_"+d.depth;
					    })
					    .text(function (d) {
					    	if(depthChart[d.depth] == false){
					    		console.log(" DepthChart = "+ depthChart);
					    		depthChart[d.depth]=true;
					    		depthY[d.depth]=d.y;
					    		levelNames[d.depth] = d.name;
					    		if (d.count == 1){
					    			return d.count + " Location";
					    		}
					    		else{
					    			return d.count + " Locations";
					    		}
	
					    	}
					    });					  	
				}
				
				// Transition nodes to their new position.
				var nodeUpdate = node.transition()
				    .duration(duration)
				    .attr("transform", function (d) {
				    	return "translate(" + d.x + "," + d.y + ")";
				});
				
				nodeUpdate.select("rect")
				    .attr("width", rectW)
				    .attr("height", rectH)
				    .attr("stroke", "black")
				    .attr("stroke-width", 1)
				    .style("fill", function (d) {
				    	return "#fff"
				    	//return (d.depth == selectedNode) ? "lightsteelblue" : "#fff";
				});
				
				nodeUpdate.select("text")
				    .style("fill-opacity", 1);
				
				// Transition exiting nodes to the parent's new position.
				var nodeExit = node.exit().transition()
				    .duration(duration)
				    .attr("transform", function (d) {
				    	return "translate(" + source.x + "," + source.y + ")";
				    })
				    .remove();
				
				nodeExit.select("rect")
				    .attr("width", rectW)
				    .attr("height", rectH)
				    .attr("stroke", "black")
				    .attr("stroke-width", 1);
				
				nodeExit.select("text");
				
				// Update the links
				var link = svg.selectAll("path.link")
				    .data(links, function (d) {
				    	return d.target.id;
				    });
				
				

				// Enter any new links at the parent's previous position.
				link.enter().insert("path", "g")
				    .attr("class", "link")
				    .attr("x", rectW / 2)
				    .attr("y", rectH / 2)
				    .attr("d", function (d) {
				    	linkY[d.source.depth]=((d.source.y+d.target.y)/2);
				    	linkBools[d.source.depth] = [d.source.isfixedam,d.source.issched,d.source.interv,
				    	                             d.source.ymw,d.source.time,d.source.timeunit,d.source.distance];
				    	console.log(d.source);
					    var o = {
					        x: source.x0,
					        y: source.y0
					    };
					    return diagonal({
					        source: o,
					        target: o
					    });
				    });
				    
				
				// Transition links to their new position.
				link.transition()
				    .duration(duration)
				    .attr("d", diagonal);
				
				// Transition exiting nodes to the parent's new position.
				link.exit().transition()
				    .duration(duration)
				    .attr("d", function (d) {
					    var o = {
					        x: source.x,
					        y: source.y
					    };
					    return diagonal({
					        source: o,
					        target: o
					    });
					})
				    .remove();
				 			
				svg.selectAll(".link")
					.attr("id",function(d){
						return "link_"+d.source.depth;
					})
					.attr("marker-end",function(d){
						if(d.source.isfetch == "false")
							return "url(#arrowhead)";
						else
							return "";
					})
					.attr("marker-start",function(d){
						if(d.source.isfetch == "true")
							return "url(#arrowhead-start)";
						else
							return "";
					});
					
				// Stash the old positions for transition.
				nodes.forEach(function (d) {
				    d.x0 = d.x;
				    d.y0 = d.y;
				});
				
				if(updateFixed){
					svg.append("text")
						.attr('text-anchor','middle')
						.attr('font-weight','bold')
						.attr('font-size','12px')
						.attr("dy",".35em")
						.text('Products Begin Here')
						.attr("transform",function(d){
							return "translate("+(root.x+rectW/2)+","+(root.y - rectH/2) +")";
						});
					svg.append("text")
						.attr('text-anchor','middle')
						.attr('font-weight','bold')
						.attr('font-size','12px')
						.attr("dy",".35em")
						.text('Products Terminate Here')
						.attr("transform",function(d){
							var depthHere = depthY[maxDepth-1];
							console.log("DY = " + depthHere);
							return "translate("+(root.x+rectW/2)+","+(depthHere + rectH*1.5) +")";
						});
					
						for(var i=0;i<depthY.length;i++){
							svg.append("text")
							.attr('font-size','11px')
							.attr("dy",".35em")
							.attr('id','levelname_'+i)
							.attr('class','levelname')
							.text(levelNames[i])
							.attr("transform",function(d){
								return "translate("+(root.x-width/2+rectW/2)+","+(depthY[i] + rectH/2) +")";
							});
						}
						console.log(linkBools);
						for(var i=0;i<linkY.length-1;i++){
							svg.append("text")
							.attr('font-size','11px')
							.attr('id','link_amt_'+i)
							.attr('class','link_routeinfo')
							.text(function(d){
								console.log("Bool2 = " + linkBools[i][0]);
								if(linkBools[i][0]=="true")
									return "fixed amount";
								else
									return "demand based amount";
								})
							.attr("dy",".35em")
							.attr("transform",function(d){
								return "translate("+(root.x + width/2-rectW/2-35)+","+(linkY[i] + rectH/2-22) +")";
							});
							svg.append("text")
							.attr('font-size','11px')
							.attr('id','link_freq_'+i)
							.attr('class','link_routeinfo')
							.text(function(){
								if(linkBools[i][1]=="true")
										return "fixed frequency";
									else
										return "frequency as needed";
							})
							.attr("dy",".35em")
							.attr("transform",function(d){
								return "translate("+(root.x + width/2-rectW/2-35)+","+(linkY[i] + rectH/2 - 11)+")";
							});
							svg.append("text")
							.attr('font-size','11px')
							.attr('id','link_interv_'+i)
							.attr('class','link_routeinfo')
							.text(function(){
								var intervInt = parseInt(linkBools[i][2]);
								var intervFloat = parseFloat(linkBools[i][2]);
								console.log(intervInt + " " + linkBools[i][2] + " " + intervFloat);
								
								//STB TO DO, this will not translate yet...
								if (intervInt == intervFloat)
									return intervInt + " shipments per " + linkBools[i][3];
								else
									return intervFloat + " shipments per " + linkBools[i][3];
							})
							.attr("dy",".35em")
							.attr("transform",function(d){
								return "translate("+(root.x + width/2-rectW/2-35)+","+(linkY[i]+rectH/2)+")";
							});
							
							svg.append("text")
							.attr('font-size','11px')
							.attr('id','link_transit_'+i)
							.attr('class','link_routeinfo')
							.text(function(){
								var intervInt = parseInt(linkBools[i][4]);
								var intervFloat = parseFloat(linkBools[i][4]);
								console.log(intervInt + " " + linkBools[i][4] + " " + intervFloat);
								var unit = linkBools[i][5];
								if (intervFloat > 1.0)
									unit += "s";
								//STB TO DO, this will not translate yet...
								if (intervInt == intervFloat)
									return "transit time: "+ intervInt + " " + unit;
								else
									return "transit time: " +intervFloat + " " + unit;
								
							})
							.attr("dy",".35em")
							.attr("transform",function(d){
								return "translate("+(root.x + width/2-rectW/2-35)+","+(linkY[i]+rectH/2+11)+")";
							});
							
							svg.append("text")
							.attr('font-size','11px')
							.attr('id','link_distance_'+i)
							.attr('class','link_routeinfo')
							.text(function(){
								var intervInt = parseInt(linkBools[i][6]);
								var intervFloat = parseFloat(linkBools[i][6]);
								console.log(intervInt + " " + linkBools[i][6] + " " + intervFloat);
								//STB TO DO, this will not translate yet...
								if (intervInt == intervFloat)
									return "distance: "+ intervInt + " km";
								else
									return "distance: " +intervFloat + " km";
								
							})
							.attr("dy",".35em")
							.attr("transform",function(d){
								return "translate("+(root.x + width/2-rectW/2-35)+","+(linkY[i]+rectH/2+22)+")";
							});
						}

					}
				
					//svg.selectAll('text.levelname').each(insertLinebreaks);
					if(updateFixed){
						updateFixed=false;
					}
				}
			}	
    	});
})(jQuery);

    

    	
    	
    