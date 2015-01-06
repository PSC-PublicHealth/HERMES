% title_slogan=_("Specify Vaccine Demand")
%rebase outer_wrapper **locals()

<script>
%if defined('createpipe'):
	var createOn = true;
%else:
	var createOn = false;
%end
</script>
<h2 style="display:none">{{_('Vaccine Demand By Population Type')}}</h2>
<table>
<tr>
	<td>
		<form id='left_grid_form'>
			<input type='radio' name='left_show' value='vaccines'>{{_('Vaccines')}}
			<input type='radio' name='left_show' value='people'>{{_('Population')}}
		</form>
	</td>
	<td>
		<div align=center id="model_sel_widget"></div>
	</td>
</tr>
<tr>
  <td>
	<table id="demand_vac_grid"></table>
  </td>

  <td>
    <table id="demand_edit_grid"></table>
  </td>
</tr>
</table>

<table>
	<tr>
		<td><input type="checkbox" id="set_scale_cb"></td>
		<td>
			<label>{{_("Show scaling factors to demand?")}}</label><br>
			<div id="set_scale_div" 	style="display:none">
				<table>
					<tr id="demand_scale_separate_option"><td>
						<input type='checkbox' id='set_scale_long_cb'><label>{{_("Scale vaccines separately?")}}</label>
					</td></tr>
					<tr id="demand_scale_separate_required" style="display:none"><td>
						<label>{{_("Vaccines are scaled separately")}}</label>
					</td></tr>
					<tr id="set_scale_single_block"><td>
						<label>{{_("Overall scaling factor:")}}</label>
						<input type='text' id='set_scale_text' onkeypress="validateFloatOrReturn(event)"><br>
						<label>{{_("Scale projected demand relative to actual demand:")}}</label>
						<input type='text' id='set_rel_scale_text'  onkeypress="validateFloatOrReturn(event)"><br>						
					</td></tr>
					<tr style="display:none" id="demand_scale_row"><td>
    					<table id="demand_scale_grid"></table>
  					</td></tr>
				</table>
			</div>
		</td>
	</tr>
	<tr id='cal_edit_row'>
		<td><input type="checkbox" id="set_cal_cb"></td>
		<td>
			<label>{{_("Show treatment calendar pattern?")}}</label><br>
			<div id="set_cal_div" style="display:none">
				<table>
					<tr id="demand_cal_separate_option"><td>
						<input type='checkbox' id='set_cal_long_cb'><label>{{_("Schedule population types separately?")}}</label>
					</td></tr>
					<tr id="demand_cal_separate_required" style="display:none"><td>
						<label>{{_("Populations are scheduled separately")}}</label>
					</td></tr>
					<tr id="set_cal_single_block"><td>
						<div id='box_cal_single_div'></div>
					</td></tr>
					<tr style="display:none" id="demand_cal_row"><td>
    					<table id="demand_cal_grid"></table>
  					</td></tr>
				</table>
			</div>
		</td>
	</tr>
	<tr id='cal_hide_row' style='display:none'>
		<td colspan='2'>
			{{_("This editor does not support the treatment schedule for this model.")}}
		</td>
	</tr>
</table>
<table id="nextback" width=100%>
	<tr>
		<td width=10%>
			<input type="button" id="back_button" value='{{_("Previous Screen")}}'>
		</td>
		<td width=70%>
		</td>
		<td width=10%>
			<input type="button" id="expert_button" value='{{_("Skip to Model Editor")}}'>
		</td>
		<td width=10%>
			<input type="button" id="next_button" value='{{_("Next Screen")}}'>
		</td>
	</tr>
</table>
<script>
{{!setupToolTips()}}

