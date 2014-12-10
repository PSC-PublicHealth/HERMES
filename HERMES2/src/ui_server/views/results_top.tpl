%rebase outer_wrapper title_slogan=_('Simulation Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<table>
<tr><td style="float:left;width:80px">
<h2 style="display:none">{{_('Task:')}}</h2>
<table>
<tr><td><button id="results_edit_button" style="width:100%">{{_('Open')}}</button></td></tr>
<tr><td><button id="results_delete_button" style="width:100%">{{_('Delete')}}</button></td></tr>
</table>
</td>

<td>
<h3 style="display:none">{{_('Available Results')}}</h3>
<table id="manage_results_grid"></table>
<div id="manage_results_pager"> </div>

</td>
</tr>
</table>

<div id="results_info_dialog" title="This should get replaced">
</div>

<div id="results_confirm_delete" title='{{_("Delete Results")}}'>
</div>

<script>
{{!setupToolTips()}}

var lastsel_results;

function resultsInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be an integer
	return "<button type=\"button\" class=\"hermes_info_button\" id="+cellvalue+">Info</button>";
}

$("#manage_results_grid").jqGrid({ //set your grid id
	url:'json/manage-results-table',
	datatype: "json",
	caption:"{{_('Available Simulation Results')}}",
	editurl: 'edit/edit-results.json',
	//width: 1220, //width chosen here actually renders in much smaller # of pixels
	//height:'auto', //deprecated with resize_grid
	pager: '#manage_results_pager', //set your pager div id
  pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
  pginput: false, //ditto
	rowNum: 9999,
	colNames:[
		"{{_('Model Name')}}",
		"{{_('Model ID')}}",
		"{{_('Result Name')}}",
		"{{_('Results ID')}}",
		"",
		"{{_('SubRunID')}}",
		"{{_('Sub-Run')}}",
		"{{_('Details')}}"
	],
	colModel:[
		{name:'modelname', index:'modelname', editable:false, width:275},
		{name:'modelid', index:'modelid', sorttype:'int', editable:false, width:150, hidden:true},
		//{name:'resultsgrpname', index:'resultsgrpname', width:150,editable:false},
		{name:'runname', index:'runname', width:150,editable:false},
		{name:'resultsid', index:'resultsid', editable:false, sorttype:'int', width:275},
		//{name:'resultgrpname', index:'resultsgrpname', sorttype:'int', width:150,hidden:true},
		//{name:'placeholder', index:'placeholder',width:200},
		{name:'resultstype', index:'resultstype', sortable:false, editable:false},
		{name:'runid', index:'runid', sorttype:'int', width:150, key:true, hidden:true},
		{name:'runnum', index:'runnum', sorttype:'int', width:150},
		{name:'info', index:'info', width:110, align:'center', sortable:false,
	  	  formatter:resultsInfoButtonFormatter}
	],
	jsonReader:{
		repeatitems:false,
		root:'rows'
	},
	grouping:true,
	groupingView: {
		//groupField : ['runname','modelname'],
		//groupField : ['modelname','resultsid'],

		//groupField : ['modelname','resultsid'],
		//groupColumnShow: [false,false],
		groupField : ['modelname','runname'],
		groupColumnShow: [false,false],
		
		groupCollapse:true
	},
	onSelectRow: function(resultsid, status){
   		if (status) {
			if(resultsid && resultsid!==lastsel_results){
				jQuery('#manage_results_grid').jqGrid('saveRow',lastsel_results);
				jQuery('#manage_results_grid').jqGrid('editRow',resultsid,true);
				lastsel_results=resultsid;
			}
		}
		else {
			alert('outside click '+resultsId);
		}
	},
	gridComplete: function(){
   		$(".hermes_info_button").click(function(event) {
    		$.getJSON('json/results-info',{resultsId:$(this).attr('id')})
    		.done(function(data) {
        		if (data.success) {
        			if (data.success) {
        				$("#results_info_dialog").html(data['htmlstring']);
        				$("#results_info_dialog").dialog('option','title',data['title']);
        				$("#results_info_dialog").dialog("open");
        			}
    				else {
        				alert('{{_("Failed: ")}}'+data.msg);
    				}
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
    }
});	

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_results_grid"
  var offset = $(idGrid).offset() //position of grid on page
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-130);
}
$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
$(window).resize(resize_grid);  //bind resize_grid to window resize

/*   	url:'json/manage-results-table',	
	datatype: "json",
//   editurl:'edit/edit-results.json',	
    caption:"{{_('Available Simulation Results')}}",
	width: 800, //specify width; optional
	colNames:[
	  	"{{_('Model Name')}}",
		"{{_('Model ID')}}",
		"{{_('Result Name')}}",
		"{{_('Results ID')}}",
		" ",
		"{{_('Results ID')}}",
		"{{_('Sub-Run')}}",
//		"{{_('Details')}}"
	], //define column names
	colModel:[
	{name:'runname', index:'runname', editable:false, width:275},
	{name:'runid', index:'runid', sorttype:'int', width:150, hidden:true},
	{name:'modelname', index:'modelname', editable:false, width:275},
	{name:'modelid', index:'modelid', sorttype:'int', width:150,hidden:true},
	{name:'placeholder',index:'placeholder',width:200},
	{name:'resultsid', index:'resultsid', sorttype:'int', width:150, key:true, hidden:true},
	{name:'runnum', index:'runnum', sorttype:'int', width:150},
//    {name:'info', index:'info', width:110, align:'center', sortable:false,
	  	  formatter:resultsInfoButtonFormatter},
	], //define column runs
//	pager: '#manage_results_pager', //set your pager div id
	sortname: 'runname', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
//	sortorder: "asc", //sort order; optional
//	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
  	onSelectRow: function(resultsid, status){
   		if (status) {
			if(resultsid && resultsid!==lastsel_results){
				jQuery('#manage_results_grid').jqGrid('saveRow',lastsel_results);
				jQuery('#manage_results_grid').jqGrid('editRow',resultsid,true);
				lastsel_results=resultsid;
			}
		}
		else {
			alert('outside click '+resultsId);
		}
	},
	loadError: function(xhr,status,error){
    			alert('{{_("Error: ")}}'+status);
	},
	beforeProcessing: function(data,status,xhr) {
		if (!data.success) {
        	alert('{{_("Failed: ")}}'+data.msg);
		}
	},
    gridComplete: function(){
   		$(".hermes_info_button").click(function(event) {
    		$.getJSON('json/results-info',{resultsId:$(this).attr('id')})
    		.done(function(data) {
        		if (data.success) {
        			$("#results_info_dialog").html(data['htmlstring']);
        			$("#results_info_dialog").dialog('option','title',data['title']);
        			$("#results_info_dialog").dialog("open");
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
    treeGrid: true,
    	ExpandColumn: 'runname',
*/
    	
	//grouping : true,
	//groupingView: {
	//	groupField:['runname','modelname'],
	//	groupColumnShow: [false,false,],
	//	groupOrder: ['asc','asc']
	//},
//});
$("#manage_results_grid").jqGrid('navGrid','#manage_results_pager',{edit:false,add:false,del:false});

function refreshGrid() {
	$("#manage_results_grid").trigger("reloadGrid");
};

//$(function() {
//	setInterval(refreshGrid,5000);
//});

$(function() {
	$("#results_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function() {
	$("#results_confirm_delete").dialog({
		autoOpen:false, 
		height:"auto", 
		width:"auto",
     	buttons: {
			'{{_("Delete")}}': function() {
				$( this ).dialog( "close" );
	    		$.getJSON('edit/edit-results.json',{id:lastsel_results, oper:'del'})
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
				lastsel_results=null;
								
        	},
        	'{{_("Cancel")}}': function() {
          		$( this ).dialog( "close" );
        	}
     	}
	});
});

$(function() {

	var btn = $("#results_edit_button");
	btn.button();
	btn.click( function() {
		var modelId = $("#manage_results_grid").jqGrid('getCell',lastsel_results,'modelid');
		window.location="{{rootPath}}results-summary?modelId="+modelId+"&resultsId="+lastsel_results+"&resultType=vaccines";
	});

});

$(function() {

	var btn = $("#results_delete_button");
	btn.button();
	btn.click( function() {
		if (lastsel_results==null) {
			alert('{{_("No Selection")}}');
		}
		else {
			$("#manage_results_grid").jqGrid('restoreRow',lastsel_results);
			var resultsId = $("#manage_results_grid").jqGrid('getCell', lastsel_results, 'resultsid');
			var runName = $("#manage_results_grid").jqGrid('getCell', lastsel_results, 'runname');
			var runNumber = $("#manage_results_grid").jqGrid('getCell', lastsel_results, 'runnum');
			var myMsg = '{{_("Really delete the result for run ")}}' + runName + " : " + runNumber + " ? ";
			$("#results_confirm_delete").html(myMsg);
			$("#results_confirm_delete").dialog("open");
		}
	});

});

  
</script>
 