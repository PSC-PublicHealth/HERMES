%rebase outer_wrapper title_slogan=_('Simulation Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId
<!---
-->
<script type="text/javascript" src="{{rootPath}}static/jquery.fileDownload.js"></script>
<script src="{{rootPath}}static/hermes-ui-utils.js"></script>
<script src="{{rootPath}}static/vakata-jstree-841eee8/dist/jstree.min.js"></script>
<script src="{{rootPath}}static/d3/d3.min.js" charset="utf-8"></script>
<script src="{{rootPath}}static/dimple.v2.1.2/dimple.v2.1.2.min.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/vakata-jstree-841eee8/dist/themes/default/style.min.css"/>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/summary.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_availability_by_cohort.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/storage_utilization_by_level.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/transport_utilization_by_route.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_summary_grid.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/cost_summary_grid.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/cost_keypoints.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/results_tabs.js"></script>
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/hierarchical-charts/zoomable-treemap.js"></script>
<script src="{{rootPath}}static/hierarchical-charts/hierarchical-barcharts.js"></script>

<link rel="stylesheet" href='{{rootPath}}static/results-widgets/results-widgets.css'/> 
<style>
#results_holder{
	min-width:100%;
	max-width:100%;
	min-height:100%;
	max-height:100%;	
}
#results_tree{
	float:left;
	font-size:10px;
	max-width:30%;
	min-width:200px;
	max-height:500px;
	overflow-y:scroll;
	
}
#results_summary_tabs{
	float:left;
	min-width:500px;
	max-width:70%;
}
#results_before{
	font-size:18px;
	margin:20px 20px;
}
.res_del_button{
	font-size:8px;
}
</style>

<div id="result_holder">
	<div id="results_tree">Loading Results Tree</div>
	<div id="results_summary_tabs">
		<p id="results_before">{{_("Please select a result from the menu on the left to display.")}}</p>
		<ul>
		</ul>
	</div>
</div>

<div id="delete_confirm_dialog">{{_('Are you sure that you would like to delete this result?')}}</div>
<div id="delete_group_confirm_dialog">{{_('Are you sure that you would like to delete this entire group of results?')}}</div>

<script>

var show_result = true;
	getResultsTree({{modelId}})
	.done(function(result){
		if(!result.success){
			alert(result.msg);
		}
		else{
			if(result.treeData.length == 0){
				$("#results_tree").text("{{_('There are no simulation experiments.')}}");
			}
			else{
				$("#results_tree")
				.jstree({
				    "core" : {'data': result.treeData, 'check_callback':true },
				    'plugins':['types','unique']
				});
				
				
				$("#results_tree")
				.on('after_open.jstree',function(e,data){
					setupButtons();
				})
				.on('changed.jstree',function(e,data){
					node_select = data.selected[0];
					node_instance = data.instance.get_node(node_select);
					if(show_result){
						console.log("NodeInstance = " + node_instance);
						if(node_instance){
							if(node_instance.id.search('r_')>-1){
								$("#results_before").hide();
								$("#results_summary_tabs").results_tabs({
									rootPath:'{{rootPath}}'
								});
								$("#results_summary_tabs").fadeTo(500,1.0);
								var resultsMon = node_instance.id.replace('r_','');
								var modelId = parseInt(resultsMon.split("_")[0]);
								var resultsId = parseInt(resultsMon.split("_")[1]);
								var hasCosts = parseInt(resultsMon.split("_")[2]);
								var boolCosts = hasCosts == 1 ? true : false;
								$("#results_summary_tabs").results_tabs("add",modelId,resultsId,
																		node_instance.original.tabText,
																		boolCosts);
							}
						}
					}
					else{
						show_result=true;
					}
					
				})
				.on('select_node.jstree',function(e,data){
					return data.instance.toggle_node(data.node);
				});
			}
		}
	});	