{ // put things in local scope

function validateFloatOrReturn(evt) {
	var theEvent = evt || window.event;
	var key = theEvent.keyCode || theEvent.which;
	if ( key == 13 ) {
		theEvent.target.blur();
    	theEvent.returnValue = false;
		//if(theEvent.preventDefault) theEvent.preventDefault();
	}
	else {
		key = String.fromCharCode( key );
		var regex = /[0-9]|\.|-/;
		if( !regex.test(key) ) {
    		theEvent.returnValue = false;
			//if(theEvent.preventDefault) theEvent.preventDefault();
		}
	}
}

function setTextFieldValue( $fld, val ) {
	$fld.attr('data-old',val);
	$fld.val(val);
}

function revertTextFieldValue( $fld ) {
	var old = $fld.attr('data-old');
	if ( old != undefined ) $fld.val(old);
}

function scalarScaleTextBlur(evt, url) {
	var theEvent = evt || window.event;
	var val = $(theEvent.target).val();
	if (isNaN(val)) {
		revertTextFieldValue( $(theEvent.target) );
		alert('{{_("Please enter a number.")}}');
	}
	else {
		$.getJSON(url,
			{
				modelId:function() { return $("#model_sel_widget").modelSelector('selId')},
				value:val
			})
		.done(function(data) {
			if (data.success) {
				setTextFieldValue($(theEvent.target),val);
				$("#demand_scale_grid").trigger("reloadGrid");
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
				revertTextFieldValue($(theEvent.target));
			}
		})
		.fail(function(jqxhr, textStatus, error) {
			alert('{{_("Error: ")}}'+jqxhr.responseText);
			revertTextFieldValue($(theEvent.target));
		});
	}
};

$(function() {
	$('#set_scale_cb').click(function () {
	    $("#set_scale_div").toggle(this.checked);
	});	
	$('#set_cal_cb').click(function () {
	    $("#set_cal_div").toggle(this.checked);
	});	
	$('#set_scale_long_cb').click(function() {
		$("#set_scale_single_block").toggle( ! this.checked );
		$("#demand_scale_row").toggle( this.checked );
	});
	$('#set_cal_long_cb').click(function() {
		if (this.checked) {
						$("#demand_cal_grid").trigger("reloadGrid");
		$("#set_cal_single_block").toggle( false );
		$("#demand_cal_row").toggle( true );
		}
		else {
			$("#set_cal_single_block").toggle( true );
			$("#demand_cal_row").toggle( false );
		}
	});
	$("#set_scale_text").blur(function(evt) {
		scalarScaleTextBlur(evt,'{{rootPath}}json/set-demand-scalar-scale');
	});
	$("#set_rel_scale_text").blur(function(evt) {
		scalarScaleTextBlur(evt,'{{rootPath}}json/set-demand-scalar-relscale');
	});
	
	if(createOn){
			var btn = $("#back_button");
			btn.button();
			btn.click( function() {
				window.location = "{{rootPath}}model-create/back"
			});
			
			var btn = $("#next_button");
			btn.button();
			btn.click( function() {
				window.location = "{{rootPath}}model-create/next";
			});
			
			var btn = $("#expert_button");
			btn.button();
			btn.click( function() {
				window.location = "{{rootPath}}model-create/next?expert=true";
			});
	}
	else{
		$("#nextback").remove();
	}
});


$(function() {
	if ($('input[name="left_show"]:checked').val() == undefined) {
		$('input[name="left_show"][value="vaccines"]').attr('checked',true);
	}
	$('#left_grid_form').change( function(event) {
		$("#demand_vac_grid").trigger("reloadGrid");
	});
});

$(function() {
	$('#box_cal_single_div').hrmWidget({
		widget:'boxCalendar',
		label:'{{_("Which days should clinics be open?")}}',
		afterBuild:function(mytable) {
			//alert('afterBuild happened');
		},
		onChange:function(mytable) {
			var outerThis = this;
			var peopleType = this.attr('data-people');
			var newState = this.boxCalendar('getState');
			$.getJSON('{{rootPath}}json/set-demand-scalar-cal',
				{
					modelId: function() { return $("#model_sel_widget").modelSelector('selId') },
					calendar: newState,
					people: peopleType
				})
				.done(function(data) {
					if (data.success) {
						outerThis.boxCalendar('saveState'); // so revert will work
						if (data.requireVectorCal) {
	    					$("#demand_cal_separate_option").toggle(false);
	    					$("#demand_cal_separate_required").toggle(true);
						}
						else {
	    					$("#demand_cal_separate_option").toggle(true);
	    					$("#demand_cal_separate_required").toggle(false);
						}
					}
					else {
						alert('{{_("Failed: ")}}'+data.msg);
						outerThis.boxCalendar( 'revertState');
					}
				})
				.fail(function(jqxhr, textStatus, error) {
					alert('{{_("Error: ")}}'+jqxhr.responseText);
					outerThis.boxCalendar( 'revertState' );
				});
		},
	});
});

$(function() {
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing demand for")}}',
		afterBuild:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
			var modelName = this.modelSelector('selName');
			buildSideTable(modelId, modelName);
			buildScaleTable(modelId, modelName);
			buildCalendarTable(modelId, modelName);
			buildPage(modelId, modelName);
		},
		onChange:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
			var modelName = this.modelSelector('selName');
			$("#demand_vac_grid").trigger("reloadGrid");
			$("#demand_scale_grid").trigger("reloadGrid");
			$("#demand_cal_grid").trigger("reloadGrid");
			$("#demand_edit_grid").jqGrid('GridUnload');
			buildPage(modelId, modelName);
		},
	});
});

