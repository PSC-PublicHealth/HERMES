%rebase outer_wrapper **locals()

<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>
		</td>
	</tr>
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
			// As of right now, there is nothing to do
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

function floatCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value)))
		return true;
	else {
		return false;
	}
}

function nonNegCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value) && value>=0.0))
		return true;
	else {
		return false;
	}	
}

function priceCheck(value) { return nonNegCheck(value); }

function buildPage(modelId) {
	updateAllButGrid(modelId);
	$("#fridge_cost_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-fridge-cost-table',
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
		          "{{_('Years to Amortize')}}",
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
	        		  editable:true, edittype:'text', editrules:{integer:true, minValue:2000, maxValue:3000}},
			      {name:'amortyears', jsonmap:'amortyears', index:'amortyears', align:'center',
			        	  formatter:'number', formatoptions:{defaultValue:''},
			        	  editable:true, editrules:{ 
			        		  custom:true, 
			        		  custom_func: function(value,colname) {
			        			  if (nonNegCheck(value))
			        				  return [true,''];
			        			  else
			        				  return [false,'{{_("Please enter a valid value for Years to Amortize")}}'];
			        		  }
			        	  }},
		          {name:'ongoing', jsonmap: 'powerrate', index:'ongoing', editable:true, edittype:'text', width:100, align:'center', 
			        	  formatter:'number', formatoptions:{defaultValue:''},
			        	  editable:true, editrules:{ 
			        		  custom:true, 
			        		  custom_func: function(value,colname) {
			        			  if (nonNegCheck(value))
			        				  return [true,''];
			        			  else
			        				  return [false,'{{_("Please enter a valid value for Ongoing Cost")}}'];
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
					var id = unescape($(this).parent().attr("id"));
					var devName = $("#fridge_cost_grid").jqGrid('getCell',id,"displayname");
					var units = $("#fridge_cost_grid").jqGrid('getCell',id,"ongoingunits");
					var fuel = $("#fridge_cost_grid").jqGrid('getCell',id,"ongoingwhat");
					$("#fridge_cost_grid").jqGrid('editGridRow',id,{
						//closeAfterEdit:true,
						closeAfterEdit:false,
						closeOnEscape:true,
	                  	jqModal:true,
	                  	//viewPagerButtons:false,
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
	                  		console.log(data);
	                  		if (data.success) return [true];
	                  		else return [false,data.msg];
	                  	},
	            		beforeShowForm:function($form) {
	            			var $elt = $form.find('#tr_ongoing').find('td').first();
	            			$elt.html(units + ' ' + fuel);
	            		},	                  	
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
 