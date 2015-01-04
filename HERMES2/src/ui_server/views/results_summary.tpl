%rebase outer_wrapper title_slogan=_('Simulation Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId

<script type="text/javascript" src="{{rootPath}}static/Highcharts-3.0.5/js/highcharts.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery.fileDownload.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/summary.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_availability_by_cohort.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/storage_utilization_by_level.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/transport_utilization_by_route.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_summary_grid.js"></script>

<link rel="stylesheet" href='{{rootPath}}static/results-widgets/results-widgets.css'/> 
<style type="text/css">
/* for jqGrid tables */
//.ui-jqgrid {font-size:x-small}
//.ui-jqgrid tr.jqgrow td {font-size:x-small}
//.ui-jqgrid tr.jqgroup td {
//	font-size:small;
//	background-color: rgb(88,88,88);
//	color: white;
//}
//th.ui-th-column div {
//	word-wrap: break-word;
//	white-space: pre-wrap; /* CSS3 */
//    	white-space: -moz-pre-wrap; /* Mozilla, since 1999 */
//    	white-space: -pre-wrap; /* Opera 4-6 */
//    	white-space: -o-pre-wrap; /* Opera 7 */
//    	overflow: hidden;
//    	height: auto !important;
//    	vertical-align: middle;
//	font-size:x-small;
//}
</style>

<h1>{{modelName}}</h1>
<h4>Results: {{resultsGroupName}}</h4>
<div id="summary_test_div" class='rs_summary' width="100%"></div>
<div id="summary_div" width="100%">
<table id="vaccine_summary_results_grid"></table>
<div style="width:500;" id="results_summary_buttons_div">
<button id="results_summary_show_ge_button" style="width:100px;">{{_('Show Geographic Viz')}}</button>
<button id="results_summary_show_ne_button" style="width:100px;">{{_('Show Network Viz')}}</button>
% if gvAvailable:
<button id="results_summary_show_gv_button" style="width:100px;">{{_('Show Fireworks Viz')}}</button>
% end
<button id="results_download_xls_button" style="width:100px;">{{_('Download Excel Results')}}</button>
</div>
<div style="float:left;width:300;" id="vaccine-availability-by-cohort"></div>
<div style="float:left;width:300;" id="storage-utilization-by-level"></div>
<div style="float:left;width:300;" id="transUtil_by_route_graph"></div>
</div>

<div id="download_xls_saveas" title={{_('Save Excel Model Results As...')}}>
	<form>
		<fieldset>
			<table>
				<tr>
					<td><label for="download_xls_saveas_name">{{_('Filename')}}</td>
					<td><input id="download_xls_saveas_name" type="text"></td>
				</tr>
			</table>
		</fieldset>
	</form>
</div>
<script>

function perElem(value,options){
	var el = document.createElement("")
}

$("#summary_test_div").results_summary_page({
	resultsId:'{{resultsId}}',
	modelId:'{{modelId}}',
	rootPath:'{{rootPath}}'
});

//$('#vaccine_summary_results_grid').vsgrid({
//	resultsId:'{{resultsId}}',
//	modelId:'{{modelId}}'
//});

//$.ajax({
//	url:'{{rootPath}}json/results-vaccine-by-place-by-size-hist?modelId={{modelId}}&resultsId={{resultsId}}',
//	dataType:'json',
//	success:function(result){
//		$('#vaccine-availability-by-cohort').vachart({
//			jsonData:result
//		});
//	}
//});
//
//$.ajax({
//	url:'{{rootPath}}json/result-storage-utilization-by-place-by-levelhist?modelId={{modelId}}&resultsId={{resultsId}}',
//	dataType:'json',
//	success:function(result){
//		$("#storage-utilization-by-level").suchart({
//			jsonData:result
//		});
//	}
//});
//
//$.ajax({
//	url:'{{rootPath}}json/result-transport-utilization-by-route-by-level-hist?modelId={{modelId}}&resultsId={{resultsId}}',
//	dataType:'json',
//	success:function(result){
//		$('#transUtil_by_route_graph').tuchart({
//			jsonData:result
//		});
//	}
//});

$(function(){
	window.addEventListener('resize',function(event){
		if($(window).width() > 900){
			$("#summary_test_div").results_summary_page("grow");
		}
		else{
			$("#summary_test_div").results_summary_page("shrink");
		}
	});
});

$("#download_xls_saveas").dialog({
	autoOpen:false,
	height: 300,
	width: 400,
	model: true,
	buttons:{
		'OK':{
			text:'{{_("Save")}}',
			click: function() {
				if(!$('#download_xls_saveas_name').val()){
					alert("{{_("Must define a name to give the file.")}}");
				}
				else {
					var filename = $("#download_xls_saveas_name").val();
					$(this).dialog('close');
					$.ajax({
						url: '{{rootPath}}json/create-xls-summary-openpyxl',
						dataType:'json',
						data:{modelId:{{modelId}},resultsId:{{resultsId}},filename:filename}})
					.done(function(data){
						if (data.success==true){
							$.fileDownload('{{rootPath}}downloadXLS?shortname='+filename) 
								.done(function(){})
								.fail(function(){alert("{{_('A problem has occured in the creation of the report.')}}");});
						}
						else {
							alert('{{_("There was a problem creating the report")}}\n'+ data.msg);
						}
					})
					.fail( function(data){
						alert(data.msg);
					});
				}
			}
		},
		'Cancel':{
			text:'{{_("Cancel")}}',
			click: function(){
				$(this).dialog("close");
			}
		}
	},
	open: function (e,ui){
		$(this).keypress(function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER){
				e.preventDefault();
				$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
		});
	}	
});