function getShow() {
	var v = $('input[name="left_show"]:checked').val();
	if ( v == undefined) return 'vaccines';
	else return v;
}

function boxClick(cb,event) {
	event.stopPropagation();
	$.getJSON('{{rootPath}}json/manage-empty-demand',
		{name:cb.value, 
		modelId:function() { return $("#model_sel_widget").modelSelector('selId')},
		add:cb.checked,
		show:getShow
		})
	.done(function(data) {
		if (data.success) {
			var modelId = $('#model_sel_widget').modelSelector('selId');
			var modelName = $('#model_sel_widget').modelSelector('selName');
			$("#demand_edit_grid").jqGrid('GridUnload');
			buildPage(modelId, modelName);
			$("#demand_scale_grid").trigger("reloadGrid");
		}
		else {
			alert('{{_("Failed: ")}}'+data.msg);
	      	cb.checked = !cb.checked;				
		}
	})
	.fail(function(jqxhr, textStatus, error) {
		alert('{{_("Error: ")}}'+jqxhr.responseText);
      	cb.checked = !cb.checked;				
	});
}

function checkboxFormatter(cellvalue, options, rowObject)
{
	if (cellvalue) {
		return "<input type='checkbox'  checked value='"+rowObject[1]+"' onclick='boxClick(this,event)'>";
	}
	else {
		return "<input type='checkbox'  value='"+rowObject[1]+"' onclick='boxClick(this,event)'>";
	}
};

function buildSideTable(modelId, modelName) {

	$("#demand_vac_grid").jqGrid({ //set your grid id
	   	url:'{{rootPath}}json/manage-demand-vac-table',
		datatype: "json",
		postData: {
			modelId: function() { return $("#model_sel_widget").modelSelector('selId') },
			show: getShow
		},
		width: 300, //temporarily hardcoded
		colNames:[
		   "",
		   "{{_('Name')}}"
		], //define column names
		colModel:[
		          {name:'usedin', index:'usedin', align:'center', width:40, formatter:checkboxFormatter,
		           editable:true},
		          {name:'name', index:'name', width:150, key:true},
		], //define column models
		scroll: true,
		rowNum: 9999,
		sortname: 'name', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
	    caption:'{{_("Include in the dose table?")}}',
	}).jqGrid('hermify',{debug:true});
};

