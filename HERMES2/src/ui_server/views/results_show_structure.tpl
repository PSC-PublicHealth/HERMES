%rebase outer_wrapper title_slogan=_("Network Visualization"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultId=resultsId
<!---
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
-->
<span class="show_title">{{_('Supply Chain Network Results Explorer')}}<br></span>
<span class="show_note">{{_('Click on a circle to see its locations to which it ships.  Left click on a location or route to get more detailed information.')}}
	{{_("Choose different outputs under visualization options to plot them on the diagram.")}}</span>

<script src="{{rootPath}}static/d3/d3.min.js" charset="utf-8"></script>
<script src="{{rootPath}}static/hermes_info_dialogs.js"></script>
<script type="text/javascript" src='{{rootPath}}static/Highcharts-3.0.5/js/highcharts.js'></script>
<script src="{{rootPath}}static/collapsible-network-diagram/collapsible-network-diagram.js"></script>
<script src="{{rootPath}}static/saveSvgAsPng-gh-pages/saveSvgAsPng.js"></script>
<script src="{{rootPath}}static/jquery.corner.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/collapsible-network-diagram/collapsible-network-diagram.css"/>

<script>
function updateNetworkDiagram(){
	getModelJson().done(function(result){
		if (!result.success){
			alert(result.msg);
		}
		else{
			//$("#collapsible-network-diagram").remove();
			//$("#model_show_diagram").append("<div id='collapsible-network-diagram'/>");
			$("#collapsible-network-diagram").diagram({
				jsonData:result,
				storeDialogDivID:'model_store_info',
				rootPath:'{{rootPath}}',
				modelId:'{{modelId}}',
				resultsId:'{{resultsId}}',
				resizeOn:true
				//jsonUrl:'{{rootPath}}json/model-structure-tree-d3?modelId={{modelId}}'
			});
			$("#tooldiv").show();
		}
	});
};

function getModelJson(){
	return $.ajax({
		url:'{{rootPath}}json/model-structure-tree-d3?modelId={{modelId}}',
		dataType:'json'
	}).promise();
};
</script>
<style>
.show_title{
	font-size:24px;
	font-weight:bold;
}
.show_note{
	font-size:14px;
}
#tooldiv{
	float:left;
	position: absolute;
	top:150px;
	background-color:#45474A;
	padding:15px;
	z-index:5;
	opacity:.20;
	display:none;
}

#model_show_ui_holder{
	min-height:100%;
	min-width:100%;
}
#model_show_diagram{
	min-height:100%;
	min-width:100%;
}
#collapsible-network-diagram{
	max-height:100%;
	min-height:100%
	max-width:100%;
	min-width:100%;
}
.toolbox-head{
	color:#ffffff;
	font-size:12px;
	pointer:none;
	margin-bottom:20px;
}
.toolbox-item{
	color:#ffffff;
	pointer:none;
	font-size:10px;
}
.tr-tb{
	display:none;
}
</style>

<div id="tooldiv">

<table style="padding:0px;margin:0px;">
<tr colspan=2>
	<td>
		<span class="toolbox-head">Visuailization Options</span>
	</td>
<tr class="tr-tb">
	<td>
		<span class="toolbox-item">Show Location Labels: </span>
	</td>
	<td>
		<span class="toolbox-item"><input type="checkbox" id="show_loc_labels" value="On" checked/></span>
	</td>
</tr>
<tr class="tr-tb">
	<td>
		<span class="toolbox-item">Show Route Labels: </span>
	</td>
	<td>
		<span class="toolbox-item"><input type="checkbox" id="show_route_labels" value="On" checked/><span>
	</td>
</tr>
<!--<tr>
	<td>
	<span class="toolbox-item">Save as PNG Image: </span>
	</td>
	<td>
		<input type='button' id="save_as_png" value="save">
	</td>
</tr>-->
	
</table>
</div>

<div id="model_show_ui_holder">
	<div id="collapsible-network-diagram">
		<script>
		</script>
	</div>
</div>

<div id="log"></div>
<script>
$(function(){
	$("#tooldiv").corner();
	$("#tooldiv").mouseover(function(){
		$(".tr-tb").show();
		$("#tooldiv").stop().fadeTo(100,1.0);
	});
	$("#tooldiv").mouseout(function(){
		$(".tr-tb").hide();
		$("#tooldiv").stop().fadeTo(100,0.2);
	});
	$("#show_loc_labels").click(function(){
		//saveSvgAsPng(document.getElementById('collapsible-network-diagramsvgContainer'),"diagram.png");
		if($("#show_loc_labels").is(':checked'))
			$("#collapsible-network-diagram").diagram("showPlaceNames");
		else
			$("#collapsible-network-diagram").diagram("hidePlaceNames");
	});
	$("#show_route_labels").click(function(){
		if($("#show_route_labels").is(':checked'))
			$("#collapsible-network-diagram").diagram("showRouteNames");
		else
			$("#collapsible-network-diagram").diagram("hideRouteNames");
	});
	
	updateNetworkDiagram();
//	$.ajax({
//		url: '{{rootPath}}json/dialoghtmlforstore',
//		dataType:'json',
//		data:{name:dialogBoxName,geninfo:1,utilinfo:0,popinfo:1,storedev:1,transdev:1,vacavail:0,fillratio:0,invent:0,availplot:0},
//		success:function(data){
//			//console.log(data.htmlString);
//			$(document.body).append(data.htmlString);
//		}
//	});
	
});	
</script>
 