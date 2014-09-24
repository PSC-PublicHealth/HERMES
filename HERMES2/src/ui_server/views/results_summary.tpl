%rebase outer_wrapper title_slogan=_('Simulation Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId

<script type="text/javascript" src="http://code.highcharts.com/highcharts.js"></script>
<style type="text/css">
/* for jqGrid tables */
.ui-jqgrid {font-size:small}
.ui-jqgrid tr.jqgrow td {font-size:small}
.ui-jqgrid tr.jqgroup td {
	font-size:small;
	background-color: rgb(88,88,88);
	color: white;
}
th.ui-th-column div {
	word-wrap: break-word;
	white-space: pre-wrap; /* CSS3 */
    	white-space: -moz-pre-wrap; /* Mozilla, since 1999 */
    	white-space: -pre-wrap; /* Opera 4-6 */
    	white-space: -o-pre-wrap; /* Opera 7 */
    	overflow: hidden;
    	height: auto !important;
    	vertical-align: middle;
	font-size:small;
}
</style>


<div id="summary_div" width="100%">
<table id="vaccine_summary_results_grid"></table>
<div style="width:500;" id="results_summary_buttons_div">
<button id="results_summary_show_ge_button" style="width:100px;">{{_('Show Geographic Viz')}}</button>
% if gvAvailable:
<button id="results_summary_show_gv_button" style="width:100px;">{{_('Show Fireworks Viz')}}</button>
% end
</div>
<div style="float:left;width:300;" id="vaccine_by_place_graph"></div>
<div style="float:left;width:300;" id="storeUtil_by_place_graph"></div>
<div style="float:left;width:300;" id="transUtil_by_route_graph"></div>
</div>

<script>
function perElem(value,options){
	var el = document.createElement("")}
	
$(document).ready(function(){	
$("#results_summary_show_ge_button").click( function(){
	window.location="{{rootPath}}geographic_visualization?modelId="+{{modelId}}+"&resultsId="+{{resultsId}};
});

% if gvAvailable:
$("#results_summary_show_gv_button").click( function(){
	window.location="{{rootPath}}results-fireworks?modelId="+{{modelId}}+"&runId="+{{resultsId}};
});
% end

$("#vaccine_summary_results_grid").jqGrid({ //set your grid id
   	url:'json/results-summary?modelId={{modelId}}&resultsId={{resultsId}}&resultType=vaccines',
	datatype: "json",
	jsonReader: {
		root:'rows',
		repeatitems: false,
		id:'vaccid'
	},
	sortable:true,
    caption:"{{_('Vaccine Results')}}",
	width: 900, //specify width; optional
	height:175,
	colNames:[
		"{{_('ID')}}",
	  	"{{_('Vaccine')}}",
		"{{_('Availability')}}",
		"{{_('Vials Used')}}",
		"{{_('Doses Per Vial')}}",
		"{{_('Doses Requested')}}",
		"{{_('Doses Administered')}}",
		"{{_('Open Vial Waste')}}",
		"{{_('Percent Stored 2 to 8 C')}}",
		"{{_('Percent Store Below 2C')}}",
		"{{_('Vials Spoiled')}}"
	], //define column names
	colModel:[	
	{name:'vaccid',index:'vaccid',jsonmap:'vaccid',hidden:true, key:true},
	{name:'name',index:'name',jsonmap:'DisplayName',width:150,sortable:true,sorttype:'text'},
	{name:'availability',index:'availability',jsonmap:'SupplyRatio',width:75,
		formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; if(value < 0.0){ value=0.0;}; return value.toFixed(2) + "%"},
		align:'right'},
	{name:'vialsused',index:'vialsused',jsonmap:'VialsUsed',width:75,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
	{name:'dosespervial',index:'dosespervial',jsonmap:'DosesPerVial',width:50,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
	{name:'dosesrequested',index:'dosesrequested',jsonmap:'Applied',width:75,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
	{name:'dosesadmin',index:'dosesadmin',jsonmap:'Treated',width:85,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}},
	{name:'ovw',index:'ovw',jsonmap:'OpenVialWasteFrac',width:75,
		formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; if(value < 0.0){ value=0.0;}; return value.toFixed(2) + "%"},
		align:'right'},
	{name:'percooler',index:'percooler',jsonmap:'coolerStorageFrac',width:75,formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; return value.toFixed(2) + "%"},align:'right'},
	{name:'perfreezer',index:'perfreezer',jsonmap:'freezerStorageFrac',width:75,formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; return value.toFixed(2) + "%"},align:'right'},
	{name:'vialspoiled',index:'vialsspoiled',jsonmap:'VialsExpired',width:75,formatter:'number',align:'right',formatoptions:{decimalPlaces:0}}
	], //define column runs
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
	 
});

$.getJSON('json/results-vaccine-by-place-by-size-hist?modelId={{modelId}}&resultsId={{resultsId}}', function(results) {
	$("#vaccine_by_place_graph").highcharts({
		chart : {
			type : 'bar',
			height : 300,
			width : 300
		},
		title : {
			text : "{{_('Availability by Location')}}"
		},
		legend : {
			enabled : true,
			title: {
				text: "{{_('Birth Cohort Size')}}"
			},
		},
		xAxis : {
			categories : results.categories,
			title : {
				text : "{{_('Availability')}}"
			}
		},
		yAxis : {
			min : 0,
			title : {
				text : "{{_('Number Of Locations')}}"
			}
		},
		plotOptions : {
			bar: {
				dataLabels : {
					enabled : false
				},
            	groupPadding: 0,
            	pointPadding: 0,
            	borderWidth: 0
			}
		},
		credits : {
			enabled : false
		},
		series : results.datas
	});
}); 

$.getJSON('json/result-storage-utilization-by-place-by-levelhist?modelId={{modelId}}&resultsId={{resultsId}}', function(results) {
	$("#storeUtil_by_place_graph").highcharts({
		chart : {
			type : 'bar',
			height : 300,
			width : 300
		},
		title : {
			text : "{{_('Maximum Storage Utilization by Location')}}"
		},
		legend : {
			enabled : true,
			title: {
				text: 'Levels'
			}
		},
		xAxis : {
			categories : results.categories,
			title : {
				text : "{{_('Utilization')}}"
			}
		},
		yAxis : {
			min : 0,
			title : {
				text : "{{_('Number Of Locations')}}"
			}
		},
		plotOptions : {
			bar: {
				dataLabels : {
					enabled : false
				},
            	groupPadding: 0,
            	pointPadding: 0,
            	borderWidth: 0
			}
		},
		credits : {
			enabled : false
		},
		series : results.datas
	});
}); 

$.getJSON('json/result-transport-utilization-by-route-by-level-hist?modelId={{modelId}}&resultsId={{resultsId}}', function(results) {
	$("#transUtil_by_route_graph").highcharts({
		chart : {
			type : 'bar',
			height : 300,
			width : 300
		},
		title : {
			text : "{{_('Maximum Transport Utilization by Route')}}"
		},
		legend : {
			enabled : true,
			title: {
				text: "Origin Level"
			},
		},
		xAxis : {
			categories : results.categories,
			title : {
				text : "{{_('Utilization')}}"
			}
		},
		yAxis : {
			min : 0,
			title : {
				text : "{{_('Number Of Locations')}}"
			}
		},
		plotOptions : {
			bar: {
				dataLabels : {
					enabled : false
				},
            	groupPadding: 0,
            	pointPadding: 0,
            	borderWidth: 0
			}
		},
		credits : {
			enabled : false
		},
		series : results.datas
	});
}); 
});
</script>

<!-- Hierarchical Charts for Cost Summaries -->
<div id="costcharts" name="costcharts"/>
<div id="hierarchicalBarchart" name "hierarchicalBarchart"/>
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
        minHeight: 175,
        resizable: false,
        scrollable: true,
        trant: {
             "title": "{{_('Costs by Report Level')}}", 
             "currency_label": "{{_('Currency')}}",
             "year_label": "{{_('Year')}}",
        }

    });
</script>
