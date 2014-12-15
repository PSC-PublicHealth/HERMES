%rebase outer_wrapper **locals()

<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>
		</td>
	</tr>
	<tr>
	<td width=100%>
		<table id="store_cost_grid"></table>
		<div id="store_cost_pager"> </div>
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

<div id="store_info_dialog" title="This should get replaced"></div>

<script>
{ // local scope

function updateAllButGrid(modelId) {
	$.getJSON('{{rootPath}}json/get-cost-info-buildings',{modelId:modelId})
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
	$("#store_cost_grid").trigger("reloadGrid");
}

function storeInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the routename string
	return "<div class=\"hermes_button_triple\" id=\""+escape(cellvalue)+"\"></div>";
};

function priceCheck(value) {
	if ((value=='') || (!isNaN(parseFloat(value)) && isFinite(value)))
		return true;
	else {
		return false;
	}
}

function buildPage(modelId) {
	updateAllButGrid(modelId);

	$("#store_cost_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-cost-buildings-table',
	    editurl:'{{rootPath}}edit/edit-cost-buildings',
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
		          "{{_('ID')}}",
		          "{{_('Store Name')}}",
		          "{{_('Level')}}",
		          "{{_('Cost Per Year')}}",
		          "{{_('Cost Currency')}}",
		          "{{_('Cost Base Year')}}",
		          "{{_('Details')}}"		          
		], //define column names
		colModel:[
		          {name:'id', jsonmap:'id', index:'id', key:true},
		          {name:'name', jsonmap:'name', index:'name', key:true},
		          {name:'level', jsonmap:'level', index:'level'},
		          {name:'cost', jsonmap:'cost', index:'cost', jsonmapwidth:100, align:'center',
	        		  formatter:'currency', formatoptions:{defaultValue:''},
	        		  editable:true, editrules:{ 
		        		  custom:true, 
		        		  custom_func: function(value,colname) {
		        			  if (priceCheck(value))
		        				  return [true,''];
		        			  else
		        				  return [false,'{{_("Please enter a valid cost for Cost Per Year")}}'];
		        		  }
		        	  }
		          },
		          {name:'costcur', jsonmap:'costcur', index:'costcur', width:70, align:'center', sortable:false,
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
		          {name:'costyear', jsonmap:'costyear', index:'costyear', align:'center',
		        	  editable:true, edittype:'text', editrules:{integer:true, minValue:2000, maxValue:3000}
		          },
		          {name:'info', jsonmap: 'detail', index:'info', width:140, align:'center', sortable:false, 
		        	  formatter:storeInfoButtonFormatter}
		          ], //define column models
		pager: 'store_cost_pager', //set your pager div id
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
					$.getJSON('{{rootPath}}json/store-info',
							{storeId:id, modelId:$('#model_sel_widget').modelSelector('selId')})
					.done(function(data) {
						if (data.success) {									
							$("#store_info_dialog").html(data['htmlstring']);
							$("#store_info_dialog").dialog('option','title',data['title']);
							$("#store_info_dialog").dialog("open");
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
					var storeName = $("#store_cost_grid").jqGrid('getCell',id,"name");
					$("#store_cost_grid").jqGrid('editGridRow',id,{
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
	                  	editCaption:'{{_("Edit Site Cost Information for Store ")}}' + storeName + ' (' + id + ')',
	                  	savekey:[true,13],
	                  	afterSubmit:function(response,postData){
	                  		var data = $.parseJSON(response.responseText);
	                  		console.log(data);
	                  		if (data.success) return [true];
	                  		else return [false,data.msg];
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
	.jqGrid('navGrid','#store_cost_pager',
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
		label:'{{_("Showing building costs for")}}',
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
	$("#store_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});


} // end local scope
</script>
 