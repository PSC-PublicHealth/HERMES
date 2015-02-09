%rebase outer_wrapper title_slogan=_("Create A Model"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,pagehelptag=pagehelptag
<!---
###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################
-->
<script src="{{rootPath}}static/uisession.js"></script>
<script>
var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
console.log(modJson);
var modelInfo = ModelInfoFromJson(modJson);
console.log(modelInfo);
</script>

<p>
	<span class="hermes-top-main">
		{{_('Make Adjustments')}}
	</span>
</p>

<p>
	<span class="hermes-top-sub">
		{{_("Here you can make some minor adjustments to the supply chain.  Make adjustments to the model by clicking the cell to be modified and then hitting the enter key when finished.  You can expand or collapase levels by click the triangle next to the location name.")}}
	</span>
</p>


<table id="model_create_adjust_grid"></table>
<div id="model_create_adjust_pager"> </div>

<form>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value="{{_("Previous Screen")}}"></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value="{{_("Next Screen")}}"></td>
      </tr>
    </table>
</form>

<div id="model_confirm_delete" title='{{_("Delete Model")}}'></div>

<div id="model_create_existing_dialog" title='{{_("Model Creation Started")}}'>
	<p>{{_('This model has already been saved to the HERMES database, proceeding will overwrite the previous model.  Would you like to continue?')}}; 
</div>

<div id="back-modal" title = '{{_("Warning")}}'>
	<p>{{_('Going back and changing any items will result in resetting changes made in this page. Would you like to continue?')}}</p>
</div>

<div id="dialog-modal" title='{{_("Invalid Entry")}}'>
  <p>{{_('The name of the model must not be blank.')}}</p>
</div>

<script>
$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		$("#back-modal").dialog("open");
		//window.location = "{{rootPath}}model-create/back"
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
        },
        open: function(e,ui) {
    	    $(this)[0].onkeypress = function(e) {
    		if (e.keyCode == $.ui.keyCode.ENTER) {
    		    e.preventDefault();
    		    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
    		}
    	    };
        }
	});

	$("#back-modal").dialog({
		resizable: false,
		modal:true,
		autoOpen:false,
		buttons:{
			'{{_("Yes")}}':function(){
				$(this).dialog("close");
				window.location = "{{rootPath}}model-create/back";
			},
			'{{_("No")}}':function(){
				$(this).dialog("close");
			}
		},
		open: function(e,ui) {
		    $(this)[0].onkeypress = function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER) {
			    e.preventDefault();
			    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
		    };
		}
	});
	
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		var valsOK = true;
		if (valsOK) {
			if(modelInfo.modelId > -1){
				$("#model_create_existing_dialog").dialog("open");
			}
			else{
				window.location = "{{rootPath}}model-create/next?create=true";
			}
		}
		else {
			$("#dialog-modal").dialog("open");
		}
	});
	
	$("#model_create_existing_dialog").dialog({
		resizable: false,
		model: true,
		autoOpen:false,
		buttons:{
			'{{_("Continue")}}': function() {
				$(this).dialog("close");
				$.getJSON('{{rootPath}}edit/edit-models.json',
					{
					id: modelInfo.modelId, 
					oper:'del'
					}
				)
				.done(function(data) {
					if (data.success) {
						modelInfo.modelId = -1;
						window.location = "{{rootPath}}model-create/next?create=true";
				    }
				    else {
				    	alert('{{_("Failed: ")}}'+data.msg);
				    }
				})
	    	    .fail(function(jqxhr, textStatus, error) {
	    	    	alert('{{_("Error: ")}}'+jqxhr.responseText);
	    	    });
			},
			'{{_("Cancel")}}': function(){
				$(this).dialog("close");
			}
		},
	    open: function(e,ui) {
			$(this)[0].onkeypress = function(e) {
				if (e.keyCode == $.ui.keyCode.ENTER) {
					e.preventDefault();
					$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
					}
			    };
		}
	});
});