$(function(){
	$("#delete_confirm_dialog").dialog({
		modal:true,
		autoOpen:false,
		buttons:{
			"{{_('Yes')}}":function(){
				$(this).dialog("close");
				var resId = $(this).data('resultsId');
				var modelId = $(this).data('modelId');
				var nodeId = $(this).data('nodeId');
				$.ajax({
					url:'{{rootPath}}edit/edit-results.json?id='+resId+'&oper=del',
					dataType:'json',
					success: function(result){
						if(!result.success){
							alert(result.msg);
						}
						else{
							var tree = $("#results_tree").jstree(true);
							
							//Get the appropriate node information
							var nodeToDelete = tree.get_selected();
							var groupNode = tree.get_node(tree.get_parent(nodeToDelete));
							var modelNode = tree.get_node(tree.get_parent(groupNode));
							
							tree.delete_node(nodeToDelete);
							// walk up the tree, in case there is nothing to show
							if(groupNode.children.length == 0){
								tree.delete_node(groupNode);
							}
							if(modelNode.children.length == 0){
								tree.delete_node(modelNode);
							}
							var $tabHolder = $("#results_summary_tabs");
							if ($tabHolder.hasClass('ui-tabs')) { // which means it has been initialized
								$("#results_summary_tabs").results_tabs("remove",modelId,resId);								
							}
							
							//Must reset the buttons that are currently being displayed
							setupButtons();
						}
					}
				});
			},
			"{{_('No')}}":function(){
				$(this).dialog("close");
			}
		},
		open: function(e,ui) {
			$(this)[0].onkeypress = function(e) {
				if (e.keyCode == $.ui.keyCode.ENTER) {
					e.preventDefault();
					$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
					}
			    };
		}
	});
	$("#delete_group_confirm_dialog").dialog({
		modal:true,
		autoOpen:false,
		buttons:{
			"{{_('Yes')}}":function(){
				$(this).dialog("close");
				var rgId = $(this).data('rgId');
				var modelId = $(this).data('modelId');
				var nodeId = $(this).data('nodeId');
				$.ajax({
					url:'{{rootPath}}edit/delete-results-group.json?rgId='+rgId,
					dataType:'json',
					success: function(result){
						if(!result.success){
							alert(result.msg);
						}
						else{
							var tree = $("#results_tree").jstree(true);
							
							//Get the appropriate node information
							var nodeToDelete = tree.get_selected();
							var modelNode = tree.get_node(tree.get_parent(nodeToDelete));
							var nTD = tree.get_node(tree.get_node(nodeToDelete));
							for(var i=0;i<nTD.children.length;i++){
								var id = nTD.children[i];
								var modelId = parseInt(id.split("_")[1]);
								var resultsId = parseInt(id.split("_")[2]);
								var $tabHolder = $("#results_summary_tabs");
								if ($tabHolder.hasClass('ui-tabs')) { // make sure it's been initialized
									$tabHolder.results_tabs("remove",modelId,resultsId);
									//resultNode = tree.get_node(nTD.children[i]);
									//tree.delete_node(resultNode);
									//console.log(resultNode.id);
								}
							}
							tree.delete_node(nodeToDelete);
							// walk up the tree, in case there is nothing to show
							
							if(modelNode.children.length == 0){
								tree.delete_node(modelNode);
							}
							//$("#results_summary_tabs").results_tabs("remove",modelId,resId);
							
							//Must reset the buttons that are currently being displayed
							setupButtons();
						}
					}
				});
			},
			"{{_('No')}}":function(){
				$(this).dialog("close");
				var tree=$("#results_tree").jstree(true);
				tree.open_node(tree.get_selected());
			}
		},
		open: function(e,ui) {
			$(this)[0].onkeypress = function(e) {
				if (e.keyCode == $.ui.keyCode.ENTER) {
					e.preventDefault();
					$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
					}
			    };
		}
	});
	
	window.addEventListener('resize',function(event){
		if($(window).width() > 900){
			$(".rs_summary").results_summary_page("grow");
		}
		else{
			$(".rs_summary").results_summary_page("shrink");
		}
	});
});

function setupButtons(){
	$("[id^=rg_del_but]").button();
	$("[id^=rg_del_but]").click(function(e){
		var rgMon = $(this).prop("id").replace("rg_del_but_",'');
		var node_id = rgMon;
		var modelId = parseInt(rgMon.split("_")[1]);
		var rGId = parseInt(rgMon.split("_")[2]);
		$("#delete_group_confirm_dialog").data('nodeId',node_id);
		$("#delete_group_confirm_dialog").data('modelId',modelId);
		$("#delete_group_confirm_dialog").data('rgId',rGId);
		$("#delete_group_confirm_dialog").dialog("open");
	});
	$("[id^=res_del_but]").button();
	$("[id^=res_del_but]").click(function(e){
		show_result= false;// this prevents the results from showing up when clicked
		var resultsMon = $(this).prop("id").replace("res_del_but_",'');
		var node_id = resultsMon;
		var modelId = parseInt(resultsMon.split("_")[1]);
		var resultsId = parseInt(resultsMon.split("_")[2]);
		$("#delete_confirm_dialog").data('nodeId',node_id);
		$("#delete_confirm_dialog").data('resultsId',resultsId);
		$("#delete_confirm_dialog").data('modelId',modelId);
		$("#delete_confirm_dialog").dialog("open");
	});
}
function getResultsTree(modelId){
	var thisURL = '{{rootPath}}json/results-tree-for-all-models'
	if(modelId > -1){
		thisURL = '{{rootPath}}json/results-tree-for-one-model?modelId='+modelId;
	}
	return $.ajax({
		url:thisURL,
		dataType:'json'
		}).promise();
};

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>
