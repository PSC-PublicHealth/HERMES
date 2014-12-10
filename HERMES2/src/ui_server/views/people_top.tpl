% title_slogan=_("Population Types")
%rebase outer_wrapper **locals()

<table>
<tr><td style="float:left;width:80px">
<h2 style="display:none">Task:</h2>
<table>
<tr><td><button id="create_people_from_proto_button" style="width:100%">{{!_('Create')}}</button></td></tr>
<tr><td><button id="copy_people_button" style="width:100%">{{!_('Copy')}}</button></td></tr>
<tr><td><button id="paste_people_button" style="width:100%">{{!_('Paste')}}</button></td></tr>
</table>
</td>

<td>
<h3 style="display:none">{{_('Known Population Types')}}</h3>
<label for="people_top_model_select">{{_('Showing population types for')}}</label>
<select name="people_top_model_select" id="people_top_model_select"></select>
<table id="manage_people_grid"></table>
<div id="manage_people_pager"> </div>

</td>
</tr>
</table>

<div id="people_info_dialog" title="This should get replaced"></div>

<div id="confirm_dialog" title='{{_("Confirm Removal")}}'></div>

<div id="get_paste_name_dialog" title='{{_("Name Conflict")}}'>
<form>
{{_("The name on the clipboard is already in use in this model.  What name should be used for the new item?")}}
<fieldset>
	<table>
		<tr>
  		<td><label for="paste_new_name">{{_('Name Of The Copy')}}</label></td>
  		<td><input type="text" name="paste_new_name" id="get_paste_name_dlg_new_name" 
  			class="text ui-widget-content ui-corner-all" /></td>
  		</tr>
  	</table>
</fieldset>
</form>
</div>

<script>
{{!setupToolTips()}}

var lastsel_people;
var sel_model_name = null;
	
function boxClick(cb,event) {
	if (cb.checked) {
		// The item is being changed from not-in-model to in-model
		event.stopPropagation();
		$.getJSON('{{rootPath}}json/add-type-to-model',{name:cb.value, modelId:$("#people_top_model_select").val()})
		.done(function(data) {
			if (data.success) {
				$("#manage_people_grid").trigger("reloadGrid"); // to update checkboxes
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
	      		cb.checked = false;				
			}
		})
		.fail(function(jqxhr, textStatus, error) {
			alert('{{_("Error: ")}}'+jqxhr.responseText);
      		cb.checked = false;				
		});
	}
	else { 
		// The item is being removed from the model.
		event.stopPropagation();
		var dlg = $('#confirm_dialog')
		dlg.html('{{_("Really remove all instances of ")}}' + cb.value 
				+ '{{_("from model ")}}' + $("#people_top_model_select").val() + '{{_("?")}}');
		dlg.data('name',cb.value);
		dlg.data('modelId',$("#people_top_model_select").val());
		dlg.data('cb',cb);
		dlg.dialog('open');
	};
}

function peopleInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>";
};

function checkboxFormatter(cellvalue, options, rowObject)
{
	if (cellvalue) {
		return "<input type='checkbox'  checked value='"+rowObject[0]+"' onclick='boxClick(this,event)'>";
	}
	else {
		return "<input type='checkbox'  value='"+rowObject[0]+"' onclick='boxClick(this,event)'>";
	}
};

$("#manage_people_grid").jqGrid({ //set your grid id
   	url:'{{rootPath}}json/manage-people-table',
    editurl:'{{rootPath}}edit/edit-people.json',	
	datatype: "json",
	postData: {
		modelId: function() { return $("#people_top_model_select").val(); }
	},
	//width: 750, //deprecated with resize_grid
	//height:'auto', //expand height according to number of records
	rowNum:9999, // rowNum=-1 has bugs, suggested solution is absurdly large setting to show all on one page
	colNames:[
	          "{{_('Name')}}",
	          "{{_('Used in ')}}"+sel_model_name,
	          "{{_('DisplayName')}}",
	          "{{_('Details')}}"
	], //define column names
	colModel:[
	          {name:'name', index:'name', width:200, key:true},
	          {name:'usedin', index:'usedin', align:'center', formatter:checkboxFormatter},
	          {name:'dispnm', index:'dispnm', width:200, editable:true, edittype:'text'},
	          {name:'info', index:'info', width:110, align:'center', sortable:false,
	        	  formatter:peopleInfoButtonFormatter}
	], //define column models
	pager: '#manage_people_pager', //set your pager div id
	pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
  pginput: false, //ditto
	sortname: 'name', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
	sortorder: "asc", //sort order; optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
	beforeRequest: function() {
		return (sel_model_name != null); // suppress update until selected model is known
	},
   	onSelectRow: function(id){
		if(id && id!==lastsel_people){
			jQuery('#manage_people_grid').jqGrid('saveRow',lastsel_people);
			jQuery('#manage_people_grid').jqGrid('editRow',id,{
				keys:true,
				extraparam: { modelId: function() { return $("#people_top_model_select").val(); }}
			});
			lastsel_people=id;
		}
	},
	gridComplete: function(){
		$(".hermes_info_button").click(function(event) {
			$.getJSON('{{rootPath}}json/people-info',{name:unescape($(this).attr('id')), modelId:$("#people_top_model_select").val()})
			.done(function(data) {
				if (data.success) {
					$("#people_info_dialog").html(data['htmlstring']);
					$("#people_info_dialog").dialog('option','title',data['title']);
					$("#people_info_dialog").dialog("open");
				}
				else {
    				alert('{{_("Failed: ")}}'+data.msg);
				}
			})
				.fail(function(jqxhr, textStatus, error) {
					alert("Error: "+jqxhr.responseText);
			});
			event.stopPropagation();
		});
	},
	rowattr: function(rowdata){
		if (!rowdata.usedin) return {"class":"not-editable-row"};
	},
    caption:"{{ _("Available Population Types") if not defined('smallCaption') else smallCaption }}"
}).jqGrid('hermify',{debug:true});
$("#manage_people_grid").jqGrid('navGrid','#manage_people_pager',{edit:false,add:false,del:false});

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_people_grid"
  var offset = $(idGrid).offset() //position of grid on page
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-130);
}
$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
$(window).resize(resize_grid);  //bind resize_grid to window resize