function buildPage(modelId, modelName) {
	$.getJSON('{{rootPath}}json/get-demand-table',{modelId:modelId})
	.done(function(data) {
		if (data.success) {
			if (data.supported) {
				$("#demand_edit_grid").jqGrid({ //set your grid id
   					url:'{{rootPath}}json/manage-demand-table',
    				editurl:'{{rootPath}}edit/edit-demand',	
					datatype: "json",
					postData: {
						modelId: modelId
					},
					//width: 740, //deprecated with resize_grid
					colNames:data.colNames,
					colModel:data.colModel,
					sortname:data.sortname,
					scroll: true,
					rowNum: 9999,
					viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
					gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
    				caption:'{{_("How many doses of each vaccine per person per year?")}}',
					onSelectRow: function(resultsid, status){
   						//if (status) {
   							if (resultsid) {
								var $this = $(this);
								$this.jqGrid('editRow',resultsid,{
									keys:true,
									extraparam: { 
										modelId: function() { return $("#model_sel_widget").modelSelector('selId') }
									},
									successfunc: function(response) {
										if (response.status >=200 && response.status<300) {
											data = $.parseJSON(response.responseText);
											if (data.success == undefined) return true;
											else {
												if (data.success) return true;
												else {
													if (data.msg != undefined) alert(data.msg);
													else alert('{{_("Sorry, transaction failed.")}}');
													return false;
												}
											}
										}
										else {
											alert('{{_("Sorry, transaction failed.")}}');
											return false;
										}
									},
								});
                  var ids = $("#demand_edit_grid").jqGrid('getDataIDs');
									for(var i=0; i<ids.length; i++) { 
                      $( document ).on( "blur", "input[id^='" + ids[i] + "_']", function() { 
                          var focusfrom = $(this).parent().parent().attr('id');
                          setTimeout(function()
                          {
                              if ($(document.activeElement).parent().parent().attr("id")!=focusfrom) {
                                  $('#demand_edit_grid').jqGrid('saveRow',focusfrom);
                              }
                          }, 1);
                      });
									}
   							}
						//}
						//else {
						//	alert('outside click '+resultsid);
						//}
					},
				}).jqGrid('hermify',{debug:true});
				resize_grid();
			}
			else {
				$("#demand_edit_grid").html('<h2>'+'{{_("The demand pattern associated with this model is not supported by the editor.")}}'+'</h2>');
			}

	    	if (data.hasScalarScale || data.hasVectorScale) {
	    		$("#set_scale_cb").attr('checked',true);
	    		$("#set_scale_div").toggle(true);
	    	}
	    	else {
	    		$("#set_scale_cb").attr('checked',false);
	    		$("#set_scale_div").toggle(false);
	    	}
	    	if (data.hasVectorScale) {
				$("#set_scale_single_block").toggle( false );
				$("#demand_scale_row").toggle( true );
	    		$("#set_scale_long_cb").attr('checked',true);
	    		if (data.requireVectorScale) {
	    			$("#demand_scale_separate_option").toggle(false);
	    			$("#demand_scale_separate_required").toggle(true);
	    		}
	    	}
	    	else {
				$("#set_scale_single_block").toggle( true );
				$("#demand_scale_row").toggle( false );
	    		$("#set_scale_long_cb").attr('checked',false);
	    	}
	    	setTextFieldValue( $("#set_scale_text"), data.scalarScaleSetting );
	    	setTextFieldValue( $("#set_rel_scale_text"), data.scalarRelScaleSetting );
	    	
	    	$("#cal_edit_row").toggle(data.calSupported);
	    	$("#cal_hide_row").toggle(!data.calSupported);
	    	if (data.hasScalarCal || data.hasVectorCal) {
	    		$("#set_cal_cb").attr('checked',true);
	    		$("#set_cal_div").toggle(true);
	    	}
	    	else {
	    		$("#set_cal_cb").attr('checked',false);
	    		$("#set_cal_div").toggle(false);
	    	}
	    	if (data.hasVectorCal) {
				$("#set_cal_single_block").toggle( false );
				$("#demand_cal_row").toggle( true );
	    		$("#set_cal_long_cb").attr('checked',true);
	    		if (data.requireVectorCal) {
	    			$("#demand_cal_separate_option").toggle(false);
	    			$("#demand_cal_separate_required").toggle(true);
	    		}
	    	}
	    	else {
				$("#set_cal_single_block").toggle( true );
				$("#demand_cal_row").toggle( false );
	    		$("#set_cal_long_cb").attr('checked',false);
	    	}
	    	$('#box_cal_single_div').boxCalendar('setState',data.scalarCalSetting);
		}
	    else {
	    	alert('{{_("Failed: ")}}'+data.msg);
	    }
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert('{{_("Error: ")}}'+jqxhr.responseText);
	});
};

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#demand_edit_grid"
  var idGrid2 = "#demand_vac_grid"
  var offset = $(idGrid).offset() //position of grid on page
  $(idGrid2).jqGrid('setGridHeight', $(window).height()-offset.top-130);
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-130);
}
$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
$(window).resize(resize_grid);  //bind resize_grid to window resize

