%rebase outer_wrapper title_slogan=_('Simulation Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId
<script src="{{rootPath}}static/hermes-ui-utils.js"></script>
<script src="{{rootPath}}static/vakata-jstree-841eee8/dist/jstree.min.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery.fileDownload.js"></script>
<script type="text/javascript" src="{{rootPath}}static/Highcharts-3.0.5/js/highcharts.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/vakata-jstree-841eee8/dist/themes/default/style.min.css"/>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/summary.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_availability_by_cohort.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/storage_utilization_by_level.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/transport_utilization_by_route.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_summary_grid.js"></script>
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
</style>

<div id="result_holder">
	<div id="results_tree">Loading Results Tree</div>
	<div id="results_summary_tabs">
		<p id="results_before">{{_("Please select a result from the menu on the left to display.")}}</p>
		<ul>
		</ul>
	</div>
</div>

<script>

//var tabList = [];

//$(function(){
	//$("#results_summary_tabs").tabs();
	
	//$("#results_summary_tabs").css("opacity",0);
	getResultsTree({{modelId}})
	.done(function(result){
		if(!result.success){
			alert(result.msg);
		}
		else{
			if(result.treeData.length == 0){
				$("#results_tree").text("{{_('There are Simulation Experiments.')}}");
			}
			else{
				$("#results_tree").jstree({
				    "core" : {'data': result.treeData },
				    'plugins':['wholerow','types','unique']
				})
				.on('changed.jstree',function(e,data){
					node_select = data.selected[0];
					node_instance = data.instance.get_node(node_select);
					if(node_instance.id.search('r_')>-1){
						$("#results_before").hide();
						$("#results_summary_tabs").results_tabs({
							rootPath:'{{rootPath}}'
						});
						$("#results_summary_tabs").fadeTo(500,1.0);
						var resultsMon = node_instance.id.replace('r_','');
						var modelId = parseInt(resultsMon.split("_")[0]);
						var resultsId = parseInt(resultsMon.split("_")[1]);
						$("#results_summary_tabs").results_tabs("add",modelId,resultsId,
																node_instance.original.tabText);
					}
				})
				.on('select_node.jstree',function(e,data){
					return data.instance.toggle_node(data.node);
				});
			}
		}
	});	

$(function(){
	window.addEventListener('resize',function(event){
		if($(window).width() > 900){
			$(".rs_summary").results_summary_page("grow");
		}
		else{
			$(".rs_summary").results_summary_page("shrink");
		}
	});
});

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
</script>