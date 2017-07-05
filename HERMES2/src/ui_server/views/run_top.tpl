%rebase outer_wrapper title_slogan=_('Run Status'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
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
<p>
	<span class="hermes-top-main">
		{{_('Status of Currently Running Simulations')}}
	</span>
</p>

<table>
	<tr>
		<td>
			<h3 style="display:none">{{_('Run Status')}}</h3>
					<table id="manage_runs_grid"></table>
					<div id="manage_runs_pager"> </div>
		</td>
	</tr>
</table>
<div id='run_info_dialog'></div>
<div id="run_cancel_confirm_dialog" title="{{_('Confirming Run Cancelation')}}"></div>
<div id="run_cancel_info_dialog" title="{{_('Notification')}}"></div>

<script>


function runInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be an integer
	return "<button  class='hermes_info_button' id='"+cellvalue+"'>Info</button>";
}

function runCancelButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be an integer
	return "<button class='hermes_cancel_button' id='"+cellvalue+"'>{{_('Cancel')}}</button>" +
	"<button  class='hermes_clear_button' id='"+cellvalue+"'>{{_('Clear')}}</button>" +
	"<button  class='hermes_logs_button' id='"+cellvalue+"'>{{_('Logs')}}</button>";
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
		"",
        "{{_('Running')}}"
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
    	  formatter:runCancelButtonFormatter},
    {name:'isrunning', index:'isrunning', sorttype:'int', hidden:true}
	], //define column runs
	pager: '#manage_runs_pager', //set your pager div id
  pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
  pginput: false, //ditto
	sortname: 'runname', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
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
			//runId = $(this).attr('id');
			//alert(runId);
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
		$(".hermes_clear_button").click(function(event) {
			//runId = $(this).attr('id');
			//alert(runId);
			$.getJSON('json/run-clear',{runId:$(this).attr('id')})
			.done(function(data) {
				if (data.success) {
				        refreshGrid();
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
		$(".hermes_logs_button").click(function(event) {
			//runId = $(this).attr('id');
			//alert(runId);
			$.getJSON('json/run-logs',{runId:$(this).attr('id')})
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
			//$.getJSON('json/run-terminate',{runId:$(this).attr('id')})
			var $thisId = $(this).attr('id');
			$("#run_cancel_confirm_dialog").html("{{_('Are you sure that you would like to cancel the currently run?')}}");
			$("#run_cancel_confirm_dialog").dialog({
				modal:true,
				autoOpen: true,
				width:'auto',
				buttons:{
					"{{_('Yes')}}": function(){
						$.getJSON('json/run-terminate',{runId:$thisId})
						.done(function(data) {
			    			if (data.success) {
			    				$("#run_cancel_confirm_dialog").html("");
			    				$("#run_cancel_confirm_dialog").dialog("close");
								$("#run_cancel_confirm_dialog").dialog("destroy");
								$("#run_cancel_info_dialog").html("{{_('The run has been successfully cancelled')}}");
			    				$("#run_cancel_info_dialog").dialog({
			    					modal:true,
			    					autoOpen:true,
			    					width:'auto',
			    					buttons:{
			    						"{{_('OK')}}":function(){
			    							$("#run_cancel_info_dialog").html("");
			    							$(this).dialog("close");
			    							$(this).dialog("destroy");
			    						}
			    					}
			    				});
			    			}
			    			else {
			    				alert('{{_("Failed: ")}}'+data.msg);
			    			}
						})
						.fail(function(jqxhr, textStatus, error) {
							alert('{{_("Error: ")}}'+jqxhr.responseText);
						});
						event.stopPropagation();
					},
					"{{_('No')}}": function(){
						$(this).dialog("close");
						$(this).dialog("destroy");
					}
				}
			});
		});
		$(".hermes_cancel_button").each(function() {
			var id = $(this).attr('id');
			var state = $('#manage_runs_grid').getCell(id, 'isrunning');
			$(this).prop('disabled', (state == 'false'));
		});
		if (lastsel_runs != undefined) {
			// preserve selection across reload
			$('#manage_runs_grid').jqGrid('setSelection', lastsel_runs);
		}
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
$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
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

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });

</script>
 