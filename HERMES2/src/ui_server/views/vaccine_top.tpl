% title_slogan=_("Database Types")
%rebase outer_wrapper **locals()

% currentType = 'vaccines'
% typesEntries = [
%    ['vaccines', _('Vaccines'),        'vaccines-top'],
%    ['trucks',   _('Transport'),       'truck-top'],
%    ['fridges',  _('Storage'),         'fridge-top'],
%    ['people',   _('Population'),      'people-top'],
%    ['perdiems', _('PerDiems'),        'perdiem-top'],
%    ['staff',    _('Staff'),           'staff-top'],
% ]

% def unpackTypesEntry(te):
%    ret = {}
%    ret['type'] = te[0]
%    ret['name'] = te[1]
%    ret['dbUrl'] = te[2]
%    ret['fullDbURL'] = rootPath + ret['dbUrl'] + '?crmb=clear'
%    return ret
% end

<table>
  <tr>
  %for te in typesEntries:
  %   t = unpackTypesEntry(te)
    <th style="width:120px">
      <button id="{{t['type']}}_button" style="width:100%">{{t['name']}}</button>
    </th>
  %end
  </tr>
  <tr style="height:40px"></tr>
</table>

<script>
$(function() {
    // set up top row buttons
    % for te in typesEntries:
    %   t = unpackTypesEntry(te)
    var btn = $('#{{t['type']}}_button');
    btn.button();
    % if t['type'] == currentType:
    btn.button('disable');
    % else:
    btn.click( function() {
	window.location = "{{t['fullDbURL']}}";
    });
    %end
    %end
});

</script>




<table>
<tr>
<td style="float:left;width:80px">
<h2 style="display:none">Task:</h2>
<table>
<tr><td><button id="create_vaccine_from_proto_button" style="width:100%">
            {{!_('Create')}}
            </button></td></tr>
<tr><td><button id="copy_vaccine_button" style="width:100%">
            {{!_('Copy')}}
            </button></td></tr>
<tr><td><button id="paste_vaccine_button" style="width:100%">
            {{!_('Paste')}}
            </button></td></tr>
</table>
</td>

<td>

<h3 style="display:none">{{_('Known Vaccine Types')}}</h3>

<label for="vaccine_top_model_select">{{_('Showing vaccine types for')}}</label>
<select name="vaccine_top_model_select" id="vaccine_top_model_select"></select>

<label for="vaccine_top_subkey_select">{{_('Grouping subgrids by')}}</label>
<select name="vaccine_top_subkey_select" id="vaccine_top_subkey_select"></select>

<table id="manage_vaccine_grid"></table>
<div id="manage_vaccine_pager"> </div>

</td>
</tr>
</table>

<div id="vaccine_info_dialog" title="This should get replaced"></div>

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

var lastsel_vaccine_subgrid_table_id;
var lastsel_vaccine;
var sel_model_name = null;
var sel_model_id = null;
var sel_subkey_name = null;
var sel_subkey_id = null;


