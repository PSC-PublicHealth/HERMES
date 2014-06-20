%rebase outer_wrapper title_slogan=_("Create A Model"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<h1>{{_('Optionally Make Adjustments')}}</h1>
This table gives you a chance to adjust the values you've entered.  When you are satisfied with
the values, select 'Create The Model' to add your model to the list of available models.
<p>

<table id="model_create_adjust_grid"></table>
<div id="model_create_adjust_pager"> </div>

<form>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value={{("Next")}}></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_('The name of the model must not be blank.')}}</p>
</div>

<script>
$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/back"
	});
});

$(function() {
	$("#dialog-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				$( this ).dialog( "close" );
        	}
        }
	});

	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		var valsOK = true;
		if (valsOK) {
			window.location = "{{rootPath}}model-create/next?create=true";
		}
		else {
			$("#dialog-modal").dialog("open");
		}
	});
});

$(function() {

    var lastsel_models;
    $("#model_create_adjust_grid").jqGrid({ //set your grid id
   	    url:'{{rootPath}}json/adjust-models-table',
	    datatype: "json",
        treeGrid: true,
	    width: 600, //specify width; optional
	    colNames:['level','Location','idcode','Fetch','Scheduled','Shipments','per','Clients'], //define column names
	    colModel:[
	        {name:'levelname', index:'level', width:100},
	        {name:'name', index:'name', width:100, editable:true, edittype:'text'},
	        {name:'idcode', index:'idcode', width:50, key:true, sorttype:'int'},
	        {name:'fetch',index:'fetch',width:50,editable:true,edittype:'select',editoptions: {value:"fetch:true; deliver:false"}},
	        {name:'sched',index:'sched',width:50,editable:true,edittype:'select',editoptions: {value:"sched:true; demand:false"}},
	        {name:'howoften',index:'howoften',width:60, sorttype:'int',editable:true,editrules:{integer:true}},
	        {name:'ymw',index:'ymw',width:50,editable:true,edittype:'select',editoptions: {value:"year:year; month:month; week:week"}},
	        {name:'kids', index:'kids', width:50, sorttype:'int',editable:true,edittype:'text',editrules:{integer:true}},	        
	    ], //define column models
	    pager: '#model_create_adjust_pager', // but this is actually ignored for treeGrid=true
	    sortname: 'idcode', //the column according to which data is to be sorted; optional
	    viewrecords: false, // not good for treeGrid
	    sortorder: "asc", //sort order; optional
	    gridview: false, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
   	    onSelectRow: function(id){
		    if(id && id!==lastsel_models){
			    jQuery('#model_create_adjust_grid').jqGrid('saveRow',lastsel_models);
			    //jQuery('#model_create_adjust_grid').jqGrid('editRow',id,true);
			    jQuery('#model_create_adjust_grid').jqGrid('editRow',id,{
			    	"keys":true,
			    	"aftersavefunc": function(rowid,response) {
			    		$("#model_create_adjust_grid").trigger('reloadGrid');
					}});
			    lastsel_models=id;
		    }
	    },
        editurl:'{{rootPath}}edit/edit-create-model.json',
        height: 'auto',	
        caption:'{{_("Model Transport Network")}}',
        ExpandColumn : 'name'
    });
    $("#model_create_adjust_grid").jqGrid('navGrid','#model_create_adjust_pager',{edit:false,add:false,del:false});
});

</script>
 