%rebase outer_wrapper **locals()
<!---
-->
<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>
		</td>
	</tr>
	<tr>
		<td width=100%>
			<table id="truck_cost_grid"></table>
			<div id="truck_cost_pager"> </div>
		</td>
	</tr>
</table>

<div id="truck_info_dialog" title="This should get replaced"></div>

<script>
{ // local scope

function updateAllButGrid(modelId) {
	$.getJSON('{{rootPath}}json/get-cost-info-truck',{modelId:modelId})
	.done(function(data) {
		if (data.success) {
			// Nothing to do so far
		}
	    else {
	    	alert('{{_("Failed: ")}}'+data.msg);
	    }
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert('{{_("Error: ")}}'+jqxhr.responseText);
	});
		
};

function updatePage(modelId) {
	updateAllButGrid(modelId);
	$("#truck_cost_grid").trigger("reloadGrid");
}

function truckInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<div class=\"hermes_button_triple\" id=\""+escape(cellvalue)+"\"></div>";
	/*
	return "<button type=\"button\" class=\"this_edit_button\" id="+escape(cellvalue)+">Edit</button>" +
			"<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>" +
			"<button type=\"button\" class=\"this_info_button\" id="+escape(cellvalue)+" disabled>Del</button>";
	*/
};

function floatCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value)))
		return true;
	else return false;
}


function priceCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value)))
		return true;
	else {
		return false;
	}
}

function updateEditDlgTitle(btnStr, $form, rowid, gridId, prefix) {
	var $mySpan = $form.parents('.ui-jqdialog').children('.ui-jqdialog-titlebar').children('span');
	var $g = $('#'+gridId);
	var ids = $g.jqGrid('getDataIDs');
	var idx = ids.indexOf(rowid);
	if (btnStr == 'next') {
		idx += 1;
		if (idx > ids.length) idx = 0;
	}
	else if (btnStr == 'same') {
		// do nothing
	}
	else {
		// prev
		idx -= 1;
		if (idx<0) idx = ids.length - 1;
	}
	var newDisplayName = $g.jqGrid('getCell', ids[idx], 'displayname');
	$mySpan.html(prefix + newDisplayName);

	var units = $g.jqGrid('getCell',ids[idx],"fuelrateunits");
	var fuel = $g.jqGrid('getCell',ids[idx],"fuel");
	var $elt = $form.find('#tr_fuelrate').find('td').first();
	$elt.text(units + ' ' + fuel);
}