function boxClick(cb,event) {
	if (cb.checked) {
		// The item is being changed from not-in-model to in-model
		event.stopPropagation();
		$.getJSON('{{rootPath}}json/add-type-to-model',{name:cb.value, modelId:$("#vaccine_top_model_select").val()})
		.done(function(data) {
			if (!data.success) {
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
				+ '{{_(" from model ")}}' + $("#vaccine_top_model_select").val() + '{{_("?")}}');
		dlg.data('name',cb.value);
		dlg.data('modelId',$("#vaccine_top_model_select").val());
		dlg.data('cb',cb);
		dlg.dialog('open');
	};
}

function vaccineInfoButtonFormatter(cellvalue, options, rowObject)
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

$("#manage_vaccine_grid").jqGrid({ //set your grid id
   	url:'{{rootPath}}json/manage-vaccine-table-groupings',
	datatype: "json",
	postData: {
		modelId: function() {
          return $("#vaccine_top_model_select").val();
        },
        subkey: function() {
          return $("#vaccine_top_subkey_select option:selected").text();
        }
	},
//	width: '750',   //deprecated with resize_grid
//	height:'auto',
  rowNum:9999, // rowNum=-1 has bugs, suggested solution is absurdly large setting to show all on one page
  
	colNames:[
              "primary_key",
	          "{{_('Name')}}",
	          "{{_('Count')}}"
	],
	colModel:[
              {name:'primary_key', key:true, hidden: true, hidedlg: true},
	          {name:'name', index:'name', width:200},
	          {name:'count', index:'count', width:200}
	],
	pager: '#manage_vaccine_pager',
	pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
    pginput: false, //ditto
	sortname: 'name',
	sortorder: "asc",
	gridview: true,
	viewrecords: true,
	beforeRequest: function() {
        // suppress update until selected model and subkey are known
		return (sel_model_name != null && sel_subkey_name != null);
	},
	rowattr: function(rowdata){
		if (!rowdata.usedin) return {"class":"not-editable-row"};
	},
    caption:"{{ _("Available Vaccine Types") if not defined('smallCaption') else smallCaption }}",
    // subgrid dynamically expands to show grouped rows that all the share
    // same (subkey) value
    subGrid: true,
    // subgrid_id: the id of the div where we will expand the subgrid
    // row_id: is the "RandomKey" used to lookup the subgrid rows
    subGridRowExpanded: function(subgrid_id, row_id) {
       var subgrid_table_id = subgrid_id + "_t";

       //console.log('DEBUG subgrid_id ' + subgrid_id);
       //console.log('DEBUG subgrid_table_id ' + subgrid_table_id);
       //console.log('DEBUG row_id ' + row_id);
	var hideUsedIn = false;
	if (sel_model_name == 'HERMES Database')
	    hideUsedIn = true;

       jQuery("#"+subgrid_id).html("<table id='"+subgrid_table_id+"' class='scroll'></table>");
       jQuery("#"+subgrid_table_id).jqGrid({
          url:'{{rootPath}}json/manage-vaccine-sub-table',
          editurl:'{{rootPath}}edit/edit-vaccine.json',	
          datatype: "json",
          colNames: [
        	"{{_('Name')}}",
	        "{{_('Used in ')}}"+sel_model_name,
	        "{{_('DisplayName')}}",
	        "{{_('Details')}}"
          ],
          colModel: [
	          {name:'name', index:'name', width:200, key:true},
	          {name:'usedin', index:'usedin', align:'center', formatter:checkboxFormatter, hidden:hideUsedIn},
	          {name:'dispnm', index:'dispnm', width:200, editable:true},
	          {name:'info', index:'info', width:110, align:'center', sortable:false,
	        	  formatter:vaccineInfoButtonFormatter}          
          ],
          height: '100%',
          rowNum: -1, // all in one 'page'
          sortname: 'name',
          sortorder: "asc",
          postData: {
            // these are set in the select boxes at the top of the page
		    modelId: function() {
              return $("#vaccine_top_model_select").val();
            },
            subkey: function() {
              return $("#vaccine_top_subkey_select option:selected").text();
            },
            // the value that all rows in the sub grid share for subkey;
            // passed in to the subGridRowExpanded function; row_id is the
            // "RandomKey"
            subval: row_id  	      
          },
          onSelectRow: function(id) {
		    if (id && id!==lastsel_vaccine) {
			    jQuery('#'+subgrid_table_id).jqGrid('saveRow', lastsel_vaccine);
    		    jQuery('#'+subgrid_table_id).jqGrid('editRow', id, {
	        			keys: true,
    		    		extraparam: {modelId: function() {
                            return $("#vaccine_top_model_select").val();
                        }
                    }
			    });
            lastsel_vaccine_subgrid_table_id = subgrid_table_id;
			lastsel_vaccine=id;
		    }
	      },

          gridComplete: function(){
		    $(".hermes_info_button").click(function(event) {
			  $.getJSON('{{rootPath}}json/vaccine-info',{name:unescape($(this).attr('id')), 
				modelId:$("#vaccine_top_model_select").val()})
			  .done(function(data) {
				if (data.success) {
				    $("#vaccine_info_dialog").html(data['htmlstring']);
			    	$("#vaccine_info_dialog").dialog('option','title',data['title']);
					$("#vaccine_info_dialog").dialog("open");		
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
        // set hermify options for subgrids
       }).jqGrid('hermify',{debug:true, subgrid:true, resizable:true});
    }
// parent grid hermify options
}).jqGrid('hermify',{debug:true, subgrid:false, resizable:true, has_subgrid:true});

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_vaccine_grid"
  var offset = $(idGrid).offset() //position of grid on page
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-130);
}
$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
$(window).resize(resize_grid);  //bind resize_grid to window resize

$("#manage_vaccine_grid").jqGrid('navGrid','#manage_vaccine_pager',{edit:false,add:false,del:false});
setPrintGrid('manage_vaccine_grid','manage_vaccine_pager','{{_("Available Vaccines")}}');

$(function() {
	$("#vaccine_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
	$("#confirm_dialog").dialog({
		autoOpen:false, height:"auto", width:"auto", modal:true,
		buttons: {
	    	Ok: function() {
	    		var dlg = $('#confirm_dialog');
	    		$.getJSON('{{rootPath}}json/remove-type-from-model',
	    				{name:dlg.data('name'), modelId:dlg.data('modelId')})
	    		.done(function(data) {
			        if (!data.success) {
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
						{modelId:$("#vaccine_top_model_select").val(),typeName:newNm})
				.done(function(data) {
					if (data.success) {
						if (data.value) {
							$.getJSON('{{rootPath}}json/paste-clipboard-to-type', {
								modelId:$("#vaccine_top_model_select").val(), 
								type:"vaccine", name:newNm
							})
							.done(function(data) {
								if (data.success) {
									$("#manage_vaccine_grid").trigger("reloadGrid"); // to update checkboxes											
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
	var btn = $("#create_vaccine_from_proto_button");
	btn.button();
	btn.click( function() {
		$("#manage_vaccine_grid").jqGrid('restoreRow',lastsel_vaccine);
		var vaccineName = null;
		var modelId = $("#vaccine_top_model_select").val()
		if (lastsel_vaccine && lastsel_vaccine_subgrid_table_id) {
			vaccineName = $("#"+lastsel_vaccine_subgrid_table_id).jqGrid(
                'getCell',lastsel_vaccine,'name');
		}
		if (!lastsel_vaccine_subgrid_table_id ||
                lastsel_vaccine_subgrid_table_id == false ||
                !vaccineName || vaccineName == false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}check-may-modify?modelId='+modelId)
			.done(function(data) {
				if (data.success) {
					if (data.value) {
						window.location = "{{rootPath}}vaccine-edit?modelId=" +
                            modelId + "&protoname='" + vaccineName + "'";
					}
					else {
						alert('{{_("Simulation results have already been ' + 
                            'generated for this model.  If you change the ' +
                            'model, those results will become invalid.  You ' +
                            'must either delete those results or create a ' +
                            'new copy of the model and modify it instead.")}}'
                        );
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

	var btn = $("#copy_vaccine_button");
	btn.button();
	btn.click( function() {
		$("#manage_vaccine_grid").jqGrid('restoreRow',lastsel_vaccine);
		var vaccineName = null;
		if (lastsel_vaccine && lastsel_vaccine_subgrid_table_id) {
			vaccineName = $("#" + lastsel_vaccine_subgrid_table_id).jqGrid(
                'getCell',lastsel_vaccine,'name');
		}
		if (!lastsel_vaccine_subgrid_table_id ||
                lastsel_vaccine_subgrid_table_id == false ||
                !vaccineName || vaccineName == false) {
			alert('{{_("No Selection")}}');
		}
		else {
			$.getJSON('{{rootPath}}json/copy-type-to-clipboard',
					{name:vaccineName, modelId:$("#vaccine_top_model_select").val()})
			.done(function(data) {
				if (data.success) {
					$("#paste_vaccine_button").button("option","disabled",false);
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

	var btn = $("#paste_vaccine_button");
	btn.button({disabled:true});
	btn.click( function() {

		$.getJSON(
            '{{rootPath}}check-may-modify?modelId=' +
            $("#vaccine_top_model_select").val()
                ).then(
                    // success
                    function(data) {
                        console.log(data);
                        if (data.value) {
                            return $.getJSON('{{rootPath}}json/test-clipboard-type',{type:'vaccine'});
                        }
                        else {
                            alert('{{_("Simulation results have already been generated for this model.  ' + 
                                'If you change the model, those results will become invalid.  ' + 
                                'You must either delete those results or create a ' +
                                'new copy of the model and modify it instead.")}}');
                        }
                    },
                    // failure
                    function(jqxhr, textStatus, error) {
	  					alert("Error 5: "+jqxhr.responseText);
                    }
                ).then(
                    // success
                    function(data) {
                        console.log(data);
                        if (data.value) {
	    				    return $.getJSON('{{rootPath}}json/get-clipboard-name');
                        }
                        else {
                            alert('{{_("The data on the clipboard is not a Vaccine Type.")}}');
                        }
                    },
                    // failure
                    function(jqxhr, textStatus, error) {
	  					alert("Error 4: "+jqxhr.responseText);
                    }
                ).then(
                    // success
                    function(data) {
                        console.log(data);
						var proposedName = data.value;
						return $.getJSON('{{rootPath}}check-unique-hint',
							{
                                modelId:$("#vaccine_top_model_select").val(),
                                typeName:proposedName
                            });
                    },
                    // failure
                    function(jqxhr, textStatus, error) {
	  					alert("Error 3: "+jqxhr.responseText);
                    }
                ).then(
                    // success
                    function(data) {
                        console.log(data);
						if (data.value) {
                            var proposedName = data.value;
							return $.getJSON('{{rootPath}}json/paste-clipboard-to-type',
                                {
                                    modelId:$("#vaccine_top_model_select").val(),
                                    type:"vaccine", name:proposedName
                                });
                        }
                        else {
						    $("#get_paste_name_dialog").data(
                                'modelId',$("#vaccine_top_model_select").val());
							$("#get_paste_name_dlg_new_name").val(data.hint);
							$("#get_paste_name_dialog").dialog("open");
						}
                    },
                    // failure
                    function(jqxhr, textStatus, error) {
	  					alert("Error 2: "+jqxhr.responseText);
                    }
                ).then(
                    // success
                    function(data) {
                        console.log(data);
                        return $("#manage_vaccine_grid").trigger("reloadGrid");
                    },
                    // failure
                    function(jqxhr, textStatus, error) {
						alert("Error 1: "+jqxhr.responseText);
					}
                );

	});
	
	$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'vaccine'})
	.done(function(data) {
		if (data.success) {
			if (data.value) {
				$("#paste_vaccine_button").button("option","disabled",false);
			}
			else {
				$("#paste_vaccine_button").button("option","disabled",true);
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
	var sel = $("#vaccine_top_model_select");
	sel.change( function() {
		$.getJSON('{{rootPath}}json/set-selected-model', {id:$("#vaccine_top_model_select").val()})
		.done(function(data) {
			sel_model_name = data['name'];
//			$("#manage_vaccine_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
			$("#manage_vaccine_grid").trigger("reloadGrid"); // to update checkboxes
	    })
	  	.fail(function(jqxhr, textStatus, error) {
	  		alert("Error: "+jqxhr.responseText);
		});
	});

    // trigger reload when the 'subkey' (the subgrid grouping key) is changed
	$("#vaccine_top_subkey_select").change( function() {
		$("#manage_vaccine_grid").trigger("reloadGrid");
	});

    $.getJSON('{{rootPath}}list/select-model', {'includeRef' : 1})
	.done(function(data) {
		var sel = $("#vaccine_top_model_select");
    	sel.append(data['menustr']);
    	sel_model_name = data['selname'];
        sel_model_id = data['selid'];
        $("#vaccine_top_model_select").val(sel_model_id);
        // make the subkey, subval available for later use
        $.getJSON('{{rootPath}}list/select-subkey',
          {'modelId': sel_model_id}
          ).done(function(data) {
    		var subkey_sel = $("#vaccine_top_subkey_select");
        	subkey_sel.append(data['menustr']);
            sel_subkey_name = data['selname']; 
            sel_subkey_id = data['selid']; 
            $("#vaccine_top_subkey_select").val(sel_subkey_id);
            $("#manage_vaccine_grid").trigger("reloadGrid");
        })
      	.fail(function(jqxhr, textStatus, error) {
      		alert("Error: "+jqxhr.responseText);
    	});
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert("Error: "+jqxhr.responseText);
	});

});
  
</script>

<!-- this was the original error handling, replaced by depasse.
// ... line 510 ...
//		$.getJSON('{{rootPath}}check-may-modify?modelId='+$("#vaccine_top_model_select").val())
//		.done(function(data) {
//			if (data.success) {
//				if (data.value) {
//					$.getJSON('{{rootPath}}json/test-clipboard-type',{type:'vaccine'})
//					.done(function(data) {
//						if (data.success) {
//							if (data.value) {
//								$.getJSON('{{rootPath}}json/get-clipboard-name')
//								.done(function(data) {
//									var proposedName = data.value;
//									$.getJSON('{{rootPath}}check-unique-hint',
//											{modelId:$("#vaccine_top_model_select").val(),typeName:proposedName})
//									.done(function(data) {
//										if (data.success) {
//											if (data.value) {
//												$.getJSON('{{rootPath}}json/paste-clipboard-to-type', {
//													modelId:$("#vaccine_top_model_select").val(), 
//													type:"vaccine", name:proposedName
//												})
//												.done(function(data) {
//													if (data.success) {
//														$("#manage_vaccine_grid").trigger("reloadGrid"); // to update checkboxes											
//													}
//													else {
//														alert('{{_("Failed: ")}}'+data.msg);								
//													}
//												})
//												.fail(function(jqxhr, textStatus, error) {
//								  					alert("Error 1: "+jqxhr.responseText);
//												});							
//											}
//											else {
//						    					$("#get_paste_name_dialog").data('modelId',$("#vaccine_top_model_select").val());
//												$("#get_paste_name_dlg_new_name").val(data.hint);
//												$("#get_paste_name_dialog").dialog("open");
//											}
//										}
//										else {
//											alert('{{_("Failed: ")}}'+data.msg);								
//										}
//									})
//									.fail(function(jqxhr, textStatus, error) {
//					  					alert("Error 2: "+jqxhr.responseText);
//									});							
//								})
//				  				.fail(function(jqxhr, textStatus, error) {
//				  					alert("Error 3: "+jqxhr.responseText);
//								});
//							}
//							else {
//								alert('{{_("The data on the clipboard is not a Vaccine Type.")}}')
//							}
//						}
//						else {
//							alert('{{_("Failed: ")}}'+data.msg);
//						}
//	    			})
//	  				.fail(function(jqxhr, textStatus, error) {
//	  					alert("Error 4: "+jqxhr.responseText);
//					});
//				}
//				else {
//					alert('{{_("Simulation results have already been generated for this model.  If you change the model, those results will become invalid.  You must either delete those results or create a new copy of the model and modify it instead.")}}');
//				}
//			}
//			else {
//				alert('{{_("Failed: ")}}'+data.msg);
//			}
//		})
//		.fail(function(jqxhr, textStatus, error) {
//			alert('{{_("Error 5: ")}}'+jqxhr.responseText);
//		});
//
-->


