;(function($){
	/// important variables

	var tree;
	var root;
	var baseSvg;
	var svgGroup;
	var diagonal;
	
	var margin = 100;
	var currentNode = null;
    // Calculate total nodes, max label length
    var totalNodes = 0;
    var maxLabelLength = 0;
    // variables for drag/drop
    var selectedNode = null;
    var draggingNode = null;
    // panning variables
    var panSpeed = 200;
    var panBoundary = 20; // Within 20px from edges will pan when dragging.
    // Misc. variables
    var i = 0;
    var duration = 750;
   
    // size of the diagram
    var viewerWidth = $(document).width()-margin*2;
    var viewerHeight = $(document).height()-300;
    
    jQuery.fn.d3Click = function () {
	  this.each(function (i, e) {
	    var evt = document.createEvent("MouseEvents");
	    evt.initMouseEvent("click", true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
	    e.dispatchEvent(evt);
	  });
	};
	
	function open_store_info_box(rootPath,modelId,storeId,storeName){
		var divIDName = "storeInfo_" + Math.random().toString(36).replace(/[^a-z]+/g,'');
		$.ajax({
			url: rootPath+'json/dialoghtmlforstore',
			dataType:'json',
			data:{name:divIDName,geninfo:1,utilinfo:0,popinfo:1,storedev:1,transdev:1,vacavail:0,fillratio:0,invent:0,availplot:0}
		})
		.done(function(result){
			if(!result.success){
				alert(result.msg);
			}
			else{
				$(document.body).append(result.htmlString);
				var meta_data = eval(divIDName + "_meta");
				populateStoreInfoDialog(rootPath,divIDName,meta_data,modelId,storeId,-1);
				$("#"+divIDName+"_dialog").dialog("option","title","Information for Location "+ storeName + "("+ storeId+")");
				$("#"+divIDName+"_dialog").dialog("open");
			}
		});
	}
	
	function open_route_info_box(rootPath,modelId,routeId){
		var divIDName = 'route_info_' + Math.random().toString(36).replace(/[^a-z]+/g,'');
		$.ajax({
			url: rootPath+'json/dialoghtmlforroute',
			dataType:'json',
			data:{name:divIDName,geninfo:1,utilinfo:0,tripman:0},
			success:function(result){
				if(!result.success){
					alert(result.msg);
				}
				else{
					$(document.body).append(result.htmlString);
					var meta_data = eval(divIDName + '_meta');
					populateRouteInfoDialog(rootPath,divIDName,meta_data,modelId,routeId,-1);
					$("#"+divIDName+"_dialog").dialog("option","title","Information for Route "+ routeId);
					$("#"+divIDName+"_dialog").dialog("open");
				}
			}	
		});
	};
	
	
	function toggleAllHere(d){
		if(d._children){
			$("#node_"+d.idcode).d3Click();
		}
			
		if(d.children){
			d.children.forEach(toggleAllHere);
		}
	};
		
		
	
	$.widget("collapsible-network-diagram.diagram",{
		options:{
			file: 'static/collapsible-network-diagram/readme.json',
			jsonUrl:'',
			jsonData:{},
			storeDialogDivID:'',
			rootPath:'',
			modelId:'',
			minWidth:500,
			minHeight:300,
			scrollable:false,
			resizable:false,
			hideRouteNames:false,
			hidePlaceNames:false,
			selectedNode: -1,
			hasChildrenColor:"steelblue",
			noChildrenColor:"#adf",
			trant: {
				title:'Collapsible Zoom Pan Network Diagram'
			}			
		},
		
		hideRouteNames: function(){
			$(".link text").css("visibility",'hidden');
			$(".nodeLoop").css("opacity",0);
			this.options.hideRouteNames = true;
		},
		
		showRouteNames: function(){
			$(".link text").css("visibility","visible");
			$(".nodeLoop").css("opacity",1);
			this.options.hideRouteNames = false;
		},
		hidePlaceNames: function(){
			$(".nodeText").css("opacity",0);
			this.options.hidePlaceNames = true;

		},
		
		showPlaceNames: function(){
			$(".nodeText").css("opacity",1);
			this.options.hidePlaceNames = false;
		},
		
		resetNewtork: function(){
		   treeData.children.forEach(toggleAll);
		},
		
		clickNode: function(idcode){
			$("#node_"+idcode).d3Click();
		},

		expandAll: function(){
			treeData.children.forEach(toggleAllHere);
		},

		_create: function(){
			trant = this.option.trant;
			
			var storeDialogID = this.options.storeDialogDivID;
			var modelId = this.options.modelId;
			var rootPath = this.options.rootPath;
			
			treeData = this.options.jsonData;
			
			this.containerID = $(this.element).attr('id');
			this.svgContainerID = this.containerID+"svgContainer";
			
			d3.select("#"+this.containerID).append("svgContainer")
				.attr("id",this.svgContainerID);
			
			//Stuff that will help with SVG rendering
			(function(){	
				var ua = navigator.userAgent,
						iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
						typeOfCanvas = typeof HTMLCanvasElement,
						nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
						textSupport = nativeCanvasSupport 
						&& (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
				//I'm setting this based on the fact that ExCanvas provides text support for IE
				//and that as of today iPhone/iPad current text support is lame
				labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
				nativeTextSupport = labelType == 'Native';
				useGradients = nativeCanvasSupport;
				animate = !(iStuff || !nativeCanvasSupport);
			})();
			
			var Log = {
			  elem: false,
			  write: function(text){
			    if (!this.elem) 
			      this.elem = document.getElementById('log');
			    this.elem.innerHTML = text;
			    this.elem.style.left = (500 - this.elem.offsetWidth / 2) + 'px';
			  }
			};
			
		    tree = d3.layout.tree()//.size([viewerHeight*10.0, viewerWidth*10.0]);
		
		    // define a d3 diagonal projection for use by the node paths later on.
		    diagonal = d3.svg.diagonal()
		        .projection(function(d) {
		            return [d.y, d.x];
		        });
		
		    // define the zoomListener which calls the zoom function on the "zoom" event constrained within the scaleExtents
		    var zoomListener = d3.behavior.zoom().scaleExtent([0.1, 3]).on("zoom", zoom);
		        // define the baseSvg, attaching a class for styling and the zoomListener
		    baseSvg = d3.select("#"+this.svgContainerID).append("svg")
		    		.attr("id","netSVG")
		    		.attr("width", viewerWidth)
		    		.attr("height", viewerHeight)
		    		.attr("class", "overlay")
		    		.call(zoomListener)
		    		.on('contextmenu',function(){
		    			d3.event.preventDefault();
		    		});
		    		
		    		
			var overCircle = function(d) {
		        selectedNode = d;
		        updateTempConnector();
		    };
		    var outCircle = function(d) {
		        selectedNode = null;
		        updateTempConnector();
		    };

    	    // Function to update the temporary connector indicating dragging affiliation
    	    var updateTempConnector = function() {
    	        var data = [];
    	        if (draggingNode !== null && selectedNode !== null) {
    	            // have to flip the source coordinates since we did this for the existing connectors on the original tree
    	            data = [{
    	                source: {
    	                    x: selectedNode.y0,
    	                    y: selectedNode.x0
    	                },
    	                target: {
    	                    x: draggingNode.y0,
    	                    y: draggingNode.x0
    	                }
    	            }];
    	        }
    	        var link = svgGroup.selectAll(".templink").data(data);

    	        link.enter().append("path")
    	            .attr("class", "templink")
    	            .attr("d", d3.svg.diagonal())
    	            .attr('pointer-events', 'none');

    	        link.attr("d", d3.svg.diagonal());

    	        link.exit().remove();
    	    };
		
		    dragListener = d3.behavior.drag()
		        .on("dragstart", function(d) {
		            if (d == root) {
		                return;
		            }
		            dragStarted = true;
		            nodes = tree.nodes(d);
		            d3.event.sourceEvent.stopPropagation();
		            // it's important that we suppress the mouseover event on the node being dragged. Otherwise it will absorb the mouseover event and the underlying node will not detect it d3.select(this).attr('pointer-events', 'none');
		        })
		        .on("drag", function(d) {
		            if (d == root) {
		                return;
		            }
		            if (dragStarted) {
		                domNode = this;
		                initiateDrag(d, domNode,tree);
		            }
		
		            // get coords of mouseEvent relative to svg container to allow for panning
		            relCoords = d3.mouse($('svg').get(0));
		            if (relCoords[0] < panBoundary) {
		                panTimer = true;
		                pan(this, 'left');
		            } else if (relCoords[0] > ($('svg').width() - panBoundary)) {
		
		                panTimer = true;
		                pan(this, 'right');
		            } else if (relCoords[1] < panBoundary) {
		                panTimer = true;
		                pan(this, 'up');
		            } else if (relCoords[1] > ($('svg').height() - panBoundary)) {
		                panTimer = true;
		                pan(this, 'down');
		            } else {
		                try {
		                    clearTimeout(panTimer);
		                } catch (e) {
		
		                }
		            }
		
		            d.x0 += d3.event.dy;
		            d.y0 += d3.event.dx;
		            var node = d3.select(this);
		            node.attr("transform", "translate(" + d.y0 + "," + d.x0 + ")");
		            updateTempConnector();
		        }).on("dragend", function(d) {
		            if (d == root) {
		                return;
		            }
		            domNode = this;
		            if (selectedNode) {
		                // now remove the element from the parent, and insert it into the new elements children
		                var index = draggingNode.parent.children.indexOf(draggingNode);
		                if (index > -1) {
		                    draggingNode.parent.children.splice(index, 1);
		                }
		                if (typeof selectedNode.children !== 'undefined' || typeof selectedNode._children !== 'undefined') {
		                    if (typeof selectedNode.children !== 'undefined') {
		                        selectedNode.children.push(draggingNode);
		                    } else {
		                        selectedNode._children.push(draggingNode);
		                    }
		                } else {
		                    selectedNode.children = [];
		                    selectedNode.children.push(draggingNode);
		                }
		                // Make sure that the node being added to is expanded so user can see added node is correctly moved
		                expand(selectedNode);
		                sortTree();
		                endDrag();
		            } else {
		                endDrag();
		            }
		        });
		    // A recursive helper function for performing some setup by walking through all nodes

		    
		
		    // Append a group which holds all nodes and which the zoom Listener can act upon.
		    svgGroup = baseSvg.append("g");
		    //this.updateFn = update;
		    // Define the root
		    root = treeData;
		    root.x0 = viewerHeight / 2;
		    root.y0 = 0;
			function toggle(d) {
				if (d.children) {
					d._children = d.children;
					d.children = null;
				} 
				else {
					d.children = d._children;
					d._children = null;
				}
			};
			
			function toggleAll(d){
				if (d.children) {
				    d.children.forEach(toggleAll);
				    toggle(d);
				}
			};
		    function visit(parent, visitFn, childrenFn) {
		    	if (!parent) return;

		        visitFn(parent);

		        var children = childrenFn(parent);
		        if (children) {
		            var count = children.length;
		            for (var i = 0; i < count; i++) {
		                visit(children[i], visitFn, childrenFn);
		            }
		        }
		    };
		    
		    // Call visit function to establish maxLabelLength
		    visit(treeData, function(d) {
		        totalNodes++;
		        maxLabelLength = Math.max(d.name.length, maxLabelLength);

		    }, function(d) {
		        return d.children && d.children.length > 0 ? d.children : null;
		    });


		    // sort the tree according to the node names

		    function sortTree() {
		        tree.sort(function(a, b) {
		            return b.name.toLowerCase() < a.name.toLowerCase() ? 1 : -1;
		        });
		    }
		    // Sort the tree initially incase the JSON isn't in a sorted order.
		    sortTree();

		    // TODO: Pan function, can be better implemented.

		    function pan(domNode, direction) {
		        var speed = panSpeed;
		        if (panTimer) {
		        	clearTimeout(panTimer);
		            translateCoords = d3.transform(svgGroup.attr("transform"));
		            if (direction == 'left' || direction == 'right') {
		                translateX = direction == 'left' ? translateCoords.translate[0] + speed : translateCoords.translate[0] - speed;
		                translateY = translateCoords.translate[1];
		            } else if (direction == 'up' || direction == 'down') {
		                translateX = translateCoords.translate[0];
		                translateY = direction == 'up' ? translateCoords.translate[1] + speed : translateCoords.translate[1] - speed;
		            }
		            scaleX = translateCoords.scale[0];
		            scaleY = translateCoords.scale[1];
		            scale = zoomListener.scale();
		            svgGroup.transition().attr("transform", "translate(" + translateX + "," + translateY + ")scale(" + scale + ")");
		            d3.select(domNode).select('g.node').attr("transform", "translate(" + translateX + "," + translateY + ")");
		            zoomListener.scale(zoomListener.scale());
		            zoomListener.translate([translateX, translateY]);
		            panTimer = setTimeout(function() {
		                pan(domNode, speed, direction);
		            });
		        }
		    }

		    // Define the zoom function for the zoomable tree
		    function zoom() {
		        svgGroup.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
		    };


		    

		    function resize() {
		    	x = window.innerWidth - margin*2;
		    	y = window.innerHeight - 400;
		    	svgGroup.attr("width",x).attr("height",y);
		    };
		    
		    function initiateDrag(d, domNode, tree) {
		        draggingNode = d;
		        d3.select(domNode).select('.ghostCircle').attr('pointer-events', 'none');
		        d3.selectAll('.ghostCircle').attr('class', 'ghostCircle show');
		        d3.select(domNode).attr('class', 'node activeDrag');

		        svgGroup.selectAll("g.node").sort(function(a, b) { // select the parent and sort the path's
		            if (a.id != draggingNode.id) return 1; // a is not the hovered element, send "a" to the back
		            else return -1; // a is the hovered element, bring "a" to the front
		        });
		        // if nodes has children, remove the links and nodes
		        if (nodes.length > 1) {
		            // remove link paths
		            links = tree.links(nodes);
		            nodePaths = svgGroup.selectAll("path.link")
		                .data(links, function(d) {
		                    return d.target.id;
		                }).remove();
		            // remove child nodes
		            nodesExit = svgGroup.selectAll("g.node")
		                .data(nodes, function(d) {
		                    return d.id;
		                }).filter(function(d, i) {
		                    if (d.id == draggingNode.id) {
		                        return false;
		                    }
		                    return true;
		                }).remove();
		        }

		        // remove parent link
		        parentLink = tree.links(tree.nodes(draggingNode.parent));
		        svgGroup.selectAll('path.link').filter(function(d, i) {
		            if (d.target.id == draggingNode.id) {
		                return true;
		            }
		            return false;
		        }).remove();

		        dragStarted = null;
		    };

		    function endDrag() {
		        selectedNode = null;
		        d3.selectAll('.ghostCircle').attr('class', 'ghostCircle');
		        d3.select(domNode).attr('class', 'node');
		        // now restore the mouseover event or we won't be able to drag a 2nd time
		        d3.select(domNode).select('.ghostCircle').attr('pointer-events', '');
		        updateTempConnector();
		        if (draggingNode !== null) {
		            update(root,tree);
		            centerNode(draggingNode);
		            draggingNode = null;
		        }
		    };

		    // Helper functions for collapsing and expanding nodes.

		    function collapse(d) {
		        if (d.children) {
		            d._children = d.children;
		            d._children.forEach(collapse);
		            d.children = null;
		        }
		    };

		    function expand(d) {
		        if (d._children) {
		            d.children = d._children;
		            d.children.forEach(expand);
		            d._children = null;
		        }
		    };

		    // Function to center node when clicked/dropped so node doesn't get lost when collapsing/moving with large amount of children.

		    function centerNode(source) {
		        scale = zoomListener.scale();
		        x = -source.y0;
		        y = -source.x0;
		        x = x * scale + parseInt(baseSvg.style('width')) / 4;
		        y = y * scale + parseInt(baseSvg.style('height')) / 2;
		        if (y < 120) y = 120;
		        d3.select('g').transition()
		            .duration(duration)
		            .attr("transform", "translate(" + x + "," + y + ")scale(" + scale + ")");
		        zoomListener.scale(scale);
		        zoomListener.translate([x, y]);
		    };

		    // Toggle children function

		    function toggleChildren(d) {
		        if (d.children) {
		            d._children = d.children;
		            d.children = null;
		        } else if (d._children) {
		            d.children = d._children;
		            d._children = null;
		        }
		        return d;
		    };

		    // Toggle children on click.

		    function click(d) {
		        //if (d3.event.defaultPrevented) return; // click suppressed // Causes Chrome to stop responding after a while and is not necessary
		        d = toggleChildren(d);
		        update(d);
		        centerNode(d)
		        currentNode = d;
		    };
	
		    function rightClickStore(d) {
	    	   d3.event.preventDefault();
	    	   open_store_info_box(rootPath,modelId,d.idcode,d.name);   
		    }
		   function rightClickLink(d){
			   d3.event.preventDefault();
			   if(d.hasOwnProperty('target')){
				   if(d.target.supRouteId == 'none'){
					   open_route_info_box(rootPath,modelId,d.source.supRouteId);
				   }   
				   else{
					   open_route_info_box(rootPath,modelId,d.target.supRouteId);
				   }
			   }
			   else{
				   loopName = d.name.replace(" Loop","")
				   open_route_info_box(rootPath,modelId,loopName);
			   }
				   
			};
		   
			function update(source) {
				        // Compute the new height, function counts total children of root node and sets tree height accordingly.
				        // This prevents the layout looking squashed when new nodes are made visible or looking sparse when nodes are removed
				        // This makes the layout more consistent.
				        console.log(source);
				        var levelWidth = [1];
				        var childCount = function(level, n) {
				
				            if (n.children && n.children.length > 0) {
				                if (levelWidth.length <= level + 1) levelWidth.push(0);
				
				                levelWidth[level + 1] += n.children.length;
				                n.children.forEach(function(d) {
				                    childCount(level + 1, d);
				                });
				            }
				        };
				        childCount(0, root);
				        var newHeight = d3.max(levelWidth) * 50; // 25 pixels per line  
				        tree = tree.size([newHeight, viewerWidth]);
				
				        // Compute the new tree layout.
				        var nodes = tree.nodes(root).reverse(),
				            links = tree.links(nodes);
				
				        // Set widths between levels based on maxLabelLength.
				        nodes.forEach(function(d) {
				            d.y = (d.depth * (maxLabelLength * 10)); //maxLabelLength * 10px
				            // alternatively to keep a fixed scale one can set a fixed depth per level
				            // Normalize for fixed-depth by commenting out below line
				        	//d.y = (d.depth * 500);//500px per level.
				        	//d.x = (100);
				        });
				
				        // Update the nodes
				        node = svgGroup.selectAll("g.node")
				            .data(nodes, function(d) {
				                return d.id || (d.id = ++i);
				            });
				
				        // Enter any new nodes at the parent's previous position.
				        var nodeEnter = node.enter().append("g")
				            //.call(dragListener)
				            .attr("class", "node")
				            .attr("transform", function(d) {
				                return "translate(" + source.y0 + "," + source.x0 + ")";
				            })
				            .attr('id',function(d){
				            	if(d.level==9999)
				            		return "nodeloop_" + d.name;
				            	else
				            		return "node_" + d.idcode;
				            })
				            .on('click', click)
				            //.on('contextmenu',rightClick);
				           
				        d3.selectAll("[id^=node_]").append("circle")
				            .attr('class', function(d){
				            	if (d.level == 9999)
				            		return 'nodeCircle_loop';
				            	else
				            		return 'nodeCircle';
				            })
				            .attr('id',function(d){
				            	return "nodeCircle_" + d.idcode;
				            })
				            .attr("r", function(d){
				            	if (d.level == 9999){
				            		return 0.001;
				            	}
				            	else {
				            		return 20.0/(d.level+1);
				            	}
				            	})
				            .style("fill", function(d) {
				            	console.log("level = " + d.level);
				            	if (d.level > 10){
				            		return "black";
				            	}
				            	else if (d._children) {
				            		return "lightsteelblue";
				            	}
				            	else {
				            		return "#fff";
				            	}
				            })
				            .style("stroke","lightsteelblue")
				            .style("stroke-width","1.5px")
				            .on('contextmenu',rightClickStore);
				            
				                //return d._children ? "lightsteelblue" : "#fff";
			
				
				        d3.selectAll('[id^=nodeloop]').append("image")
				        	.attr('class','nodeImage')
				        	.attr('id',function(d){
				        		return "nodeImage_"+d.idcode
				        	})
				        	.attr("xlink:href", function(d){
				        		if(d.level == 9999)
				        			return rootPath+'static/images/loop.png';
				        	})
				        	.attr("x","-10px")
				        	.attr("y","-10px")
				        	.attr("width","20px")
				        	.attr("height","20px")
				        	.on('contextmenu',rightClickLink);
				        
				        nodeEnter.append("text")
				            .attr("x", function(d) {
				            	return d.level+100;
				               //return d.children || d._children ? -(50.0/d.level) -10 : 10 + (50.0/d.level);
				            })
				            .attr("dy", ".35em")
				            .style("font-size","10px")
				            .attr('class', function(d){
				            	if(d.level==9999)
				            		return 'nodeLoop';
				            	else
				            		return 'nodeText';
				            })				      
				            .attr("text-anchor", function(d) {
				            	return "middle";
				                return d.children || d._children ? "end" : "start";
				            })
				            .style('opacity',function(d){
				            	if(d.level==9999){
				            		if($("#collapsible-network-diagram").diagram('option','hideRouteNames'))
				            			return 0;
				            		else
				            			return 1;
				            	}
				            	else{
				            		if($("#collapsible-network-diagram").diagram('option','hidePlaceNames'))
				            			return 0;
				            		else
				            			return 1;
				            	}	            	
				            })
				            .text(function(d) {
				                return d.name;
				            })
				            .style("fill-opacity", 0);
				
				//        // phantom node to give us mouseover in a radius around it
				//        nodeEnter.append("circle")
				//            .attr('class', 'ghostCircle')
				//            .attr("r", 30)
				//            .attr("opacity", 0.2) // change this to zero to hide the target area
				//        .style("fill", "red")
				//            .attr('pointer-events', 'mouseover')
				//            .on("mouseover", function(node) {
				//                overCircle(node);
				//            })
				//            .on("mouseout", function(node) {
				//                outCircle(node);
				//            });
				
				        // Update the text to reflect whether node has children or not.
				        node.select('text')
				            .attr("x", function(d){
				            	if(d.level == 9999){
				            		return 40;
				            	}
				            	else{
				            		return 0;
				            	}
				            })
				            .attr("y",function(d){
				            	if (d.level == 9999)
				            		return 0;
				            	else	
				            		return 20/(d.level+1)+10
				            })
				            .attr("text-anchor",function(d){
				            	if (d.level==9999)
				            		return "start";
				            	else
				            		return "middle";
				            })
				            //function(d) {
				            	
//				            	if (d.level == 9999){
//				            		return 3;
//				            		return (15.0/(3))+10;
//				            	}
//				            	else{
//				            		return 0;
//				            		return d.children || d._children ? (15.0/(1+d.level)) +10 : 10 + (15.0/(1+d.level)); 
//				            	}
//				            })
//				            .attr("visibility",function(){
//				            	if($("collapsible-network-diagram").diagram('option','hidePlaceNames'))
//				            		return "hidden";
//				            	else
//				            		return "visible";
//				            })
				            //.attr("text-anchor", "start")
				            //function(d) {
				            //    return d.children || d._children ? "start" : "start";
				            //})
				            .text(function(d) {
				            	return d.name;
				            });
				
				        // Change the circle fill depending on whether it has children and is collapsed
				        node.select("circle.nodeCircle")
				            //.attr("r", 4.5)
				            .style("fill", function(d) {
				            	if (d._children){
				            		if (d.level == 9999){
				            			return "black";
				            		}
				            		else {
				            			return "lightsteelblue";
				            		}
				            	}
				            	else{
				            		return "#fff";
				            	}
				                //return d._children ?  : "#fff";
				            });
				
				        // Transition nodes to their new position.
				        var nodeUpdate = node.transition()
				            .duration(duration)
				            .attr("transform", function(d) {
				                return "translate(" + d.y + "," + d.x + ")";
				            });
				
				        // Fade the text in
				        nodeUpdate.select("text")
				            .style("fill-opacity", 1);
				
				        // Transition exiting nodes to the parent's new position.
				        var nodeExit = node.exit().transition()
				            .duration(duration)
				            .attr("transform", function(d) {
				                return "translate(" + source.y + "," + source.x + ")";
				            })
				            .remove();
				
				        //nodeExit.select("circle")
				            //.attr("r", 1);
				
				        nodeExit.select("text")
				            .style("fill-opacity", 0);
				
				        // Update the links
				        var link = svgGroup.selectAll("path.link")
				            .data(links, function(d) {
				                return d.target.id;
				            });
				        
				        var linktext = svgGroup.selectAll("g.link")
				        		.data(links,function(d){
				        			return d.target.id;
				        		});
				        
				        var link2 = svgGroup.selectAll("path.link")
				        		.data(links,function(d){
				        			return d.target.id;
				        		});
				        
				        linktext.enter()
				        	.insert("g")
				        	.attr("class","link")
				        	.append("text")
				        	.attr("dy",".35em")
				        	.style("font=size","10px")
				        	.attr("text-anchor","middle")
				        	.text(function(d){
				        		if((d.target.supRouteId == "none")||(d.target.level == 9999)){
				        			return "";
				        		}
				        		else{
				        			return d.target.supRouteId;
				        		}
				        	})
				        	.on('contextmenu',rightClickLink);
				        
				        
				        // Enter any new links at the parent's previous position.
				        link.enter().insert("path", "g")
				            .attr("class", "link")
				            .style("fill","none")
				            .style("stroke","#ccc")
				            .style("stroke-width","1.5px")
				            .style("cursor","pointer")
				            .attr("d", function(d) {
				                var o = {
				                    x: source.x0,
				                    y: source.y0
				                };
				                return diagonal({
				                    source: o,
				                    target: o
				                });
				            });
				            //.on('contextmenu',rightClickLink);
				           
				        // Enter any new links at the parent's previous position.
				        link2.enter().insert("path", "g")
				            .attr("class", "link2")
				            .style("fill","none")
				            .style("stroke","#fff")
				            .style("stroke-width","15.0px")
				            .style("cursor","pointer")
				            .style("opacity",0.001)
				            .attr("d", function(d) {
				                var o = {
				                    x: source.x0,
				                    y: source.y0
				                };
				                return diagonal({
				                    source: o,
				                    target: o
				                });
				            })
				            .on('contextmenu',rightClickLink);
				               
				        // Transition links to their new position.
				        linktext.transition()
				            .duration(duration)
				            .attr("transform",function(d){
				            	return "translate(" + ((d.source.y + d.target.y) / 2) + ","
				            					    + ((d.source.x + d.target.x) / 2) + ")";
				            });
				        
				        link.transition()
				        	.duration(duration)
				        	.attr("d",diagonal);
				        
				        link2.transition()
				        	.duration(duration)
				        	.attr("d",diagonal);
				        
				        // Transition exiting nodes to the parent's new position.
				        link.exit().transition()
				            .duration(duration)
				            .attr("d", function(d) {
				                var o = {
				                    x: source.x,
				                    y: source.y
				                };
				                return diagonal({
				                    source: o,
				                    target: o
				                });
				            })
				            .remove()
				        
				        link2.exit().transition()
				            .duration(duration)
				            .attr("d", function(d) {
				                var o = {
				                    x: source.x,
				                    y: source.y
				                };
				                return diagonal({
				                    source: o,
				                    target: o
				                });
				            })
				            .remove()
				        linktext.exit().transition().remove();
				        
				        // Stash the old positions for transition.
				        nodes.forEach(function(d) {
				            d.x0 = d.x;
				            d.y0 = d.y;
				        });
				    }// end update

		    function toggleAll(d) {
		    	if (d.children) {
		    		d.children.forEach(toggleAll);
		    		toggle(d);
		        }
		     }
		    
		    this.toggleAllFn = toggleAll;
		    root.children.forEach(toggleAll);
		    //toggle(root.children[1]);
		    // Layout the tree initially and center on the root node.
		    update(root);
		    centerNode(root);
		    currentNode = root;
		    
		    
			window.addEventListener('resize',function(event){
		    	var wH = window.innerHeight-300;
		    	var wW = window.innerWidth - margin*2;
		    	var bH = parseInt(baseSvg.style("height"));
		    	var bW = parseInt(baseSvg.style("width"));
		    	
		    	//console.log(wH);
		    	//console.log(bH);
		    	
		    	baseSvg.attr("width",wW).attr("height",wH);
		    	console.log("resizing");
		    	centerNode(currentNode);
	    	
	    
			});
		
		//Toggle children
	}
});
})(jQuery);