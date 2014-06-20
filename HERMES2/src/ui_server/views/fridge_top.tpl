%rebase outer_wrapper **locals()

<table>
<tr><td  style="border-style:solid">
<h2>Task:</h2>
<table>
<tr><td><button id="create_fridge_from_proto_button" style="width:100%">{{!_('Create')}}</button></td></tr>
<tr><td><button id="copy_fridge_button" style="width:100%">{{!_('Copy')}}</button></td></tr>
<tr><td><button id="paste_fridge_button" style="width:100%">{{!_('Paste')}}</button></td></tr>
</table>
</td>

<td  style="border-style:solid">
<h3>{{_('Known Cold Storage Types')}}</h3>
<div name="model_select" id="model_select"></div>
<table id="manage_fridge_grid"></table>
<div id="manage_fridge_pager"> </div>

</td>
</tr>
</table>

<div id="fridge_info_dialog" title="This should get replaced"></div>

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

var lastsel_fridge;
var sel_model_name = null;

function getRemoveConfirm(data, typeName) {
	// Returns a promise
	var defer = $.Deferred();
	var markup;
	if (data.value.length == 0) {
		markup = '{{_("Really remove all instances of ")}}' + typeName + '{{_(" from the model?")}}';
	}
	else if (data.value.length == 1) {
		var s = data.value[0];
		markup = '{{_("This storage type is used by the transport type ")}}'+s+'{{_(". Do you want to remove it as well?")}}';
	}
	else {
		var s = '<ul><li>'+data.value.join('</li><li>')+'</li></ul>';
		markup = '{{_("This is used by the following transport types:")}}'+s+'{{_("Do you want to remove them as well?")}}';
	}
	$('<div></div>').html(markup)
	.dialog({
		autoOpen: true,
		modal: true,
		title: '{{_("Confirm Additional Removals?")}}',
		close: function() { $(this).dialog('destroy'); },
		buttons: {
			'{{_("Remove")}}': function() {
				$(this).dialog("close");
				defer.resolve({success:true});
			},
			'{{_("Cancel")}}': function() { 
				$(this).dialog("close");
				defer.reject({success:false, msg:'Cancelled'});
			}
		}
	});
	return defer.promise();
};

	
function boxClick(cb,event) {
	if (cb.checked) {
		// The item is being changed from not-in-model to in-model
		event.stopPropagation();
		$.getJSON('{{rootPath}}json/add-type-to-model',{name:cb.value, modelId:$('#model_select').modelSelector('selId')})
		.done(function(data) {
			if (data.success) {
				$("#manage_fridge_grid").trigger("reloadGrid"); // to update checkboxes
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
		
		$.getJSON('{{rootPath}}json/type-check-dependent-types',{name:cb.value, modelId:$("#model_select").modelSelector('selId')})
		.then( function(data) {
			if (data.success) return getRemoveConfirm(data, cb.value);
			else return $.Deferred().reject(data).promise();
		})
		.then( function(data) {
			return $.getJSON('{{rootPath}}json/remove-type-from-model',{name:cb.value, modelId:$("#model_select").modelSelector('selId')});
		})
		.then( function(data) {
			var defer = $.Deferred();
			if (data.success) defer.resolve(data);
			else defer.reject(data);
			return defer;
		})
		.done ( function(data) { $("#manage_fridge_grid").trigger("reloadGrid"); } ) // to update checkboxes
		.fail( reportError )
		.fail( function(data) { cb.checked = true; } );
	};
}

function fridgeInfoButtonFormatter(cellvalue, options, rowObject)
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

$("#manage_fridge_grid").jqGrid({ //set your grid id
   	url:'{{rootPath}}json/manage-fridge-table',
    editurl:'{{rootPath}}edit/edit-fridge.json',	
	datatype: "json",
	postData: {
		modelId: function() { return $('#model_select').modelSelector('selId'); }
	},
	//width: 750, //deprecated with resize_grid
	//height:401, //temporarily optimized for minimum 1024x600
	rowNum:9999, // temporary until storage types are grouped in a nested grid
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
	        	  formatter:fridgeInfoButtonFormatter}
	], //define column models
	pager: '#manage_fridge_pager', //set your pager div id
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
		if(id && id!==lastsel_fridge){
			jQuery('#manage_fridge_grid').jqGrid('saveRow',lastsel_fridge);
			jQuery('#manage_fridge_grid').jqGrid('editRow',id,{
				keys:true,
				extraparam: { modelId: function() { return $('#model_select').modelSelector('selId'); }}
			});
			lastsel_fridge=id;
		}
	},
	gridComplete: function(){
		$(".hermes_info_button").click(function(event) {
			$.getJSON('{{rootPath}}json/fridge-info',{name:unescape($(this).attr('id')), modelId:$('#model_select').modelSelector('selId')})
			.done(function(data) {
				if (data.success) {									
					$("#fridge_info_dialog").html(data['htmlstring']);
					$("#fridge_info_dialog").dialog('option','title',data['title']);
					$("#fridge_info_dialog").dialog("open");
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
    caption:"{{_("Available Cold Storage Types")}}"
}).jqGrid('hermify',{debug:true});
$("#manage_fridge_grid").jqGrid('navGrid','#manage_fridge_pager',{edit:false,add:false,del:false});

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_fridge_grid"
  var offset = $(idGrid).offset() //position of grid on page
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-130);
}
$(document).ready(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
$(window).resize(resize_grid);  //bind resize_grid to window resize


$(function() {
	$("#fridge_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function() {
	$("#get_paste_name_dialog").dialog({
		autoOpen:false, height:"auto", width:300, modal:true,
		buttons: {
	    	Ok: function() {
	    		var newNm = $("#get_paste_name_dlg_new_name").val();
				$.getJSON('{{rootPath}}check-unique-hint',
						{modelId:$('#model_select').modelSelector('selId'),typeName:newNm})
				.done(function(data) {
					if (data.success) {
						if (data.value) {
							$.getJSON('{{rootPath}}json/paste-clipboard-to-type', {
								modelId:$('#model_select').modelSelector('selId'), 
								type:"fridge", name:newNm
							})
							.done(function(data) {
								if (data.success) {
									$("#manage_fridge_grid").trigger("reloadGrid"); // to update checkboxes											
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

	var btn = $("#create_fridge_from_proto_button");
	btn.button();
	btn.click( function() {
		$("#manage_fridge_grid").jqGrid('restoreRow',lastsel_fridge);
		var fridgeName = null;
		var modelId = $('#model_select').modelSelector('selId');
		if (lastsel_fridge) {
			fridgeName = $("#manage_fridge_grid").jqGrid('getCell',lastsel_fridge,'name');
		}
		if (!fridgeName || fridgeName==false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}check-may-modify?modelId='+modelId)
			.done(function(data) {
				if (data.success) {
					if (data.value) {
						window.location = "{{rootPath}}fridge-edit?modelId="+modelId+"&protoname='"+fridgeName+"'";			
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

	var btn = $("#copy_fridge_button");
	btn.button();
	btn.click( function() {
		$("#manage_fridge_grid").jqGrid('restoreRow',lastsel_fridge);
		var fridgeName = null;
		if (lastsel_fridge) {
			fridgeName = $("#manage_fridge_grid").jqGrid('getCell',lastsel_fridge,'name');
		}
		if (!fridgeName || fridgeName==false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}json/copy-type-to-clipboard',
					{name:fridgeName, modelId:$('#model_select').modelSelector('selId')})
			.done(function(data) {
				if (data.success) {
					$("#paste_fridge_button").button("option","disabled",false);
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

	var btn = $("#paste_fridge_button");
	btn.button({disabled:true});
	btn.click( function() {
		$.getJSON('{{rootPath}}check-may-modify?modelId='+$('#model_select').modelSelector('selId'))
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'fridge'})
					.done(function(data) {
						if (data.success) {
							if (data.value) {
								$.getJSON('{{rootPath}}json/get-clipboard-name')
								.done(function(data) {
									var proposedName = data.value;
									$.getJSON('{{rootPath}}check-unique-hint',
											{modelId:$('#model_select').modelSelector('selId'),typeName:proposedName})
									.done(function(data) {
										if (data.success) {
											if (data.value) {
												$.getJSON('{{rootPath}}json/paste-clipboard-to-type', {
													modelId:$('#model_select').modelSelector('selId'), 
													type:"fridge", name:proposedName
												})
												.done(function(data) {
													if (data.success) {
														$("#manage_fridge_grid").trigger("reloadGrid"); // to update checkboxes											
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
						    					$("#get_paste_name_dialog").data('modelId',$('#model_select').modelSelector('selId'));
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
								alert('{{_("The data on the clipboard is not a Cold Storage Type.")}}')
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
	
	$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'fridge'})
	.done(function(data) {
		if (data.success) {
			if (data.value) {
				$("#paste_fridge_button").button("option","disabled",false);
			}
			else {
				$("#paste_fridge_button").button("option","disabled",true);
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
	$("#model_select").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing cold storage types for")}}',
		afterBuild:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
			var modelName = this.modelSelector('selName');
			sel_model_name = modelName;
			$("#manage_fridge_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+modelName);
			$("#manage_fridge_grid").trigger("reloadGrid"); // to update checkboxes
		},
		onChange:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
			var modelName = this.modelSelector('selName');
			sel_model_name = modelName;
			$("#manage_fridge_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+modelName);
			$("#manage_fridge_grid").trigger("reloadGrid"); // to update checkboxes
		},
	});
});
  
</script>
 