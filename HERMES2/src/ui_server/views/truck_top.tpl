% title_slogan=_("Transport Types")
%rebase outer_wrapper **locals()

<table>
<tr><td  style="border-style:solid">
<h2>Task:</h2>
<table>
<tr><td><button id="create_truck_from_proto_button" style="width:100%">{{!_('Create')}}</button></td></tr>
<tr><td><button id="copy_truck_button" style="width:100%">{{!_('Copy')}}</button></td></tr>
<tr><td><button id="paste_truck_button" style="width:100%">{{!_('Paste')}}</button></td></tr>
</table>
</td>

<td  style="border-style:solid">
<h3>{{_('Known Transport Types')}}</h3>
<label for="truck_top_model_select">{{_('Showing transport types for')}}</label>
<select name="truck_top_model_select" id="truck_top_model_select"></select>
<table id="manage_truck_grid"></table>
<div id="manage_truck_pager"> </div>

</td>
</tr>
</table>

<div id="truck_info_dialog" title="This should get replaced"></div>

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

var lastsel_truck;
var sel_model_name = null;

function getImportConfirm(data, typeName) {
	// Returns a promise
	var defer = $.Deferred();
	var markup;
	if (data.value.length == 0) {
		defer.resolve({success:true});
	}
	else {
		if (data.value.length == 1) {
			var s = data.value[0];
			markup = '{{_("This transport type uses the storage type ")}}'+s+'{{_(". Do you want to include it as well?")}}';
		}
		else {
			var s = '<ul><li>'+data.value.join('</li><li>')+'</li></ul>';
			markup = '{{_("This uses the following storage types internally:")}}'+s+'{{_("Do you want to include them as well?")}}';
		}
		$('<div></div>').html(markup)
		.append('<br>'+'{{_("The alternative is to create a modified version that does not use these types.")}}')
		.dialog({
			autoOpen: true,
			modal: true,
			title: '{{_("Confirm Additional Imports?")}}',
			close: function() { $(this).dialog('destroy'); },
			buttons: {
				'{{_("Import")}}': function() {
					$(this).dialog("close");
					defer.resolve({success:true});
				},
				'{{_("Cancel")}}': function() { 
					$(this).dialog("close");
					defer.reject({success:false, msg:'Cancelled'});
				}
			}
		});
	}
	return defer.promise();
};

function boxClick(cb,event) {
	if (cb.checked) {
	
		// The item is being changed from not-in-model to in-model
		event.stopPropagation();
		$.getJSON('{{rootPath}}json/type-check-type-dependencies',{name:cb.value, modelId:$("#truck_top_model_select").val()})
		.then( function(data) {
			if (data.success) return getImportConfirm(data, cb.value);
			else return $.Deferred().reject(data).promise();
		})
		.then( function(data) {
			return $.getJSON('{{rootPath}}json/add-type-to-model',{name:cb.value, modelId:$("#truck_top_model_select").val()});
		})
		.then( function(data) {
			if (data.success) return $.Deferred().resolve(data);
			else return $.Deferred().reject(data);
		})
		.done ( function(data) { $("#manage_truck_grid").trigger("reloadGrid"); } ) // to update checkboxes
		.fail( reportError )
		.fail( function(data) { cb.checked = false; } );
		
	}
	else { 
		// The item is being removed from the model.
		event.stopPropagation();
		var dlg = $('#confirm_dialog')
		dlg.html('{{_("Really remove all instances of ")}}' + cb.value 
				+ '{{_("from model ")}}' + $("#truck_top_model_select").val() + '{{_("?")}}');
		dlg.data('name',cb.value);
		dlg.data('modelId',$("#truck_top_model_select").val());
		dlg.data('cb',cb);
		dlg.dialog('open');
	};
}

function truckInfoButtonFormatter(cellvalue, options, rowObject)
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

