%rebase outer_wrapper **locals()

<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>
		</td>
	</tr>
	<tr>
	<td width=100%>
		<table id="perdiem_cost_grid"></table>
		<div id="perdiem_cost_pager"> </div>
	</td>
	</tr>
	<tr>
	<td width=100%>
		<table id="route_perdiem_grid"></table>
		<div id="route_perdiem_pager"> </div>
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

<div id="perdiem_info_dialog" title="This should get replaced"></div>

<div id="route_info_dialog" title="This should get replaced"></div>

<script>
{ // local scope

function updateAllButGrid(modelId) {
	$.getJSON('{{rootPath}}json/get-cost-info-perdiem',{modelId:modelId})
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
	$("#perdiem_cost_grid").trigger("reloadGrid");
}

function perdiemInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<div class=\"hermes_button_triple\" id=\""+escape(cellvalue)+"\"></div>";
};

function routeInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the routename string
	return "<div class=\"hermes_button_triple2\" id=\""+escape(cellvalue)+"\"></div>";
};

function fracCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value))
			&& parseFloat(value)>=0.0 && parseFloat(value)<=1.0)
		return true;
	else return false;
}

function distanceCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value))
			&& parseFloat(value)>=0.0)
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
	if (! newDisplayName ) {
		// This is the route grid
		newDisplayName = $g.jqGrid('getCell', ids[idx], 'routename');
	}
	$mySpan.html(prefix + newDisplayName);
}

