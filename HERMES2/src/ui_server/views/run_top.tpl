%rebase outer_wrapper title_slogan=_('Run A Model'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<table>
<tr><td  style="border-style:solid">
<h2>{{_('Task:')}}</h2>
<table>
<tr><td><button id="run_model_button" style="width:100%" >{{_('Run HERMES')}}</button></td></tr>
</table>
</td>

<td  style="border-style:solid">
<h3>{{_('Run Status')}}</h3>
<table id="manage_runs_grid"></table>
<div id="manage_runs_pager"> </div>

</td>
</tr>
</table>

<!--
<input id="ziprunupload" type="file" name="files[]" data-url="{{rootPath}}upload-run" style="display:none">
<div id="progress">
    <div class="bar" style="width: 0%;"></div>
</div>
-->

<div id="run_info_dialog" title="This should get replaced">
</div>

<script>
{{!setupToolTips()}}

function runInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be an integer
	return "<button type=\"button\" class=\"hermes_info_button\" id="+cellvalue+">Info</button>";
}

function runCancelButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be an integer
	return "<button type=\"button\" class=\"hermes_cancel_button\" id="+cellvalue+">{{_('Cancel')}}</button>";
}

var lastsel_runs;
$("#manage_runs_grid").jqGrid({ //set your grid id
   	url:'json/manage-runs-table',
	datatype: "json",
	//width: 700, //deprecated with resize_grid
	//height: 'auto', //expand height according to number of records
	rowNum:9999, // rowNum=-1 has bugs, suggested solution is absurdly large setting to show all on one page
	colNames:[
		"{{_('Run Name')}}",
		"{{_('Run ID')}}",
		"{{_('Model Name')}}",
		"{{_('Model ID')}}",
		"{{_('Submitted')}}",
		"{{_('Status')}}",
        "{{_('Details')}}",
		""
	], //define column names
	colModel:[
	{name:'runname', index:'runname', editable:false, width:275},
	{name:'runid', index:'runid', key:true, hidden:true, sorttype:'int'},
	{name:'modelname', index:'modelname', editable:false, width:275},
	{name:'modelid', index:'modelid', sorttype:'int', width:150},
	{name:'submitted', index:'submitted', editable:false, width:275},
	{name:'status', index:'status', editable:false, width:350},
    {name:'info', index:'info', width:110, align:'center', sortable:false,
	  	  formatter:runInfoButtonFormatter},
    {name:'cancel', index:'cancel', width:160, align:'center', sortable:false,
    	  formatter:runCancelButtonFormatter}
	], //define column runs
	pager: '#manage_runs_pager', //set your pager div id
  pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
  pginput: false, //ditto
	sortname: 'runname', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
	sortorder: "asc", //sort order; optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
   	onSelectRow: function(runid, status){
   		//alert('select '+runid);
   		if (status) {
			if(runid && runid!==lastsel_runs){
				jQuery('#manage_runs_grid').jqGrid('saveRow',lastsel_runs);
				jQuery('#manage_runs_grid').jqGrid('editRow',runid,true);
				lastsel_runs=runid;
			}
		}
		else {
			alert('outside click '+runId);
		}
	},
	gridComplete: function(){
		$(".hermes_info_button").click(function(event) {
			$.getJSON('json/run-info',{runId:$(this).attr('id')})
			.done(function(data) {
    			if (data.success) {
    				$("#run_info_dialog").html(data['htmlstring']);
    				$("#run_info_dialog").dialog('option','title',data['title']);
    				$("#run_info_dialog").dialog("open");		
    			}
    			else {
    				alert('{{_("Failed: ")}}'+data.msg);
    			}
			})
			.fail(function(jqxhr, textStatus, error) {
				alert('{{_("Error: ")}}'+jqxhr.responseText);
			});
			event.stopPropagation();
		});
		$(".hermes_cancel_button").click(function(event) {
			$.getJSON('json/run-terminate',{runId:$(this).attr('id')})
			.done(function(data) {
    			if (data.success) {
    				alert('{{_("Canceled")}}');
    			}
    			else {
    				alert('{{_("Failed: ")}}'+data.msg);
    			}
			})
			.fail(function(jqxhr, textStatus, error) {
				alert('{{_("Error: ")}}'+jqxhr.responseText);
			});
			event.stopPropagation();
		});
	},
    editurl:'edit/edit-runs.json',	
    caption:"{{_('Available Runs')}}"
});
$("#manage_runs_grid").jqGrid('navGrid','#manage_runs_pager',{edit:false,add:false,del:false});

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_runs_grid"
  var offset = $(idGrid).offset() //position of grid on page
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-130);
}
$(document).ready(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
$(window).resize(resize_grid);  //bind resize_grid to window resize

function refreshGrid() {
	$("#manage_runs_grid").trigger("reloadGrid");
	//alert('selrow is '+$("#manage_runs_grid").jqGrid('getGridParam','selrow'));
};

$(function() {
	setInterval(refreshGrid,5000);
});

$(function() {
	$("#run_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function() {

	var btn = $("#run_model_button");
	btn.button();
	btn.click( function() {
		window.location="model-run";
	});

});

  
</script>
 