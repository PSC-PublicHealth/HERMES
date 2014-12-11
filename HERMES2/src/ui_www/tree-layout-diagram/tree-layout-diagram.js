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
			$('rect#rect_'+levelNum).attr("style","fill:lightsteelblue")
			$('#loctext_'+levelNum).attr("style","font-color:white;font-weight:bold");
		},

		unbold_level: function(levelNum){
				console.log("unbolding "+ levelNum);
				$("#levelname_"+levelNum).attr("font-weight","normal");
				$('rect#rect_'+levelNum).attr("style","fill:white")
				$('#loctext_'+levelNum).attr("style","font-color:black;font-weight:normal");
				//$("#loctext_"+levelNum).attr("font-weight","normal");
		},

    	
		change_level_name: function(levelNum, levelName){
			$("#levelname_"+levelNum).text(levelName);
		},

		change_location_text: function(levelNum, levelCount){
			$("#loctext_"+levelNum).text(levelCount);
		},

    	_create: function() {
    		trant = this.options.trant;
    		updateFixed = true;
    		console.log("Select is :" + this.options.selectedNode);
    		var selectedNode = -1; //this.options.selectedNode;
    		this.containerID = $(this.element).attr('id');
    		console.log("This Contianer = " + this.containerID);
    		
    		this.svgContainerID = this.containerID+"svgContainer";
    		console.log("SVG = " + this.svgContainerID);
    		d3.select("#"+this.containerID).append("svgContainer")
    			.attr("id",this.svgContainerID);
    		getDepth = function (obj) {
				var depth = 0;
				if (obj.children) {
					obj.children.forEach(function (d) {
							var tmpDepth = getDepth(d)
							if (tmpDepth > depth) {
								depth = tmpDepth
							}
						})
				}
				return 1 + depth
    		};
    		    		
            var margin = {
            		top: 0,
            		right: 0,
            		bottom: 0,
            		left: 0
            };
            
            var width = 800 - margin.right - margin.left;
            var height = 800 - margin.top - margin.bottom;

            var i = 0;
            var duration = 750; 
            var rectW = 200;
            var rectH = 80;
            
            var tree = d3.layout.tree().nodeSize([80,120]);
           // 
            var diagonal = d3.svg.diagonal()
            		.projection(function (d) {
            			return [d.x + rectW / 2, d.y + rectH / 2];
            		});
	
            var root = this.options.jsonData;

            var startX = (width-rectW)/2;
            var startY = rectH;
            var svg = d3.select("#"+this.svgContainerID).append("svg")
            .attr("width", width).attr("height", height)
            .call(zm = d3.behavior.zoom().scaleExtent([0.1,3])
            .on("zoom", redraw))
            .append("g")
            .attr("transform", "translate(" + startX + "," + startY + ")");
	
            //necessary so that zoom knows where to zoom and unzoom from
            zm.translate([startX,startY]);
            // necessary so that zoom knows where to zoom and unzoom from
            root.x0 = 0;
            root.y0 = height / 2;
            
            //root.children.forEach(collapse);
            update(root);
            //centerNode(root);
	
            d3.select("#"+this.containerID).style("height", "800px");
            
            function collapse(d) {
				if (d.children) {
					d._children = d.children;
					d._children.forEach(collapse);
					d.children = null;
				}
			}

			function redraw() {
				svg.attr("transform",
				  "translate(" + d3.event.translate + ")"
				  + " scale(" + d3.event.scale + ")");
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
		       return [x,y]
			}
			
			function update(source) {			
				var depthChart = [];
				var depthY = [];
				var levelNames = [];
				var maxDepth = getDepth(root);
				for (var i=0;i < maxDepth;i++){
					depthChart.push(false);
					depthY.push(0);
					levelNames.push("");
				}
			
				console.log(levelNames);
				// Compute the new tree layout.
				
				var nodes = tree.nodes(root).reverse();
				var links = tree.links(nodes);
				// Normalize for fixed-depth.
							
				nodes.forEach(function (d) {
					//d.x = d.depth*20.0;//d.depth * 40*4/(getDepth(root));
				   d.y = d.depth * 160*4/(maxDepth);
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
				})
				    .on("click", click);
				
				nodeEnter.append("rect")
				    .attr("width",rectW) 
				    //function(d){
				    //	return rectW/(d.depth+1);
				    //	})
				    .attr("height", rectH)
				    .attr("stroke", "black")
				    .attr("stroke-width", 1)
				    .attr("id",function(d){
				    	return "rect_"+d.depth;
				    })
				    .style("fill", function (d) {
				    	console.log(d.depth + " **** " + selectedNode);
				    	return (d.depth == selectedNode) ? "lightsteelblue" : "#fff";
				    });
				
				if(updateFixed){
					nodeEnter.append("text")
					    .attr("x", rectW / 2)
					    .attr("y", rectH / 2)
					    .attr("dy", ".35em")
					    .attr("text-anchor", "middle")
					    .attr("id",function(d){
					    	return "loctext_"+d.depth;
					    	}
					    )
					    .text(function (d) {
					    	//if(d.depth > depthChart){
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
				    	return (d.depth == selectedNode) ? "lightsteelblue" : "#fff";
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
				
				// Stash the old positions for transition.
				nodes.forEach(function (d) {
				    d.x0 = d.x;
				    d.y0 = d.y;
				});
				
				if(updateFixed){
					svg.append("text")
						//.attr('x',)
						//.attr('y',".01px")
						.attr('text-anchor','middle')
						.attr('font-weight','bold')
						.attr('font-size','18px')
						.text('Products Enter Here')
						.attr("transform",function(d){
							return "translate("+(root.x+rectW/2)+","+(root.y - rectH/2) +")";
						});
					svg.append("text")
						//.attr('x',)
						//.attr('y',".01px")
						.attr('text-anchor','middle')
						.attr('font-weight','bold')
						.attr('font-size','18px')
						.text('Products End Here')
						.attr("transform",function(d){
							var depthHere = depthY[maxDepth-1];
							console.log("DY = " + depthHere);
							return "translate("+(root.x+rectW/2)+","+(depthHere + rectH*1.5) +")";
						});
					
						for(var i=0;i<depthY.length;i++){
							svg.append("text")
							//.attr('x',)
							//.attr('y',".01px")
							//.attr('text-anchor','middle')
							.attr('font-size','18px')
							.attr('id','levelname_'+i)
							.text(levelNames[i])
							.attr("transform",function(d){
								return "translate("+(root.x-width/2+rectW)+","+(depthY[i] + rectH/2) +")";
							});
						}
					}
				if(updateFixed){
					updateFixed=false;
				}	
			}
		
		
		//Toggle children on click.
		function click(d) {
//			if (d.children) {
//			    d._children = d.children;
//			    d.children = null;
//			} 
//			else {
//			    d.children = d._children;
//			    d._children = null;
//			}
			
			update(d);
		}
      }
    });
})(jQuery);

    

    	
    	
    