function buildScaleTable(modelId, modelName) {
	$("#demand_scale_grid").jqGrid({ //set your grid id
   		url:'{{rootPath}}json/manage-demand-scale-table',
    	editurl:'{{rootPath}}edit/edit-demand-scale',	
		datatype: "json",
		postData: {
			modelId: function() { return $("#model_sel_widget").modelSelector('selId') },
		},
		colNames:[
		   "{{_('Vaccine')}}",
		   "{{_('Overall Scale')}}",
		   "{{_('Projected vs. Actual')}}",		   
		], //define column names
		colModel:[
			{name:'vaccine', index:'usedin', editable:false, key:true},
			{name:'scale', index:'scale', width:150, editable:true, edittype:'text', 
			editrules:{number:true,minValue:0.0,maxValue:2.0}},
			{name:'relscale', index:'relscale', width:150, editable:true, edittype:'text', 
			editrules:{number:true,minValue:0.00001,maxValue:2.0}}
		], //define column models
		scroll: true,
		rowNum: 100,
		sortname: 'vaccine', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
    	caption:'{{_("Increase the demand used to predict shipment sizes by what factor?")}}',
		onSelectRow: function(resultsid){
   			if (resultsid) {
				var $this = $(this);
				$this.jqGrid('editRow',resultsid,{
					keys:true,
					extraparam: { 
						modelId: function() { return $("#model_sel_widget").modelSelector('selId') }
					},
					successfunc: function(response) {
						if (response.status >=200 && response.status<300) {
							data = $.parseJSON(response.responseText);
							if (data.success == undefined) return true;
							else {
								if (data.success) {
									// This block happens after a successful post of an edit
	    							if (data.requireVectorScale) {
	    								$("#demand_scale_separate_option").toggle(false);
	    								$("#demand_scale_separate_required").toggle(true);
	    							}
	    							else {
	    								$("#demand_scale_separate_option").toggle(true);
	    								$("#demand_scale_separate_required").toggle(false);
	    								setTextFieldValue( $('#set_scale_text'), data.scaleVal );
	    								setTextFieldValue( $('#set_rel_scale_text'), data.relScaleVal );
	    							}
									return true;
								}
								else {
									if (data.msg != undefined) alert(data.msg);
									else alert('{{_("Sorry, transaction failed.")}}');
									return false;
								}
							}
						}
						else {
							alert('{{_("Sorry, transaction failed.")}}');
							return false;
						}
					},
				});
   			}
		},
	}).jqGrid('hermify',{debug:true});
}

function calendarFormatter(cellvalue, options, rowObject)
{
	return "<div class='hermes_cal_widget' data-state='"+cellvalue+"' data-people='"+rowObject[0]+"' id='demand_cal_grid_"+rowObject[0]+"'></div>";
};

function buildCalendarTable(modelId, modelName) {
	$("#demand_cal_grid").jqGrid({ //set your grid id
   		url:'{{rootPath}}json/manage-demand-calendar-table',
		datatype: "json",
		postData: {
			modelId: function() { return $("#model_sel_widget").modelSelector('selId') },
		},
		colNames:[
		   "{{_('Population Type')}}",
		   "{{_('Schedule Pattern')}}"
		], //define column names
		colModel:[
			{name:'people', index:'people', editable:false, key:true},
			{name:'calpattern', index:'calpattern', align:'center', formatter:calendarFormatter,
		           editable:false, sortable:false},
		], //define column models
		scroll: true,
		width: 600,
		rowNum: 100,
		sortname: 'people', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
    	caption:'{{_("What is the treatment schedule for each population type?")}}',
		gridComplete: function(){
			$('.hermes_cal_widget').hrmWidget({
				label:'',
				widget:"boxCalendar",
				innerLabels:false,
				afterBuild:function() { 
					this.boxCalendar('setState',$(this).attr('data-state')); 
				},
				onChange:function($tbl) { 
					var outerThis = this;
					var peopleType = this.attr('data-people');
					var newState = this.boxCalendar('getState');
					$.getJSON('{{rootPath}}edit/edit-demand-calendar',
						{
							modelId: function() { return $("#model_sel_widget").modelSelector('selId') },
							calendar: newState,
							people: peopleType
						})
						.done(function(data) {
							if (data.success) {
								outerThis.boxCalendar('saveState'); // so revert will work
								if (data.requireVectorCal) {
	    							$("#demand_cal_separate_option").toggle(false);
	    							$("#demand_cal_separate_required").toggle(true);
								}
								else {
	    							$("#demand_cal_separate_option").toggle(true);
	    							$("#demand_cal_separate_required").toggle(false);
	    							console.log('point 4');
	    							$('#box_cal_single_div').boxCalendar('setState',data.calVal);
	    							console.log('point 4b');
								}
							}
							else {
								alert('{{_("Failed: ")}}'+data.msg);
								outerThis.boxCalendar( 'revertState' );
							}
						})
						.fail(function(jqxhr, textStatus, error) {
							alert('{{_("Error: ")}}'+jqxhr.responseText);
							outerThis.boxCalendar( 'revertState' );
						});
				}
			});
		},
	}).jqGrid('hermify',{debug:true});
}

}

</script>
 