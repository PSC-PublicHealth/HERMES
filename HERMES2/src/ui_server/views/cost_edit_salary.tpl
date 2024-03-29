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
			<table id="staff_cost_grid"></table>
			<div id="staff_cost_pager"> </div>
		</td>
	</tr>
</table>

<div id="staff_info_dialog" title="This should get replaced"></div>

<script>
{ // local scope

function updateAllButGrid(modelId) {
	$.getJSON('{{rootPath}}json/get-cost-info-salary',{modelId:modelId})
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
	$("#staff_cost_grid").trigger("reloadGrid");
}

function staffInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<div class=\"hermes_button_triple\" id=\""+escape(cellvalue)+"\"></div>";
};

function fracCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value))
			&& parseFloat(value)>=0.0 && parseFloat(value)<=1.0)
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
	else {
		// prev
		idx -= 1;
		if (idx<0) idx = ids.length - 1;
	}
	var newDisplayName = $g.jqGrid('getCell', ids[idx], 'displayname');
	$mySpan.html(prefix + newDisplayName);
}

function buildPage(modelId) {
	updateAllButGrid(modelId);

	$("#staff_cost_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-staff-cost-table',
	    editurl:'{{rootPath}}edit/edit-cost-staff',
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
		          "{{_('Base Salary')}}",
		          "{{_('Currency')}}",
		          "{{_('Base Salary Year')}}",
		          "{{_('Fraction EPI')}}",
		          "{{_('Details')}}"		          
		], //define column names
		colModel:[
		          {name:'name', jsonmap:'name', index:'name', hidden:true, key:true},
		          {name:'displayname', jsonmap:'displayname', index:'displayname', width:400},
		          {name:'basesalary', jsonmap:'basesalary', index:'basesalary', jsonmapwidth:100, align:'center', 
		        		  formatter:'currency', formatoptions:{defaultValue:''},
		        		  editable:true, editrules:{ 
			        		  custom:true, 
			        		  custom_func: function(value,colname) {
			        			  if (priceCheck(value))
			        				  return [true,''];
			        			  else
			        				  return [false,'{{_("Please enter a valid price for Base Salary")}}'];
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
		  					  if (sel=='') sel='EUR';
		  					  var args = {
		  							  widget:'currencySelector',
		  							  modelId:function() { return $('#model_sel_widget').modelSelector('selId'); },
		  							  label:'',
		  							  recreate:true
		  					  }
		  					  if (sel) args['selected'] = sel;
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
		          {name:'basesalaryyear', jsonmap:'basesalaryyear', index:'basesalaryyear', align:'center',
		        	  editable:true, edittype:'text', editrules:{integer:true, minValue:2000, maxValue:3000}
		          },
		          {name:'fractionepi', jsonmap:'fractionepi', index:'fractionepi', align:'center',
		        	  editable:true, edittype:'text', 
		        	  editrules:{
		        		  custom:true,
		        		  custom_func: function(value,colname) {
		        			  if (fracCheck(value))
		        				  return [true,''];
		        			  else
		        				  return [false,'{{_("Please enter a value between 0.0 and 1.0 to give the fraction of this staff member\'s time spent on EPI work")}}'];		        			  
		        		  }
		        	  }
		          },
		          {name:'info', jsonmap: 'detail', index:'info', width:140, align:'center', sortable:false, 
		        	  formatter:staffInfoButtonFormatter}
		          
		], //define column models
		pager: 'staff_cost_pager', //set your pager div id
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
					$.getJSON('{{rootPath}}json/staff-info',{name:id, modelId:$('#model_sel_widget').modelSelector('selId')})
					.done(function(data) {
						if (data.success) {									
							$("#staff_info_dialog").html(data['htmlstring']);
							$("#staff_info_dialog").dialog('option','title',data['title']);
							$("#staff_info_dialog").dialog("open");
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
					var devName = $("#staff_cost_grid").jqGrid('getCell',id,"displayname");
					$("#staff_cost_grid").jqGrid('editGridRow',id,{
						closeAfterEdit:false,
						bSubmit: "{{_('Save')}}",
						bCancel: "{{_('Done')}}",
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
	                  	editCaption:'{{_("Edit Salary Information for ")}}' + devName,
	                  	savekey:[true,13],
	                  	afterSubmit:function(response,postData){
	                  		var data = $.parseJSON(response.responseText);
	                  		console.log(data);
	                  		if (data.success) return [true];
	                  		else return [false,data.msg];
	                  	},
	            		onclickPgButtons:function( btnStr, $form, rowid) {
	            			updateEditDlgTitle(btnStr, $form, rowid, 'staff_cost_grid', '{{_("Edit Salary Information for ")}}');
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
//		groupingView:{
//			groupField:['category'],
//			groupDataSorted:true,
//			groupText:['<b>{0} - {1} '+"{{_('Item(s)')}}"+'</b>'],
//			groupColumnShow:[false]
//		},
	    caption:"{{_("Staff Costs")}}"
	})
	.jqGrid('navGrid','#staff_cost_pager',
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
		label:'{{_("Showing salary costs for")}}',
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
	$("#staff_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });

} // end local scope
</script>
 