$(function() {

    var lastsel_models;
    $("#model_create_adjust_grid").jqGrid({ //set your grid id
   	    url:'{{rootPath}}json/adjust-models-table',
	    datatype: "json",
        treeGrid: true,
	    width: 1000, //specify width; optional
	    colNames:["{{_('Level')}}",
	              "{{_('Location Name')}}",
	              'idcode',
	              "{{_('Pick Up or Receive Shipments?')}}",
	              "{{_('Scheduled or Demand-Based Schedule of Shipments')}}",
	              "{{_('Amount of Shipment Fixed or Demand Based')}}",
	              "{{_('Freqency of Shipments')}}",
	              "{{_('per')}}",
	              "{{_('Number of Locations Supplied by this Location')}}"], //define column names
	    colModel:[
	        {name:'levelname', index:'level', width:100},
	        {name:'name', index:'name', width:100, editable:true, edittype:'text'},
	        {name:'idcode', index:'idcode', width:30, key:true, sorttype:'int'},
	        {name:'isfetch',index:'isfetch',width:50,editable:true,edittype:'select',editoptions: {value:"true:{{_('pick up')}}; false:{{_('recieve')}}"}},
	        {name:'issched',index:'issched',width:60,editable:true,edittype:'select',editoptions: {value:"true:{{_('scheduled')}}; false:{{_('demand-based')}}"}},
	        {name:'isfixedam',index:'isfixedam',width:50,editable:true,edittype:'select',editoptions: {value:"true:{{_('fixed')}}; false:{{_('variable')}}"}},
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
			    //jQuery('#model_create_adjust_grid').jqGrid('saveRow',lastsel_models);
			    //jQuery('#model_create_adjust_grid').jqGrid('editRow',id,true);
		    	
			    jQuery('#model_create_adjust_grid').jqGrid('editRow',id,{
			    	"keys":true,
			    	"aftersavefunc":function(rowid,response){
			    		$("#1 td").each(function(){
			        		console.log($(this).attr("aria-describedby"));
			        		$this=$(this)
			        		if($this.attr("aria-describedby")=="model_create_adjust_grid_isfetch")
			        			$this.html("");
			        		if($this.attr("aria-describedby")=="model_create_adjust_grid_issched")
			        			$this.html("");
			        		if($this.attr("aria-describedby")=="model_create_adjust_grid_isfixedam")
			        			$this.html("");
			        		if($this.attr("aria-describedby")=="model_create_adjust_grid_howoften")
			        			$this.html("");
			        		if($this.attr("aria-describedby")=="model_create_adjust_grid_ymw")
			        			$this.html("");
			            });
			    	}
			    	//"aftersavefunc": function(rowid,response) {
			    	//	$("#model_create_adjust_grid").trigger('reloadGrid');
					//}
			    });
			    if(id==1){
		    		$("#1_isfetch").hide();
		            $("#1_issched").hide();
		            $("#1_isfixedam").hide();
		            $("#1_howoften").val(0);
		            $("#1_howoften").hide();
		            $("#1_ymw").val("year");
		            $("#1_ymw").hide();
		    	}
			    //lastsel_models=id;
                var ids = $("#model_create_adjust_grid").jqGrid('getDataIDs');
                for(var i=0; i<ids.length; i++) {
                    $( document ).on( "blur", "input[id^='" + ids[i] + "_'], " + "select[id^='" + ids[i] + "_']", function() {
                      var focusfrom = $(this).closest("tr").attr('id')
                      setTimeout(function()
                      {
                          if ($(document.activeElement).closest("tr").attr('id')!=focusfrom) {
                              $('#model_create_adjust_grid').jqGrid('saveRow',focusfrom);
                          }
                      }, 1);
                    });
                }
		    }
	    },
        editurl:'{{rootPath}}edit/edit-create-model.json',
        height: 'auto',	
        caption:'{{_("Model Transport Network")}}',
        ExpandColumn : 'name',
        loadComplete: function(){
        	$("#1 td").each(function(){
        		console.log($(this).attr("aria-describedby"));
        		$this=$(this)
        		if($this.attr("aria-describedby")=="model_create_adjust_grid_isfetch")
        			$this.html("");
        		if($this.attr("aria-describedby")=="model_create_adjust_grid_issched")
        			$this.html("");
        		if($this.attr("aria-describedby")=="model_create_adjust_grid_isfixedam")
        			$this.html("");
        		if($this.attr("aria-describedby")=="model_create_adjust_grid_howoften")
        			$this.html("");
        		if($this.attr("aria-describedby")=="model_create_adjust_grid_ymw")
        			$this.html("");
        		$("#model_create_adjust_grid").jqGrid('expandNode',$("#model_create_adjust_grid").jqGrid('getRootNodes'));
        		
        	});
        },
    }).jqGrid('hermify',{debug:true, resizable_hz:true});
    setTimeout("jQuery('.treeclick').click();",100);
    $("#model_create_adjust_grid").jqGrid('navGrid','#model_create_adjust_pager',{edit:false,add:false,del:false});
});

function deleteModel(modelId, modelName) {
    var msg = '{{_("Really delete the model ")}}' + modelName + " ( " + modelId + " ) ?";
    $("#model_confirm_delete").html(msg);
    $("#model_confirm_delete").data('modelId', modelId);
    $("#model_confirm_delete").dialog("open");
}
</script>
 