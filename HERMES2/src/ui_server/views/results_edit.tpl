%rebase outer_wrapper title_slogan=_('Examine Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer


<div id="results_info_dialog" title="This should get replaced">
</div>

<table>
<tr>
<td  style="border-style:solid">
<div id="results_edit_tree"></div>
</td>

<td  style="border-style:solid">
<h3>{{_('Things Might Go Here')}}</h3>
<table>
<tr><td><button id="results_1_button" style="width:100%" >{{_('Do Something')}}</button></td></tr>
<tr><td><button id="results_2_button" style="width:100%" >{{_('Do Something Else')}}</button></td></tr>
</table>
</td>
</tr>
</table>


<script>
$(function() {
	  $('#results_edit_tree').jstree({
	    "plugins": ["core","themes","json_data","ui"],
		"themes" : {
			"theme" : "classic",
		},
		"json_data" : {
			"ajax" : {
	                "url" : "json/show-tree",
					"data" : function (n) {
						return { id : n.attr ? n.attr("id") : -1 };
					}
	            }
		}
	  });
});
/*
function resultsInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be an integer
	return "<button type=\"button\" class=\"hermes_info_button\" id="+cellvalue+">Info</button>";
}

var lastsel_results;
$("#manage_results_grid").jqGrid({ //set your grid id
   	url:'json/manage-results-table',
	datatype: "json",
	width: 800, //specify width; optional
	colNames:[
		"{{_('Run Name')}}",
		"{{_('Run ID')}}",
		"{{_('Model Name')}}",
		"{{_('Model ID')}}",
		"{{_('Results ID')}}",
		"{{_('Type')}}"
	], //define column names
	colModel:[
	{name:'runname', index:'runname', editable:false, width:275},
	{name:'runid', index:'runid', sorttype:'int', width:150},
	{name:'modelname', index:'modelname', editable:false, width:275},
	{name:'modelid', index:'modelid', sorttype:'int', width:150},
	{name:'resultsid', index:'resultsid', sorttype:'int', width:150, key:true},
	{name:'resultstype', index:'resultstype', editable:false, width:275},
	], //define column runs
	pager: '#manage_results_pager', //set your pager div id
	sortname: 'runname', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
	sortorder: "asc", //sort order; optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
   	onSelectRow: function(resultsid, status){
   		alert('select '+resultsid);
   		if (status) {
			if(runid && runid!==lastsel_runs){
				jQuery('#manage_results_grid').jqGrid('saveRow',lastsel_results);
				jQuery('#manage_results_grid').jqGrid('editRow',resultsid,true);
				lastsel_results=resultsid;
			}
		}
		else {
			alert('outside click '+resultsId);
		}
	},
    editurl:'edit/edit-results.json',	
    caption:"{{_('Available Simulation Results')}}"
});
$("#manage_results_grid").jqGrid('navGrid','#manage_results_pager',{edit:false,add:false,del:false});

function refreshGrid() {
	$("#manage_results_grid").trigger("reloadGrid");
};

//$(function() {
//	setInterval(refreshGrid,5000);
//});
*/

$(function() {
	$("#results_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});


$(function() {

	var btn = $("#results_1_button");
	btn.button();
	btn.click( function() {
		$("#results_info_dialog").dialog("open");
	});

});

$(function() {

	var btn = $("#results_2_button");
	btn.button();
	btn.click( function() {
		alert("Unimplemented - Sorry!");
	});

});

  
</script>
 