$("#results_summary_show_ge_button").click( function(){
	window.location="{{rootPath}}geographic_visualization?modelId="+{{modelId}}+"&resultsId="+{{resultsId}};
});

$("#results_summary_show_ne_button").click( function(){
	window.location="{{rootPath}}network_results_visualization?modelId="+{{modelId}}+"&resultsId="+{{resultsId}};
	});
% if gvAvailable:
	$("#results_summary_show_gv_button").click( function(){
	window.location="{{rootPath}}results-fireworks?modelId="+{{modelId}}+"&runId="+{{resultsId}};
	});
% end

$("#results_download_xls_button").click( function (){
	$("#download_xls_saveas").dialog("open");
});
	
</script>

<!-- Hierarchical Charts for Cost Summaries -->
<div id="costcharts" name="costcharts">

<!-- Hierarchical Barchart -->
<div id="hierarchicalBarchart" name="hierarchicalBarchart">
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/hierarchical-charts/hierarchical-barcharts.js"></script>
<script>
    $("#hierarchicalBarchart").barchart({
        hasChildrenColor: "steelblue",
        noChildrenColor: "#ccc",
        jsonDataURLBase: "json/results-cost-hierarchical",
        jsonDataURLParameters: [
            "modelId={{modelId}}",
            "resultsId={{resultsId}}"],
        minWidth: 768,
        minHeight: 300,
        resizable: false,
        scrollable: true,
        trant: {
             "title": "{{_('Costs by Report Level')}}", 
             "currency_label": "{{_('Currency')}}",
             "year_label": "{{_('Year')}}",
        }

    });
</script>
</div>

<!-- Zoomable Treemap -->
<div id="zoomableTreemap" name="zoomableTreemap">
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/hierarchical-charts/zoomable-treemap.js"></script>
<script>
    $("#zoomableTreemap").treemap({
        hasChildrenColor: "steelblue",
        noChildrenColor: "#ccc",
        jsonDataURLBase: "json/results-cost-hierarchical-value",
        jsonDataURLParameters: [
            "modelId={{modelId}}",
            "resultsId={{resultsId}}"],
        minWidth: 768,
        minHeight: 775,
        resizable: false,
        scrollable: true,
        trant: {
             "title": "{{_('Costs by Report Level')}}", 
             "currency_label": "{{_('Currency')}}",
             "year_label": "{{_('Year')}}",
        }

    });
</script>
</div>

</div>

<script>
//$("#vaccine_summary_results_grid").jqGrid({ //set your grid id
//url:'json/results-summary?modelId={{modelId}}&resultsId={{resultsId}}&resultType=vaccines',
//datatype: "json",
//jsonReader: {
//root:'rows',
//repeatitems: false,
//id:'vaccid'
//},
//sortable:true,
//caption:"{{_('Vaccine Results')}}",
//width: 'auto', //specify width; optional
//height:'auto',
//autowidth:'true',
//colNames:[
//"{{_('ID')}}",
//	"{{_('Vaccine')}}",
//"{{_('Availability')}}",
//"{{_('Vials Used')}}",
//"{{_('Doses Per Vial')}}",
//"{{_('Doses Needed')}}",
//"{{_('Doses Received')}}",
//"{{_('Open Vial Waste')}}",
//"{{_('Percent Stored 2 to 8 C')}}",
//"{{_('Percent Store Below 2C')}}",
//"{{_('Vials Spoiled')}}"
//], //define column names
//colModel:[	
//{name:'vaccid',index:'vaccid',jsonmap:'vaccid',hidden:true, key:true},
//{name:'name',index:'name',jsonmap:'DisplayName',width:150,sortable:true,sorttype:'text'},
//{name:'availability',index:'availability',jsonmap:'SupplyRatio',width:75,
//formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; if(value < 0.0){ value=0.0;}; return value.toFixed(2) + "%"},
//align:'right'},
//{name:'vialsused',index:'vialsused',jsonmap:'VialsUsed',width:75,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
//{name:'dosespervial',index:'dosespervial',jsonmap:'DosesPerVial',width:50,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
//{name:'dosesrequested',index:'dosesrequested',jsonmap:'Applied',width:75,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
//{name:'dosesadmin',index:'dosesadmin',jsonmap:'Treated',width:85,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
//{name:'ovw',index:'ovw',jsonmap:'OpenVialWasteFrac',width:75,
//formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; if(value < 0.0){ value=0.0;}; return value.toFixed(2) + "%"},
//align:'right'},
//{name:'percooler',index:'percooler',jsonmap:'coolerStorageFrac',width:75,formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; return value.toFixed(2) + "%"},align:'right'},
//{name:'perfreezer',index:'perfreezer',jsonmap:'freezerStorageFrac',width:75,formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; return value.toFixed(2) + "%"},align:'right'},
//{name:'vialspoiled',index:'vialsspoiled',jsonmap:'VialsExpired',width:75,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}}
//], //define column runs
//gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
//
//});
</script>




















