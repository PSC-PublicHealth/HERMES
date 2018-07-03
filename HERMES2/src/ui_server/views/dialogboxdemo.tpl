%rebase outer_wrapper title_slogan=_("GeoJson Test"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultId=resultsId

<!---
-->

<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/d3/topojson.v1.min.js"></script>
<script src="{{rootPath}}static/queue.min.js"></script>
<script src="{{rootPath}}static/hermes_info_dialogs.js"></script>
<script src="{{rootPath}}static/rainbowvis.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/rickshaw-master/rickshaw.css"/>
<link rel="stylesheet" href="{{rootPath}}static/linechart-widgets/linechart.css"/>
<script src="{{rootPath}}static/rickshaw-master/rickshaw.js"></script>
<script src="{{rootPath}}static/linechart-widgets/linechart.js"></script>
<script src="{{rootPath}}static/dimple.v2.1.2/dimple.v2.1.2.min.js"></script>
<script src="{{rootPath}}static/barchart-widgets/vaccine_availability_barchart.js"></script>
<script> 
var dialogBoxName = "model_store_info";
var dialogNoResName = "model_store_noRes";
var dialogRouteResName = "model_route_info";
</script>

<button type="button" id="demo_button">Dialog</button>
<button type="button" id="no_results_demo">No Results</button>
<button type="button" id="route_res_demo">Route Dialog</button>

<script>
$(function() {
	$.ajax({
		url: '{{rootPath}}json/dialoghtmlforstore',
		dataType:'json',
		data:{name:'model_store_info',geninfo:1,utilinfo:1,popinfo:1,storedev:1,transdev:1,vacavail:1,fillratio:1,invent:1,availplot:1},
		success:function(data){
			console.log(data.htmlString);
			$(document.body).append(data.htmlString);
		}
	})
});

$(function() {
	$.ajax({
		url: '{{rootPath}}json/dialoghtmlforstore',
		dataType:'json',
		data:{name:dialogNoResName,geninfo:1,utilinfo:0,popinfo:1,storedev:1,transdev:1,vacavail:0,fillratio:0,invent:0,availplot:0},
		success:function(data){
			console.log(data.htmlString);
			$(document.body).append(data.htmlString);
		}
	})
});

$(function() {
	$.ajax({
		url: '{{rootPath}}json/dialoghtmlforroute',
		dataType:'json',
		data:{name:dialogRouteResName,geninfo:1,utilinfo:1,tripman:1},
		success:function(data){
			console.log(data.htmlString);
			$(document.body).append(data.htmlString);
		}
	})
});


$(function() {
	
	//$('#ajax_busy_image').show();
});

$(function(){
//$('#model_store_info_dialog').ready( function(){
	var btn = $("#demo_button");
	btn.button();
	btn.click(function() {
		if($("#model_store_info_dialog").length > 0){
			if ($("#model_store_info_dialog").is(':ui-dialog')) {
				$("#model_store_info_dialog").dialog('close');
			}
			var meta_data = eval(dialogBoxName+"_meta");
			var resId = -1;
			if (meta_data['getResults'] == true){ resId = {{resultsId}};}
			populateStoreInfoDialog("{{rootPath}}","model_store_info",meta_data,"{{modelId}}",'{{storeId}}',resId);
			$("#model_store_info_dialog").dialog("option","title","Information for Location " + '{{storeId}}');
			$("#model_store_info_dialog").dialog("open");
		}
	});
});
$(function(){
	//$('#model_store_info_dialog').ready( function(){
		var btn = $("#no_results_demo");
		btn.button();
		btn.click(function() {
			if($("#"+dialogNoResName+"_dialog").length > 0){
				if ($("#"+dialogNoResName+"_dialog").is(':ui-dialog')) {
					$("#"+dialogNoResName+"_dialog").dialog('close');
				}
				var meta_data = eval(dialogNoResName+"_meta");
				var resId = -1;
				if (meta_data['getResults'] == true){ resId = {{resultsId}};}
				populateStoreInfoDialog("{{rootPath}}",dialogNoResName,meta_data,"{{modelId}}",'{{storeId}}',resId);
				$("#"+dialogNoResName+"_dialog").dialog("option","title","Information for Location " + '{{storeId}}');
				$("#"+dialogNoResName+"_dialog").dialog("open");
			}
		});
	});

//});

$(function(){
	var btn = $("#route_res_demo");
	btn.button();
	btn.click(function() {
		if($("#"+dialogRouteResName+"_dialog").length > 0){
			if ($("#"+dialogRouteResName+"_dialog").is(':ui-dialog')) {
				$("#"+dialogRouteResName+"_dialog").dialog('close');
			}
			var meta_data = eval(dialogRouteResName+"_meta");
			var resId = -1;
			if (meta_data['getResults'] == true){ resId = {{resultsId}};}
			populateRouteInfoDialog("{{rootPath}}",dialogRouteResName,meta_data,"{{modelId}}",'{{routeId}}',resId);
			$("#"+dialogRouteResName+"_dialog").dialog("option","title","Information for Route " + '{{routeId}}');
			$("#"+dialogRouteResName+"_dialog").dialog("open");
		}
	});
});

function doneLoading(){
	//$('#ajax_busy_image').hide();
}

</script>