function buildPage(modelId) {
	updateAllButGrid(modelId);

	$("#truck_cost_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-truck-cost-table',
	    editurl:'{{rootPath}}edit/edit-cost-truck',
		datatype: "json",
		jsonReader: {
				root:'rows',
				repeatitems:false,
				id:'name'
		},
		postData: {
			modelId: function() { return $('#model_sel_widget').modelSelector('selId'); }
		},
		rowNum:9999, // all on one page
		colNames:[
		          "{{_('TrueName')}}",
		          "{{_('Name')}}",
		          "{{_('Base Cost')}}",
		          "{{_('Currency')}}",
		          "{{_('Base Cost Year')}}",
		          "{{_('Km To Amortize')}}",
		          "{{_('Fuel Type')}}",		          
		          "{{_('Fuel Consumption')}}",
		          "{{_('Units')}}",
		          "{{_('Of')}}",
		          "{{_('Details')}}"		          
		], //define column names
		colModel:[
		          {name:'name', jsonmap:'name', index:'name', hidden:true, key:true},
		          {name:'displayname', jsonmap:'displayname', index:'displayname', width:400},
		          {name:'basecost', jsonmap:'basecost', index:'basecost', jsonmapwidth:100, align:'center', 
		        		  formatter:'currency', formatoptions:{defaultValue:''},
		        		  editable:true, editrules:{ 
			        		  custom:true, 
			        		  custom_func: function(value,colname) {
			        			  if (priceCheck(value))
			        				  return [true,''];
			        			  else
			        				  return [false,'{{_("Please enter a valid price for Base Cost")}}'];
			        		  }
			        	  }
		          },
		          {name:'currency', jsonmap:'currency', index:'currency', width:70, align:'center', sortable:true,
		        	  editable:true,
		        	  edittype:'custom',
		        	  editoptions: {
		        		  custom_element:function(value, options){
		  					  var $divElem = $($.parseHTML("<div class='hermes_currency_selector'>"+value+"</div>"));
		  					  var sel = $divElem.text();
		  					  var args = {
		  							  widget:'currencySelector',
		  							  modelId:function() { return $('#model_sel_widget').modelSelector('selId'); },
		  							  label:'',
		  							  recreate:true
		  					  }
		  					  if (sel) args['selected'] = sel;
		  					  if (sel=='') sel='???';
		  					  $divElem.hrmWidget(args);
		        			  return $divElem;
		        		  },
		        		  custom_value:function(elem, op, value){
		        			  if (op=='get') {
		        				  return $(elem).currencySelector('selId');
		        			  }
		        			  else if (op=='set') {
		        				  $(elem).currencySelector('selId',value);
		        			  }
		        		  }
		        	  }
		          },
		          {name:'basecostyear', jsonmap:'basecostyear', index:'basecostyear', align:'center',
		        	  editable:true, edittype:'text', editrules:{integer:true, minValue:2000, maxValue:3000}
		          },
		          {name:'amortkm', jsonmap:'amortizationkm', index:'amortizationkm', align:'center',
		        	  editable:true, edittype:'text', 
		        	  editrules:{
		        		  custom:true,
		        		  custom_func: function(value,colname) {
		        			  if (floatCheck(value))
		        				  return [true,''];
		        			  else
		        				  return [false,'{{_("Please enter a valid number of kilometers to amortize this vehicle")}}'];		        			  
		        		  }
		        	  }
		          },
		          {name:'fuelcode', jsonmap:'fuelcode', index:'fuelcode', hidden:true, editable:true,
			        	editrules:{edithidden:true},
				        edittype: 'custom',
				        editoptions: {
				        	custom_element:function(value, options){
				  				var $divElem = $($.parseHTML("<div class='hermes_energy_selector'>"+value+"</div>"));
				  				var sel = $divElem.text();
				  				var args = {
				  						widget:'energySelector',
				  						modelId:function() { return $('#model_sel_widget').modelSelector('selId'); },
				  						OptionURL:'{{rootPath}}list/select-fuel',
				  						label:'',
				  						canBeBlank:true
				  				}
				  				if (sel) args['selected'] = sel;
				  				$divElem.hrmWidget(args);
				        		return $divElem;
				        	},
				        	custom_value:function(elem, op, value){
				        		if (op=='get') {
				        			return $(elem).energySelector('selId');
				        		}
				        		else if (op=='set') {
				        			$(elem).energySelector('selId',value);
				        		}
				        	}
				        }
			      },
		          {name:'fuelrate', jsonmap: 'fuelrate', index:'fuelrate', editable:true, edittype:'text', width:100, align:'center', 
		        	  formatter:'currency', formatoptions:{defaultValue:''},
		        	  editable:true, 
		        	  editrules:{
		        		  custom:true, 
		        		  custom_func: function(value,colname) {
		        			  if (floatCheck(value))
		        				  return [true,''];
		        			  else
		        				  return [false,'{{_("Please enter a valid price for Ongoing Cost")}}'];
		        		  }
				      	}
		          },
		          {name:'fuelrateunits', jsonmap: 'fuelrateunits', index:'fuelrateunits', width:100, align:'center'},
		          {name:'fuel', jsonmap: 'fuel', index:'fuel', align:'center', editable:false},
		          {name:'info', jsonmap: 'detail', index:'info', width:140, align:'center', sortable:false, 
		        	  formatter:truckInfoButtonFormatter}
		          
		], //define column models
		pager: 'truck_cost_pager', //set your pager div id
		pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
		pginput: false, //ditto
		sortname: 'name', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
		sortorder: "asc", //sort order; optional
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
		beforeSelectRow: function(rowid, e) {
		    return false;
		},
		gridComplete: function(){
			$('.hermes_button_triple').hrmWidget({
				widget:'buttontriple',
				onInfo:function(event) {
					var id = unescape($(this).parent().attr("id"));
					$.getJSON('{{rootPath}}json/truck-info',{name:id, modelId:$('#model_sel_widget').modelSelector('selId')})
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
				},
				onEdit:function(event){
					var id = unescape($(this).parent().attr("id"));
					var devName = $("#truck_cost_grid").jqGrid('getCell',id,"displayname");
					var units = $("#truck_cost_grid").jqGrid('getCell',id,"fuelrateunits");
					var fuel = $("#truck_cost_grid").jqGrid('getCell',id,"fuel");
					$("#truck_cost_grid").jqGrid('editGridRow',id,{
						closeAfterEdit:false,
						bSubmit: "Save",
						bCancel: "Done",
						closeOnEscape:true,
	                  	jqModal:true,
	                  	viewPagerButtons:true,
	                  	mType:"POST",
	                  	modal:true,
	                  	editData: {
	                  		modelId: function() { 
	                  			return $('#model_sel_widget').modelSelector('selId'); 
	        				}
	                  	},
	                  	editCaption:'{{_("Edit Cost Information for ")}}' + devName,
	                  	savekey:[true,13],
	                  	afterSubmit:function(response,postData){
	                  		var data = $.parseJSON(response.responseText);
	                  		if (data.success) {
	                  			return [true];
	                  		}
	                  		else return [false,data.msg];
	                  	},
	            		beforeShowForm:function($form) {
	            			var $elt = $form.find('#tr_fuelrate').find('td').first();
	            			$elt.text(units + ' ' + fuel);
	            		},
	            		afterComplete:function(response, postData, $form) {
	            			updateEditDlgTitle('same', $form, postData.id, 'truck_cost_grid', '{{_("Edit Cost Information for ")}}');
	            		},
	            		onclickPgButtons:function( btnStr, $form, rowid) {
	            			updateEditDlgTitle(btnStr, $form, rowid, 'truck_cost_grid', '{{_("Edit Cost Information for ")}}');
	            		}
					});
				}
			});
		},
		loadError: function(xhr,status,error){
	    	alert('{{_("Error: ")}}'+status);
		},
		beforeProcessing: function(data,status,xhr) {
			if (!data.success) {
	        	alert('{{_("Failed: ")}}'+data.msg);
			}
		},
		grouping:false,
	    caption:"{{_("Vehicle Costs")}}"
	})
	.jqGrid('navGrid','#truck_cost_pager',
			{edit:false,add:false,del:false,search:false},
			{ 
			},
			{ // add params
			},
			{ // del params
			},
			{ // search params
			},
			{ // view params
			}
	)
	.jqGrid('hermify',{
		debug:true, printable:true, resizable:true
	});
}

$(function() {
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing vehicle costs for")}}',
		writeable:true,
		afterBuild:function(mysel,mydata) {
			buildPage( mydata.selid );
		},
		onChange:function(evt, selId) {
			updatePage( selId );
			return true;
		},
	});
});


$('#cost_base_year').blur( function(evt) {
	$.getJSON('{{rootPath}}json/set-currency-base-year',
		{modelId:$('#model_sel_widget').modelSelector('selId'),
		baseYear:$('#cost_base_year').val()
	})
	.done(function(data) {
		if (data.success) {
			// do nothing
		}
		else {
			alert('{{_("Failed: ")}}'+data.msg);
		}
	})
	.fail(function(jqxhr, textStatus, error) {
		alert('{{_("Error: ")}}'+jqxhr.responseText);
	});
})

$(function() {
	$("#truck_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });

} // end local scope
</script>
 
