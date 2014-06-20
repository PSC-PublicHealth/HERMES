%rebase outer_wrapper title_slogan=_('Vaccines Editor'), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<table>
<tr><td  style="border-style:solid">
<h2>Do you want to:</h2>
<table>
<tr><td><button id="create_vaccine_from_scratch_button" style="width:100%" >{{_('Create A Vaccine From Scratch')}}</button></td></tr>
<tr><td><button id="create_vaccine_from_proto_button" style="width:100%" >{{_('Create A Modified Version Of A Vaccine')}}</button></td></tr>
<tr><td><button id="delete_vaccine_button" style="width:100%">{{_('Delete Selected vaccine')}}</button></td></tr>
</table>
</td>

<td  style="border-style:solid">
<h3>{{_('Known Vaccines')}}</h3>
<label for="vaccine_top_model_select">{{_('Showing vaccines for')}}</label>
<select name="vaccine_top_model_select" id="vaccine_top_model_select"></select>
<table id="manage_vaccines_grid"></table>
<div id="manage_vaccines_pager"> </div>

</td>
</tr>
</table>

<div id="vaccine_info_dialog" title="This should get replaced">
</div>

<script>
function vaccinesInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be an integer
	return "<button type=\"button\" class=\"hermes_info_button\" id="+cellvalue+">Info</button>";
}

var lastsel_vaccines;
var sel_model_name = "unknown";
	
$("#manage_vaccines_grid").jqGrid({ //set your grid id
   	url:'json/manage-vaccines-table',
	datatype: "json",
	width: 500, //specify width; optional
	colNames:[
	          "{{_('ID')}}",
	          "{{_('Type')}}",
	          "{{_('Name')}}",
		"{{_('Manufacturer')}}",
		"{{_('Doses/Vial')}}",
		"{{_('Used in ')}}"+sel_model_name,
		"{{_('Details')}}"
	], //define column names
	colModel:[
	          {name:'id', index:'id', hidden:true},
	          {name:'type', index:'type', width:100},
	          {name:'name', index:'name', width:100},
	          {name:'manufacturer', index:'manufacturer', width:100},
	          {name:'doses', index:'doses', width:100},
	          {name:'usedin', index:'usedin', align:'center', sortable:false, 
	        	  editable:true, edittype:'checkbox', editoptions:{value:"True:False"}},
	          {name:'details', index:'details', width:110, align:'center', formatter:vaccinesInfoButtonFormatter}
	], //define column models
	pager: '#manage_vaccines_pager', //set your pager div id
	sortname: 'name', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
	sortorder: "asc", //sort order; optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
   	onSelectRow: function(id){
		if(id && id!==lastsel_vaccines){
			jQuery('#manage_vaccines_grid').jqGrid('saveRow',lastsel_vaccines);
			jQuery('#manage_vaccines_grid').jqGrid('editRow',id,true);
			lastsel_vaccines=id;
		}
	},
	gridComplete: function(){
		$(".hermes_info_button").click(function(event) {
			$.getJSON('json/vaccine_info',{vaccineId:$(this).attr('id')})
					.done(function(data) {
						$("#vaccine_info_dialog").html(data['htmlstring']);
						$("#vaccine_info_dialog").dialog('option','title',data['title']);
						$("#vaccine_info_dialog").dialog("open");		
					})
  					.fail(function(jqxhr, textStatus, error) {
  						alert("Error: "+jqxhr.responseText);
					});
			event.stopPropagation();
		});
	},
    editurl:'edit/edit_vaccines.json',	
    caption:"{{_("Available Vaccines")}}"

});
$("#manage_vaccines_grid").jqGrid('navGrid','#manage_vaccines_pager',{edit:false,add:false,del:false});

$(function() {
	$("#vaccine_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function() {

	var btn = $("#create_vaccine_from_proto_button");
	btn.button();
	btn.click( function() {
		alert("Unimplemented - Sorry!" + $("#vaccine_top_model_select").val());
	});

});

$(function() {

	var btn = $("#create_vaccine_from_scratch_button");
	btn.button();
	btn.click( function() {
		alert("Unimplemented - Sorry!");
	});

});

$(function() {
	var sel = $("#vaccine_top_model_select");
	sel.change( function() {
		$.getJSON('json/set-selected-model', {id:$("#vaccine_top_model_select").val()})
		.done(function(data) {
			sel_model_name = data['name'];
			$("#manage_vaccines_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
	    })
	  	.fail(function(jqxhr, textStatus, error) {
	  		alert("Error: "+jqxhr.responseText);
		});
	});

	$.getJSON('list/select_model')
	.done(function(data) {
		var sel = $("#vaccine_top_model_select");
    	sel.append(data['menustr']);
    	sel_model_name = data['selname']
		$("#manage_vaccines_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert("Error: "+jqxhr.responseText);
	});
});

$(function() {

	var btn = $("#delete_vaccine_button");
	btn.button();
	btn.click( function() {
		$("#manage_vaccines_grid").jqGrid('restoreRow',lastsel_vaccines);
		var vaccineName = $("#manage_vaccines_grid").jqGrid('getCell',lastsel_vaccines,'name');
		$("#manage_vaccines_grid").jqGrid('delGridRow',lastsel_vaccines,{msg:"Really delete the vaccine "+vaccineName+" ?"});
		lastsel_vaccines=null;
	});

});

  
</script>
 