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
	return "<div class=\"hermes_button_triple\" id=\""+escape(cellvalue)+"\"></div>";
	/*
	return "<button type=\"button\" class=\"this_edit_button\" id="+escape(cellvalue)+">Edit</button>" +
			"<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>" +
			"<button type=\"button\" class=\"this_info_button\" id="+escape(cellvalue)+" disabled>Del</button>";
	*/
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
	   	url:'{{rootPath}}json/manage-fridge-cost-table-2',
	    editurl:'{{rootPath}}edit/edit-cost-fridge',
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
		          "{{_('Category')}}",
		          "{{_('Name')}}",
		          "{{_('Base Cost')}}",
		          "{{_('Currency')}}",
		          "{{_('Base Cost Year')}}",
		          "{{_('Ongoing')}}",
		          "{{_('Units')}}",
		          "{{_('Of')}}",
		          "{{_('Details')}}"
		          
		], //define column names
		colModel:[
		          {name:'name', jsonmap:'name', index:'name', hidden:true, key:true},
		          {name:'category', jsonmap:'category', index:'category'},
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
		          {name:'basecostyear', jsonmap:'basecostyear', index:'basecostyear', align:'center',
		        		  editable:true, edittype:'text', editrules:{integer:true, minValue:2000, maxValue:2020}},
		          {name:'ongoing', jsonmap: 'powerrate', index:'ongoing', editable:true, edittype:'text', width:100, align:'center', 
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
		          {name:'ongoingunits', jsonmap: 'powerrateunits', index:'ongoingunits', width:100, align:'center'},
		          {name:'ongoingwhat', jsonmap: 'energy', index:'ongoingwhat', align:'center'},
		          {name:'info', jsonmap: 'detail', index:'info', width:140, align:'center', sortable:false, 
		        	  formatter:fridgeInfoButtonFormatter}
		          
		], //define column models
		pager: 'fridge_cost_pager', //set your pager div id
		pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
		pginput: false, //ditto
		sortname: 'name', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
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
					$.getJSON('{{rootPath}}json/fridge-info',{name:id, modelId:$('#model_sel_widget').modelSelector('selId')})
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
				},
				onEdit:function(event){
					//var gr = $("#fridge_cost_grid").jqGrid('getGridParam','selRow');
					//console.log(gr);
					if(true) {
						var id = unescape($(this).parent().attr("id"));
						console.log("ID :"+id);
						var devName = $("#fridge_cost_grid").jqGrid('getCell',id,"displayname");
						$("#fridge_cost_grid").jqGrid('editGridRow',id,{
	                  	  closeAfterEdit:true,
	                  	  closeOnEscape:true,
	                  	  jqModal:true,
	                  	  viewPagerButtons:false,
	                  	  mType:"POST",
	                  	  modal:true,
	                  	  editData: {
	        					modelId: function() { 
	        						return $('#model_sel_widget').modelSelector('selId'); 
	        					}
	                  	  },
	                  	  editCaption:"Edit Cost Information for " + devName,
	                  	  savekey:[true,13]             
						});
					}
					else alert("Please Slect Row");
				}
			});
			/*
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
			*/
			/*
			$(".this_edit_button").click(function(event){
				//var gr = $("#fridge_cost_grid").jqGrid('getGridParam','selRow');
				//console.log(gr);
				if(true) {
					console.log("ID :"+ $(this).attr("id"));
					var devName = $("#fridge_cost_grid").jqGrid('getCell',$(this).attr("id"),"displayname");
					$("#fridge_cost_grid").jqGrid('editGridRow',$(this).attr("id"),{
                  	  closeAfterEdit:true,
                  	  closeOnEscape:true,
                  	  jqModal:true,
                  	  viewPagerButtons:false,
                  	  mType:"POST",
                  	  modal:true,
                  	  editData: {
        					modelId: function() { 
        						return $('#model_sel_widget').modelSelector('selId'); 
        					}
                  	  },
                  	  editCaption:"Edit Cost Information for " + devName,
                  	  savekey:[true,13]             
					});
				}
				else alert("Please Slect Row");
			});
			*/
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
	    caption:"{{_("Cold Storage Costs")}}"
	})
	.jqGrid('navGrid','#fridge_cost_pager',
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

$(function(){
	
})
} // end local scope
</script>
 