$("#manage_truck_grid").jqGrid({ //set your grid id
   	url:'{{rootPath}}json/manage-truck-table',
    editurl:'{{rootPath}}edit/edit-truck.json',	
	datatype: "json",
	postData: {
		modelId: function() { return $("#truck_top_model_select").val(); }
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
	        	  formatter:truckInfoButtonFormatter}
	], //define column models
	pager: '#manage_truck_pager', //set your pager div id
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
		if(id && id!==lastsel_truck){
			jQuery('#manage_truck_grid').jqGrid('saveRow',lastsel_truck);
			jQuery('#manage_truck_grid').jqGrid('editRow',id,{
				keys:true,
				extraparam: { modelId: function() { return $("#truck_top_model_select").val(); }}
			});
			lastsel_truck=id;
		}
	},
	gridComplete: function(){
		$(".hermes_info_button").click(function(event) {
			$.getJSON('{{rootPath}}json/truck-info',{name:unescape($(this).attr('id')), modelId:$("#truck_top_model_select").val()})
			.done(function(data) {
				if (data.success) {
					$("#truck_info_dialog").html(data['htmlstring']);
					$("#truck_info_dialog").dialog('option','title',data['title']);
					$("#truck_info_dialog").dialog("open");	
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
    caption:"{{_("Available Transport Types")}}"
}).jqGrid('hermify',{debug:true});
$("#manage_truck_grid").jqGrid('navGrid','#manage_truck_pager',{edit:false,add:false,del:false});

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_truck_grid"
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
	$("#truck_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
	$("#confirm_dialog").dialog({
		autoOpen:false, height:"auto", width:"auto", modal:true,
		buttons: {
	    	Ok: function() {
	    		var dlg = $('#confirm_dialog');
	    		$.getJSON('{{rootPath}}json/remove-type-from-model',
	    				{name:dlg.data('name'), modelId:dlg.data('modelId')})
	    		.done(function(data) {
	    			if (data.success) {
	    				$("#manage_truck_grid").trigger("reloadGrid"); // to update checkboxes
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
						{modelId:$("#truck_top_model_select").val(),typeName:newNm})
				.done(function(data) {
					if (data.success) {
						if (data.value) {
							$.getJSON('{{rootPath}}json/paste-clipboard-to-type', {
								modelId:$("#truck_top_model_select").val(), 
								type:"truck", name:newNm
							})
							.done(function(data) {
								if (data.success) {
									$("#manage_truck_grid").trigger("reloadGrid"); // to update checkboxes											
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

	var btn = $("#create_truck_from_proto_button");
	btn.button();
	btn.click( function() {
		$("#manage_truck_grid").jqGrid('restoreRow',lastsel_truck);
		var truckName = null;
		var modelId = $("#truck_top_model_select").val();
		if (lastsel_truck) {
			truckName = $("#manage_truck_grid").jqGrid('getCell',lastsel_truck,'name');
		}
		if (!truckName || truckName==false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}check-may-modify?modelId='+modelId)
			.done(function(data) {
				if (data.success) {
					if (data.value) {
						window.location = "{{rootPath}}truck-edit?modelId="+modelId+"&protoname='"+truckName+"'";			
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

	var btn = $("#copy_truck_button");
	btn.button();
	btn.click( function() {
		$("#manage_truck_grid").jqGrid('restoreRow',lastsel_truck);
		var truckName = null;
		if (lastsel_truck) {
			truckName = $("#manage_truck_grid").jqGrid('getCell',lastsel_truck,'name');
		}
		if (!truckName || truckName==false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}json/copy-type-to-clipboard',
					{name:truckName, modelId:$("#truck_top_model_select").val()})
			.done(function(data) {
				if (data.success) {
					$("#paste_truck_button").button("option","disabled",false);
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

	var btn = $("#paste_truck_button");
	btn.button({disabled:true});
	btn.click( function() {
		$.getJSON('{{rootPath}}check-may-modify?modelId='+$("#truck_top_model_select").val())
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'truck'})
					.done(function(data) {
						if (data.success) {
							if (data.value) {
								$.getJSON('{{rootPath}}json/get-clipboard-name')
								.done(function(data) {
									var proposedName = data.value;
									$.getJSON('{{rootPath}}check-unique-hint',
											{modelId:$("#truck_top_model_select").val(),typeName:proposedName})
									.done(function(data) {
										if (data.success) {
											if (data.value) {
												$.getJSON('{{rootPath}}json/paste-clipboard-to-type', {
													modelId:$("#truck_top_model_select").val(), 
													type:"truck", name:proposedName
												})
												.done(function(data) {
													if (data.success) {
														$("#manage_truck_grid").trigger("reloadGrid"); // to update checkboxes											
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
						    					$("#get_paste_name_dialog").data('modelId',$("#truck_top_model_select").val());
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
								alert('{{_("The data on the clipboard is not a Transport Type.")}}')
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
	
	$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'truck'})
	.done(function(data) {
		if (data.success) {
			if (data.value) {
				$("#paste_truck_button").button("option","disabled",false);
			}
			else {
				$("#paste_truck_button").button("option","disabled",true);
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
	var sel = $("#truck_top_model_select");
	sel.change( function() {
		$.getJSON('{{rootPath}}json/set-selected-model', {id:$("#truck_top_model_select").val()})
		.done(function(data) {
			sel_model_name = data['name'];
			$("#manage_truck_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
			$("#manage_truck_grid").trigger("reloadGrid"); // to update checkboxes
	    })
	  	.fail(function(jqxhr, textStatus, error) {
	  		alert("Error: "+jqxhr.responseText);
		});
	});

	$.getJSON('{{rootPath}}list/select-model')
	.done(function(data) {
		var sel = $("#truck_top_model_select");
    	sel.append(data['menustr']);
    	sel_model_name = data['selname']
		$("#manage_truck_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
		$("#manage_truck_grid").trigger("reloadGrid"); // to update checkboxes
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert("Error: "+jqxhr.responseText);
	});
});
  
</script>
 