$(function() {
	$("#people_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
	$("#confirm_dialog").dialog({
		autoOpen:false, height:"auto", width:"auto", modal:true,
		buttons: {
	    	Ok: function() {
	    		var dlg = $('#confirm_dialog');
	    		$.getJSON('{{rootPath}}json/remove-type-from-model',
	    				{name:dlg.data('name'), modelId:dlg.data('modelId')})
	    		.done(function(data) {
	    			if (data.success) {
	    				$("#manage_people_grid").trigger("reloadGrid"); // to update checkboxes
	    			}
	    			else {
	    				alert('{{_("Failed: ")}}'+data.msg);
			      		dlg.data('cb').checked = true;
	    			}
	    		})
	    		.fail(function(jqxhr, textStatus, error) {
	    			alert('{{_("Error: ")}}'+jqxhr.responseText);
		      		dlg.data('cb').checked = true;
	    		});
	      		$( this ).dialog( "close" );
	    	},
	    	Cancel: function() {
	    		var dlg = $('#confirm_dialog');
	      		$( this ).dialog( "close" );
	      		dlg.data('cb').checked = true;
	    	}
		}
	});
});

$(function() {
	$("#get_paste_name_dialog").dialog({
		autoOpen:false, height:"auto", width:300, modal:true,
		buttons: {
	    	Ok: function() {
	    		var newNm = $("#get_paste_name_dlg_new_name").val();
				$.getJSON('{{rootPath}}check-unique-hint',
						{modelId:$("#people_top_model_select").val(),typeName:newNm})
				.done(function(data) {
					if (data.success) {
						if (data.value) {
							$.getJSON('{{rootPath}}json/paste-clipboard-to-type', {
								modelId:$("#people_top_model_select").val(), 
								type:"people", name:newNm
							})
							.done(function(data) {
								if (data.success) {
									$("#manage_people_grid").trigger("reloadGrid"); // to update checkboxes											
								}
								else {
									alert('{{_("Failed: ")}}'+data.msg);								
								}
					      		$("#get_paste_name_dialog").dialog( "close" );
							})
							.fail(function(jqxhr, textStatus, error) {
						  		alert("Error: "+jqxhr.responseText);
						  		$("#get_paste_name_dialog").dialog( "close" );
							});							
						}
						else {
							alert('{{_("That name is also in use.")}}');
						}
					}
					else {
	    				alert('{{_("Failed: ")}}'+data.msg);
	    	      		$( this ).dialog( "close" );
					}
				})
		    	.fail(function(jqxhr, textStatus, error) {
		    		alert('{{_("Error: ")}}'+jqxhr.responseText);
		      		$( this ).dialog( "close" );
		    	});
	    	},
	    	Cancel: function() {
	      		$( this ).dialog( "close" );
	    	}
		}
	});
});


$(function() {

	var btn = $("#create_people_from_proto_button");
	btn.button();
	btn.click( function() {
		$("#manage_people_grid").jqGrid('restoreRow',lastsel_people);
		var peopleName = null;
		var modelId = $("#people_top_model_select").val()
		if (lastsel_people) {
			peopleName = $("#manage_people_grid").jqGrid('getCell',lastsel_people,'name');
		}
		if (!peopleName || peopleName==false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}check-may-modify?modelId='+modelId)
			.done(function(data) {
				if (data.success) {
					if (data.value) {
						window.location = "{{rootPath}}people-edit?modelId="+modelId+"&protoname='"+peopleName+"'";			
					}
					else {
						alert('{{_("Simulation results have already been generated for this model.  If you change the model, those results will become invalid.  You must either delete those results or create a new copy of the model and modify it instead.")}}');
					}
				}
				else {
					alert('{{_("Failed: ")}}'+data.msg);
				}
			})
			.fail(function(jqxhr, textStatus, error) {
				alert('{{_("Error: ")}}'+jqxhr.responseText);
			});
		}
		
	});

});

