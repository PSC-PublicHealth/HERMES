%rebase outer_wrapper **locals()

<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>
		</td>
	</tr>
	<tr><td>
		<div align='center' id='fridge_amort_div'>
		<label for="fridge_amort_years">{{_("Years to amortize these devices")}}</label>
		<input type="number" min="1" max="20" name="fridge_amort_years" id="fridge_amort_years">
		</div>
	</td></tr>
	<tr>
		<td width=100%>
			<table id="fridge_cost_grid"></table>
			<div id="fridge_cost_pager"> </div>
		</td>
	</tr>
</table>
	<table width=100%>
      <tr>
        <td></td>
        <td width=10%><input type="button" id="done_button" value={{_("Done")}}></td>
      </tr>
    </table>
</form>

<div id="fridge_info_dialog" title="This should get replaced"></div>

<script>
{ // local scope

function updateAllButGrid(modelId) {
	$.getJSON('{{rootPath}}json/get-cost-info-fridge',{modelId:modelId})
	.done(function(data) {
		if (data.success) {
			$("#fridge_amort_years").val(data.amortYears);
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
	$("#fridge_cost_grid").trigger("reloadGrid");
}

function fridgeInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>";
};

function currencyFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<div class=\"hermes_currency_selector\" id="+escape(cellvalue)+"></div>";
};

var priceCheckFailure = false;

function priceCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value)))
		return true;
	else {
		priceCheckFailure = true;
		return false;
	}
}

function buildPage(modelId) {
	updateAllButGrid(modelId);
	$('#fridge_amort_years').blur( function(evt) {
		$.getJSON('{{rootPath}}json/set-fridge-amort-years',
			{modelId:$('#model_sel_widget').modelSelector('selId'),
			amortYears:$('#fridge_amort_years').val()
		})
		.done(function(data) {
			if (data.success) {
				// do nothing
			}
    		else {
    			alert('{{_("Failed: ")}}'+data.msg);
    			if (data.amortYears)
    				$('#fridge_amort_years').val(data.amortYears);
    			}
		})
		.fail(function(jqxhr, textStatus, error) {
    		alert('{{_("Error: ")}}'+jqxhr.responseText);
		});
	})

	$("#fridge_cost_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-fridge-cost-table',
	    editurl:'{{rootPath}}edit/edit-cost-fridge',	
		datatype: "json",
		postData: {
			modelId: function() { return $('#model_sel_widget').modelSelector('selId'); }
		},
		rowNum:9999, // all on one page
		colNames:[
		          "{{_('TrueName')}}",
		          "{{_('Category')}}",
		          "{{_('Name')}}",
		          "{{_('Details')}}",
		          "{{_('Base Cost')}}",
		          "{{_('Currency')}}",
		          "{{_('Base Cost Year')}}",
		          "{{_('Ongoing')}}",
		          "{{_('Units')}}",
		          "{{_('Of')}}"
		], //define column names
		colModel:[
		          {name:'name', index:'name', hidden:true, key:true},
		          {name:'category', index:'category'},
		          {name:'displayname', index:'displayname', width:400},
		          {name:'info', index:'info', width:70, align:'center', sortable:false,
		        	  formatter:fridgeInfoButtonFormatter},
		          {name:'basecost', index:'basecost', width:100, align:'center', 
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
		          {name:'currency', index:'currency', width:70, align:'center', sortable:true,
		        	  editable:true,
		        	  edittype:'custom',
		        	  editoptions: {
		        		  custom_element:function(value, options){
		        			  return $.parseHTML("<div>"+value+"</div>");
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
		          {name:'basecostyear', index:'basecostyear', align:'center',
		        		  editable:true, edittype:'text', editrules:{integer:true, minValue:2000, maxValue:2020}},
		          {name:'ongoing', index:'ongoing', editable:true, edittype:'text', width:100, align:'center', 
			        	  formatter:'currency', formatoptions:{defaultValue:''},
			        	  editable:true, editrules:{ 
			        		  custom:true, 
			        		  custom_func: function(value,colname) {
			        			  if (priceCheck(value))
			        				  return [true,''];
			        			  else
			        				  return [false,'{{_("Please enter a valid price for Ongoing Cost")}}'];
			        		  }
			        	  }
		          },
		          {name:'ongoingunits', index:'ongoingunits', width:100, align:'center'},
		          {name:'ongoingwhat', index:'ongoingwhat', align:'center'}
		], //define column models
		pager: 'fridge_cost_pager', //set your pager div id
		pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
		pginput: false, //ditto
		sortname: 'name', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
		sortorder: "asc", //sort order; optional
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
		beforeSelectRow: function(rowId, evt) {
			var $this = $(this);
			var oldRowId = $this.getGridParam('selrow');
	        if (oldRowId && (oldRowId != rowId)) {
		        $this.jqGrid("saveRow", oldRowId, {
		        	extraparam: { 
						modelId: function() { return $('#model_sel_widget').modelSelector('selId'); }
		        	}
		        });
		        if (priceCheckFailure) {
		        	// The price check that was performed during saveRow may have prevented the 
		        	// row from closing.
		        	priceCheckFailure = false;
		        	return false; // prevent the new row from being edited
		        }
		        else {
		        	return true; // go ahead and edit the new row      		
		        }
			}
	        else return true;
		},
		onSelectRow: function(resultsid, status){
	   		if (status) {
	   			if (resultsid) {
					$(this).jqGrid('editRow',resultsid,{
						keys:true,
						extraparam: { 
							modelId: function() { return $('#model_sel_widget').modelSelector('selId'); }
						},
						oneditfunc: function(rowid) {
	 	 					$field = $('#'+rowid+'_currency');
	 	 					var sel = $field.text();
	 	 					$field.text('');
	 	 					if (sel=='') sel=null;
	 	 					var args = {
								widget:'currencySelector',
								modelId:function() { return $('#model_sel_widget').modelSelector('selId'); },
								label:''
	 	 					}
	 	 					if (sel) args['selected'] = sel;
							$field.hrmWidget(args);
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
	   			}
			}
			else {
				//alert('outside click '+resultsid);
			}
		},
		gridComplete: function(){
			$(".hermes_info_button").click(function(event) {
				$.getJSON('{{rootPath}}json/fridge-info',{name:unescape($(this).attr('id')), modelId:$('#model_sel_widget').modelSelector('selId')})
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
		loadError: function(xhr,status,error){
	    	alert('{{_("Error: ")}}'+status);
		},
		beforeProcessing: function(data,status,xhr) {
			if (!data.success) {
	        	alert('{{_("Failed: ")}}'+data.msg);
			}
		},
		grouping:true,
		groupingView:{
			groupField:['category'],
			groupDataSorted:true,
			groupText:['<b>{0} - {1} '+"{{_('Item(s)')}}"+'</b>'],
			groupColumnShow:[false]
		},
		/*
		rowattr: function(rowdata){
			if (!rowdata.usedin) return {"class":"not-editable-row"};
		},
		*/
	    caption:"{{_("Cold Storage Costs")}}"
	})
	.jqGrid('navGrid','#fridge_cost_pager',{edit:false,add:false,del:false})
	.jqGrid('hermify',{
		debug:true, printable:true, resizable:true
	});
}

$(function() {
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing storage costs for")}}',
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
	var btn = $("#done_button");
	btn.button();
	btn.click( function() {
		$.getJSON("{{rootPath}}json/generic-pop")
		.done(function(data) {
			if (data.success) {
				window.location = data.goto;
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
	})
})

$(function() {
	$("#fridge_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});


} // end local scope
</script>
 