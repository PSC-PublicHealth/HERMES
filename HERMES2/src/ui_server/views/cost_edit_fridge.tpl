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

function updatePage(modelId) {
	console.log('updatePage');
	$("#fridge_cost_grid").trigger("reloadGrid");
	console.log('updatePage complete');
}

function fridgeInfoButtonFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>";
};

function currencyFormatter(cellvalue, options, rowObject)
{
    // cellvalue will be the name string
	return "<div class=\"hermes_currency_selector\" id="+escape(cellvalue)+">";
};

function buildPage(modelId) {
	console.log('buildPage');
	$("#fridge_cost_grid").jqGrid({
	   	url:'{{rootPath}}json/manage-fridge-cost-table',
	    //editurl:'{{rootPath}}edit/edit-fridge.json',	
		datatype: "json",
		postData: {
			modelId: function() { return $('#model_sel_widget').modelSelector('selId'); }
		},
		rowNum:9999, // temporary until storage types are grouped in a nested grid
		colNames:[
		          "{{_('Name')}}",
		          "{{_('Foo')}}",
		          "{{_('Bar')}}",
		          "{{_('Currency')}}",
		          "{{_('Details')}}"
		], //define column names
		colModel:[
		          {name:'name', index:'name', width:400, key:true},
		          {name:'foo', index:'foo', align:'center'},
		          {name:'bar', index:'bar', width:200, editable:true, edittype:'text'},
		          {name:'currency', index:'currency', width:300, align:'center', sortable:false,
		        	  formatter:currencyFormatter},
		          {name:'info', index:'info', width:110, align:'center', sortable:false,
		        	  formatter:fridgeInfoButtonFormatter}
		], //define column models
		pager: 'fridge_cost_pager', //set your pager div id
		pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
		pginput: false, //ditto
		sortname: 'name', //the column according to which data is to be sorted; optional
		viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
		sortorder: "asc", //sort order; optional
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
	   	onSelectRow: function(id){
			/*
			if(id && id!==lastsel_fridge){
				jQuery('#manage_fridge_grid').jqGrid('saveRow',lastsel_fridge);
				jQuery('#manage_fridge_grid').jqGrid('editRow',id,{
					keys:true,
					extraparam: { modelId: function() { return $('#model_select').modelSelector('selId'); }}
				});
				lastsel_fridge=id;
			}
		 */
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
			$(".hermes_currency_selector").hrmWidget({
				widget:'currencySelector',
				modelId:function() { return $('#model_sel_widget').modelSelector('selId'); },
				label:'',
				//onChange:alert($(this).attr('id'))
			})
		},
		/*
		rowattr: function(rowdata){
			if (!rowdata.usedin) return {"class":"not-editable-row"};
		},
		*/
	    caption:"{{_("Cold Storage Costs")}}"
	})
	.jqGrid('navGrid','#fridge_cost_pager',{edit:false,add:false,del:false})
	.jqGrid('hermify',{debug:true, printable:true});
	console.log('buildPage complete');
}

$(function() {
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing storage costs for")}}',
		afterBuild:function(mysel,mydata) {
			console.log('afterBuild');
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


} // end local scope
</script>
 