function buildPage(modelId) {
	updateAllButGrid(modelId);

	$("#perdiem_cost_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-perdiem-cost-table',
	    editurl:'{{rootPath}}edit/edit-cost-perdiem',
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
		          "{{_('Base Amount')}}",
		          "{{_('Currency')}}",
		          "{{_('Base Amount Year')}}",
		          "{{_('Must Be Overnight?')}}",
		          "{{_('Count First Day?')}}",
		          "{{_('Min Km Home')}}",
		          "{{_('Details')}}"		          
		], //define column names
		colModel:[
		          {name:'name', jsonmap:'name', index:'name', hidden:true, key:true},
		          {name:'displayname', jsonmap:'displayname', index:'displayname', width:400},
		          {name:'baseamount', jsonmap:'baseamount', index:'baseamount', jsonmapwidth:100, align:'center', 
		        		  formatter:'currency', formatoptions:{defaultValue:''},
		        		  editable:true, editrules:{ 
			        		  custom:true, 
			        		  custom_func: function(value,colname) {
			        			  if (priceCheck(value))
			        				  return [true,''];
			        			  else
			        				  return [false,'{{_("Please enter a valid price for Base Amount")}}'];
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
		          {name:'baseamountyear', jsonmap:'baseamountyear', index:'baseamountyear', align:'center',
		        	  editable:true, edittype:'text', editrules:{integer:true, minValue:2000, maxValue:3000}
		          },
		          {name:'mustbeovernight', jsonmap:'mustbeovernight', index:'mustbeovernight', align:'center',
		        	  editable:true, edittype:'checkbox'
		          },
		          {name:'countfirstday', jsonmap:'countfirstday', index:'countfirstday', align:'center',
		        	  editable:true, edittype:'checkbox'
		          },
		          {name:'minkmhome', jsonmap:'minkmhome', index:'minkmhome', align:'center',
		        	  editable:true, edittype:'text', 
		        	  editrules:{
		        		  custom:true,
		        		  custom_func: function(value,colname) {
		        			  if (distanceCheck(value))
		        				  return [true,''];
		        			  else
		        				  return [false,'{{_("Please enter a value greater than or equal to 0.0 to give the minimum distance at which per diems are paid.")}}'];		        			  
		        		  }
		        	  }
		          },
		          {name:'info', jsonmap: 'detail', index:'info', width:140, align:'center', sortable:false, 
		        	  formatter:perdiemInfoButtonFormatter}
		          
		], //define column models
		pager: 'perdiem_cost_pager', //set your pager div id
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
					$.getJSON('{{rootPath}}json/perdiem-info',{name:id, modelId:$('#model_sel_widget').modelSelector('selId')})
					.done(function(data) {
						if (data.success) {									
							$("#perdiem_info_dialog").html(data['htmlstring']);
							$("#perdiem_info_dialog").dialog('option','title',data['title']);
							$("#perdiem_info_dialog").dialog("open");
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
					var devName = $("#perdiem_cost_grid").jqGrid('getCell',id,"displayname");
					$("#perdiem_cost_grid").jqGrid('editGridRow',id,{
						closeAfterEdit:true,
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
	                  	editCaption:'{{_("Edit Per Diem Information for ")}}' + devName,
	                  	savekey:[true,13],
	                  	afterSubmit:function(response,postData){
	                  		var data = $.parseJSON(response.responseText);
	                  		console.log(data);
	                  		if (data.success) return [true];
	                  		else return [false,data.msg];
	                  	},
	            		onclickPgButtons:function( btnStr, $form, rowid) {
	            			updateEditDlgTitle(btnStr, $form, rowid, 'perdiem_cost_grid', '{{_("Edit Per Diem Information for ")}}');
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
	    caption:"{{_("Per Diem Rates")}}"
	})
	.jqGrid('navGrid','#perdiem_cost_pager',
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
		debug:true, printable:true, resizable_hz:true
	});

	$("#route_perdiem_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-route-perdiem-table',
	    editurl:'{{rootPath}}edit/edit-cost-route-perdiem',
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
		          "{{_('Route Name')}}",
		          "{{_('Top Level')}}",
		          "{{_('Supplier')}}",
		          "{{_('Per Diem Type')}}",
		          "{{_('Details')}}"		          
		], //define column names
		colModel:[
		          {name:'routename', jsonmap:'routename', index:'routename', key:true},
		          {name:'level', jsonmap:'level', index:'level'},
		          {name:'supplier', jsonmap:'supplier', index:'supplier'},
		          {name:'pdtype', jsonmap:'pdtype', index:'pdtype',
		        	  editable:true,
		        	  edittype:'custom',
		        	  editoptions: {
		        		  custom_element:function(value, options){
		  					  var $divElem = $($.parseHTML("<div class='hermes_type_selector'>"+value+"</div>"));
		  					  var sel = $divElem.text();
		  					  var args = {
		  							  widget:'typeSelector',
		  							  modelId:function() { return $('#model_sel_widget').modelSelector('selId'); },
		  							  invtype:'perdiems',
		  							  selected:value,
		  							  label:'',
		  							  recreate:true
		  					  }
		  					  if (sel) args['selected'] = sel;
		  					  $divElem.hrmWidget(args);
		        			  return $divElem;
		        		  },
		        		  custom_value:function(elem, op, value){
		        			  if (op=='get') {
		        				  return $(elem).typeSelector('selValue');
		        			  }
		        			  else if (op=='set') {
		        				  $(elem).typeSelector('selValue',value);
		        			  }
		        		  }
		        	  }
		          },
		          {name:'info', jsonmap: 'detail', index:'info', width:140, align:'center', sortable:false, 
		        	  formatter:routeInfoButtonFormatter}
		], //define column models
		pager: 'route_perdiem_pager', //set your pager div id
		pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
		pginput: false, //ditto
		sortname: 'routename', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
		sortorder: "asc", //sort order; optional
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
		beforeSelectRow: function(rowid, e) {
		    return false;
		},
		gridComplete: function(){
			$('.hermes_button_triple2').hrmWidget({
				widget:'buttontriple',
				onInfo:function(event) {
					var id = unescape($(this).parent().attr("id"));
					$.getJSON('{{rootPath}}json/route-info',
							{routeName:id, modelId:$('#model_sel_widget').modelSelector('selId')})
					.done(function(data) {
						if (data.success) {									
							$("#route_info_dialog").html(data['htmlstring']);
							$("#route_info_dialog").dialog('option','title',data['title']);
							$("#route_info_dialog").dialog("open");
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
					var routeName = $("#route_perdiem_grid").jqGrid('getCell',id,"routename");
					$("#route_perdiem_grid").jqGrid('editGridRow',id,{
						closeAfterEdit:true,
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
	                  	editCaption:'{{_("Edit Per Diem Information for Route ")}}' + routeName,
	                  	savekey:[true,13],
	                  	afterSubmit:function(response,postData){
	                  		var data = $.parseJSON(response.responseText);
	                  		console.log(data);
	                  		if (data.success) return [true];
	                  		else return [false,data.msg];
	                  	},
	            		onclickPgButtons:function( btnStr, $form, rowid) {
	            			updateEditDlgTitle(btnStr, $form, rowid, 'route_perdiem_grid', '{{_("Edit Per Diem Information for Route ")}}');
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
		grouping: true,
		groupingView:{
			groupField:['level'],
			groupDataSorted:true,
			groupText:['<b>{0} - {1} '+"{{_('Item(s)')}}"+'</b>'],
			groupColumnShow:[false],
			groupCollapse: true
		},
	    caption:"{{_("Route Per Diem Rules")}}"
	})
	.jqGrid('navGrid','#route_perdiem_pager',
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
		label:'{{_("Showing per diem costs for")}}',
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
	$("#perdiem_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function() {
	$("#route_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});


} // end local scope
</script>
 