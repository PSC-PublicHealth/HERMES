%rebase outer_wrapper title_slogan=slogan, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<h3>{{_('Click on a name to expand that part of the network.  Right-click on a name for more detailed information.')}}</h3>

<div id="infovis" height=500 width=500"></div>

<div id="log"></div>
<div id="model_store_info_dialog" title="This should get replaced"></div>

<script>

$(function() {
	$("#model_store_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

(function() {
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

var jsonurl = "{{rootPath}}json/model-structure-tree"; 

function init(json){ 

	//START Create a new Space Tree instance 
	var st = new $jit.ST({ 
        //id of viz container element
        injectInto: 'infovis',
        height: 300, // or it gets flattened to zero height
        //set duration for the animation
        duration: 400,
        //set animation transition type
        transition: $jit.Trans.Quart.easeInOut,
        //set distance between node and its children
        //levelDistance: 50,
        levelsToShow: 1,
		orientation: 'top',
		Events: {
            enable: true,
            onRightClick: function (node, eventInfo, e, win) {
                if (node)
                {
					$.getJSON('json/model-store-info',{nodeId:node.id, modelId:{{modelId}}})
					.done(function(data) {
						$("#model_store_info_dialog").html(data['htmlstring']);
						$("#model_store_info_dialog").dialog('option','title',data['title']);
						$("#model_store_info_dialog").dialog("open");		
					})
  					.fail(function(jqxhr, textStatus, error) {
  						alert("Error: "+jqxhr.responseText);
					});
                   
                }
            }
        },
        //enable panning
        Navigation: {
          enable:true,
          panning:true
        },
        //set node and edge styles
        //set overridable=true for styling individual
        //nodes or edges
        Node: {
            autoHeight: true,
            autoWidth: true,
            type: 'rectangle',
            color: '#888',
            overridable: true
        },
        
        Edge: {
            type: 'bezier',
            overridable: true
        },
        
        onBeforeCompute: function(node){
            Log.write("loading " + node.name);
        },
        
        onAfterCompute: function(){
            Log.write("done");
        },
        
        //This method is called on DOM label creation.
        //Use this method to add event handlers and styles to
        //your node.
        onCreateLabel: function(label, node){
            label.id = node.id;            
            label.innerHTML = node.name;
            if (!node.data.leaf) {
                label.onclick = function(e){
                    st.onClick(node.id);
                };
            };
            //set label styles
            var style = label.style;
            style.cursor = 'pointer';
            style.color = '#333';
            style.textAlign= 'center';
            style.paddingTop = '0.1em';
            style.paddingLeft = '0.1em';
        },
        
        //This method is called right before plotting
        //a node. It's useful for changing an individual node
        //style properties before plotting it.
        //The data properties prefixed with a dollar
        //sign will override the global node style properties.
        onBeforePlotNode: function(node){
            //add some color to the nodes in the path between the
            //root node and the selected node.
            if (node.data.isstore) {
                if (node.data.leaf) {
                    node.data.$dim = node.data.$width;
                    //node.data.$type = 'triangle';
            	    node.data.$type = 'rectangle';
                    node.data.$color = "#77f";                    
                }
                else {
            	    node.data.$type = 'rectangle';
            	}
            } 
            else {
                if (node.name.length == 1) {
                    node.data.$dim = node.data.$height;
                    node.data.$type = 'circle';
                }
                else node.data.$type = 'ellipse';
            }
            if (node.selected) {
                node.data.$color = "#ff7";
            }
        },
        //This method is called right before plotting
        //an edge. It's useful for changing an individual edge
        //style properties before plotting it.
        //Edge data proprties prefixed with a dollar sign will
        //override the Edge global style properties.
        onBeforePlotLine: function(adj){
            if (adj.nodeFrom.selected && adj.nodeTo.selected) {
                adj.data.$color = "#eed";
                adj.data.$lineWidth = 3;
            }
            else {
                delete adj.data.$color;
                delete adj.data.$lineWidth;
            }
        },
        //Add a request method for requesting on-demand json trees.   
		//This method gets called when a node  
		//is clicked and its subtree has a smaller depth  
		//than the one specified by the levelsToShow parameter.  
		//In that case a subtree is requested and is added to the dataset.  
		//This method is asynchronous, so you can make an Ajax request for that  
		//subtree and then handle it to the onComplete callback.  
		//
		// The value of level seems to be unreliable here.
		request: function(nodeId, level, onComplete) {  
			$.getJSON(jsonurl,{nodeId:nodeId, level:level, nlevels:1, modelId:{{modelId}}})
			.done(function(data) {
				onComplete.onComplete(nodeId, data);    
			})
  			.fail(function(jqxhr, textStatus, error) {
  				alert("Error: "+jqxhr.responseText);
			});
		}
        
    });
    //load json data
    st.loadJSON(json);
    //compute node positions and layout
    st.compute();
    //emulate a click on the root node.
    st.onClick(st.root);
    //end

}//END of init() function 

//ajax call 
$.getJSON(jsonurl,{modelId:{{modelId}},level:0,nlevels:1})
	.done(function(data) {
		init(data); //this line will call init function with JSON loaded after this call 
	})
  	.fail(function(jqxhr, textStatus, error) {
  		alert('{{_("Error: ")}}'+jqxhr.responseText);
	});

</script>
 