$(function() {

	var btn = $("#copy_people_button");
	btn.button();
	btn.click( function() {
		$("#manage_people_grid").jqGrid('restoreRow',lastsel_people);
		var peopleName = null;
		if (lastsel_people) {
			peopleName = $("#manage_people_grid").jqGrid('getCell',lastsel_people,'name');
		}
		if (!peopleName || peopleName==false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}json/copy-type-to-clipboard',
					{name:peopleName, modelId:$("#people_top_model_select").val()})
			.done(function(data) {
				if (data.success) {
					$("#paste_people_button").button("option","disabled",false);
				}
				else {
					alert('{{_("Failed: ")}}'+data.msg);
				}
			})
			.fail(function(jqxhr, textStatus, error) {
				alert('{{_("Error: ")}}'+jqxhr.responseText);
				dlg.data('cb').checked = true;
			});
		}
		
	});

});

$(function() {

	var btn = $("#paste_people_button");
	btn.button({disabled:true});
	btn.click( function() {
		$.getJSON('{{rootPath}}check-may-modify?modelId='+$("#people_top_model_select").val())
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'people'})
					.done(function(data) {
						if (data.success) {
							if (data.value) {
								$.getJSON('{{rootPath}}json/get-clipboard-name')
								.done(function(data) {
									var proposedName = data.value;
									$.getJSON('{{rootPath}}check-unique-hint',
											{modelId:$("#people_top_model_select").val(),typeName:proposedName})
									.done(function(data) {
										if (data.success) {
											if (data.value) {
												$.getJSON('json/paste-clipboard-to-type', {
													modelId:$("#people_top_model_select").val(), 
													type:"people", name:proposedName
												})
												.done(function(data) {
													if (data.success) {
														$("#manage_people_grid").trigger("reloadGrid"); // to update checkboxes											
													}
													else {
														alert('{{_("Failed: ")}}'+data.msg);								
													}
												})
												.fail(function(jqxhr, textStatus, error) {
								  					alert("Error: "+jqxhr.responseText);
												});								
											}
											else {
						    					$("#get_paste_name_dialog").data('modelId',$("#people_top_model_select").val());
												$("#get_paste_name_dlg_new_name").val(data.hint);
												$("#get_paste_name_dialog").dialog("open");
											}
										}
										else {
											alert('{{_("Failed: ")}}'+data.msg);								
										}
									})
									.fail(function(jqxhr, textStatus, error) {
					  					alert("Error: "+jqxhr.responseText);
									});							
								})
				  				.fail(function(jqxhr, textStatus, error) {
				  					alert("Error: "+jqxhr.responseText);
								});
							}
							else {
								alert('{{_("The data on the clipboard is not a Population Type.")}}')
							}
						}
						else {
							alert('{{_("Failed: ")}}'+data.msg);
						}
	    			})
	  				.fail(function(jqxhr, textStatus, error) {
	  					alert("Error: "+jqxhr.responseText);
					});
				}
				else {
					alert('{{_("Simulation results have already been generated for this model.  If you change the model, those results will become invalid.  You must either delete those results or create a new copy of the model and modify it instead.")}}');
				}
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
		})
		.fail(function(jqxhr, textStatus, error) {
			alert('{{_("Error: ")}}'+jqxhr.responseText);
		});
	});
	
	$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'people'})
	.done(function(data) {
		if (data.success) {
			if (data.value) {
				$("#paste_people_button").button("option","disabled",false);
			}
			else {
				$("#paste_people_button").button("option","disabled",true);
			}
		}
		else {
			alert('{{_("Failed: ")}}'+data.msg);
		}
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert("Error: "+jqxhr.responseText);
	});
	

});

$(function() {
	var sel = $("#people_top_model_select");
	sel.change( function() {
		$.getJSON('{{rootPath}}json/set-selected-model', {id:$("#people_top_model_select").val()})
		.done(function(data) {
			sel_model_name = data['name'];
			$("#manage_people_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
			$("#manage_people_grid").trigger("reloadGrid"); // to update checkboxes
	    })
	  	.fail(function(jqxhr, textStatus, error) {
	  		alert("Error: "+jqxhr.responseText);
		});
	});

	$.getJSON('{{rootPath}}list/select-model')
	.done(function(data) {
		var sel = $("#people_top_model_select");
    	sel.append(data['menustr']);
    	sel_model_name = data['selname']
		$("#manage_people_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
		$("#manage_people_grid").trigger("reloadGrid"); // to update checkboxes
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert("Error: "+jqxhr.responseText);
	});
});
  
</script>
 
