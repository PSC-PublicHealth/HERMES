%rebase outer_wrapper title_slogan=_('Available Models'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<style>
.ui-jqgrid tr.jqgrow td { 
	white-space:nowrap !important; 
	overflow:hidden; 
	text-overflow: ellipsis; 
}
</style>
<h3 style="display:none">{{_('Select A Model')}}</h3>
<h4>{{_("Please select a model to open.  You can use the buttons on the right to perform various actions with the selected model.  If you would like to edit the notes or the name of a model, please double click on the line.")}}</h4>
<table id="manage_models_grid" class="models_list_table"></table>
<div id="manage_models_pager"> </div>
</td>
</tr>
</table>

<div id="model_copy_dialog_form" title={{_("Copy A Model")}}>
  <form>
  <fieldset>
  	<table>
	  	<tr>
  			<td>{{_('Model To Copy')}}</td>
  			<td id='model_copy_dlg_from_name'>replace me</td>
  		</tr>
  		<tr>
    		<td><label for="model_copy_dlg_new_name">{{_('Name Of The Copy')}}</label></td>
    		<td><input type="text" name="model_copy_dlg_new_name" id="model_copy_dlg_new_name" class="text ui-widget-content ui-corner-all" /></td>
    	</tr>
    </table>
  </fieldset>
  </form>
</div>

<div id="model_info_dialog" title="This should get replaced">
</div>

<div id="model_confirm_delete" title='{{_("Delete Model")}}'>
</div>

<div id="model_edit_note_dialog" title="{{_('Model Notes')}}">
<table>
	<tr>
		<td>
			{{_('Model Name')}}
		</td>
		<td>
			<input type="text" id="model_dialog_name_edit"></input>
		</td>
	<tr>
		<td style="vertical-align:top;">
			{{_('Model Notes')}}
		</td>
		<td>
			<textarea rows="30" cols="120" id="model_dialog_note_edit"></textarea>
		</td>
	</tr>
</table>
</div>

<script>
{{!setupToolTips()}}

function modelsInfoButtonFormatter(cellvalue, options, rowObject) {
	// cellvalue will be an integer
	//return "<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>";
	return "<div class='hermes_button_triple' id='" + escape(cellvalue)+ "'/>";
}

function modelsNoteFormatter(cellvalue, options, rowObject){
	if(cellvalue == null) return null;
	if(cellvalue.length==0) return cellvalue;
	
	var splitVal = cellvalue.split(" ");
	var newString = "";
	for(var i =0; i<splitVal.length;i++){
		newString += splitVal[i] + " ";
		if(newString.length > 120){
			newString += "...";
			break;
		}
	}
	return newString;
}

function getModelInfo(modelId){
	return $.ajax({
		url:'{{rootPath}}json/model-info?modelId='+modelId,
		dataType:'json'
	}).promise();
};

var lastsel_models = null;
var lastsel_name = null;
$("#manage_models_grid").jqGrid({ //set your grid id
    url:'json/manage-models-table',
    datatype: "json",
    rowNum:9999, // rowNum=-1 has bugs, suggested solution is absurdly large setting to show all on one page
    colNames:[
	"{{_('Name')}}",
	"{{_('Model ID')}}",
	"{{_('Note')}}",
	"{{_('Download')}}",
	"{{_('Actions')}}"
    ], //define column names
    colModel:[
//	{name:'name', index:'name', width:100, editable:true, edittype:'text'},
//	{name:'id', index:'id',width:50, key:true, sorttype:'int',hidden:false},
//	{name:'note', index:'note', width:200, editable:true, edittype:'textarea'},
//	{name:'download zip', index:'downloadzip',hidden:true},
//	{name:'statinfo', index:'statinfo', width:110, align:'center', formatter:modelsInfoButtonFormatter}
	{name:'name', index:'name', editable:true, edittype:'text'},
	{name:'id', index:'id',width:30,key:true, sorttype:'int',hidden:false},
	{name:'note', width:200, index:'note'},
	{name:'download zip', index:'downloadzip',hidden:true},
	{name:'statinfo', index:'statinfo', align:'center', formatter:modelsInfoButtonFormatter}
    ], //define column models
    pager: '#manage_models_pager', //set your pager div id
    pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
    pginput: false, //ditto
    sortname: 'name', //the column according to which data is to be sorted; optional
    viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� "optional
    sortorder: "asc", //sort order; optional
    shrinkToFit: true,
    gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
    ondblClickRow: function(id){
    	var row = $("#manage_models_grid").jqGrid().getRowData(id);
    	$("#model_dialog_name_edit").val(row['name']);
    	$("#model_dialog_note_edit").val(row['note']);
    	$("#model_edit_note_dialog").data("modelId",id);
    	$("#model_edit_note_dialog").dialog("open");
    	
    },
//    onSelectRow: function(id){
//		if(id && id!==lastsel_models){
//		    jQuery('#manage_models_grid').jqGrid('saveRow',lastsel_models);
//		    // must get a copy of the cell before we set the row editable
//		    lastsel_name = $('#manage_models_grid').jqGrid('getCell', id, 'name');
//		    jQuery('#manage_models_grid').jqGrid('editRow',id,true);
//		    lastsel_models=id;
//		    //alert(lastsel_name);
//		}
//    },
    gridComplete: function(){
    	$('.hermes_button_triple').hrmWidget({
    		widget:'openbuttontriple',
    		onInfo: function(event) {
    			var id = unescape($(this).parent().attr('id'));
    			getModelInfo(id).done(function(data) {
    			    if (!data.success) {
    			    	alert('{{_("Failed: ")}}'+data.msg);
    			    }
    			    else{
	    				$("#model_info_dialog").html(data['htmlstring']);
	    				$("#model_info_dialog").dialog('option','title',data['title']);
	    				$("#model_info_dialog").dialog("open");
    			    }
    			})
	    	  	.fail(function(jqxhr, textStatus, error) {
	    	  		alert("Error: "+jqxhr.responseText);
	    		})
    		},
    		onDel: function(event){
    			var id = unescape($(this).parent().attr('id'));
    			deleteModel(id);
    		},
    		onOpen: function(event){
    			var id = unescape($(this).parent().attr('id'));
    			window.location = "{{rootPath}}model-open?modelId="+id;
    		},
    		onCopy: function(event){
    			var id = unescape($(this).parent().attr('id'));
    			var mName = unescape($(this).parent().attr('name'));
    			copyModel(id,mName);
    		},
            onRun: function(event){
    			var id = unescape($(this).parent().attr('id'));
    			window.location = "{{rootPath}}model-run?modelId="+id;
    		},
            onResults: function(event){
    			var id = unescape($(this).parent().attr('id'));
    			window.location = "{{rootPath}}results-top?modelId="+id;
    		}    		
    	});
//	$(".hermes_info_button").click(function(event) {
//	   // $.getJSON('json/model-info',{modelId:$(this).attr('id')})
//		
//	    event.stopPropagation();
//	});
    },
    editurl:'edit/edit-models.json',	
    caption:"{{_("Select a Model")}}"
    
});
$("#manage_models_grid").jqGrid('navGrid','#manage_models_pager',{edit:false,add:false,del:false});
// setup grid print capability. Add print button to navigation bar and bind to click.
setPrintGrid('manage_models_grid','manage_models_pager','{{_("Select a Model")}}');

// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_models_grid"
  var offset = $(idGrid).offset() //position of grid on page
  var scrollTop = (document.documentElement && document.documentElement.scrollTop) || document.body.scrollTop
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  //minimum height to correspond to original unresized table, in order to line up with side buttons
  //if ( $(window).height() > buttonsBottom ) {
  $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-scrollTop-100);
//  $(idGrid).jqGrid('setGroupHeaders',{
//	  useColSpanStyle:false,
//	  groupHeaders:[
//	               {startColumnName:"{{_('Name')}}",numberOfColumns:1,title
//	            		"{{_('Model ID')}}",
//	            		"{{_('Note')}}",
//	            		"{{_('Download')}}",
//	            		"{{_('Actions')}}"'}
//  })
  //}
}
$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
$(window).resize(resize_grid);  //bind resize_grid to window resize


$(function() {
	$("#model_info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
});

$(function () {
	var names = [];
	$.ajax({
		url:'{{rootPath}}json/get-existing-model-names',
		async: false,
		dataType: 'json',
		success: function(json) {
			console.log(json.names);
			names = json.names;
		}
	});
});	
   
function copyModel(modelId) {
	get_model_name_from_id(modelId)
	.done(function(result){
		if(!result.success){
			alert("Problem getting model name: " + result.msg);
		}
		else{
			$("#model_copy_dlg_from_name").text(""+result.name);
			$("#model_copy_dlg_new_name").val(new_model_copy_name(result.name));
			$("#model_copy_dlg_from_name").data('modelId', modelId);
			$("#model_copy_dialog_form").dialog("open");
		}
	});
}

function deleteModel(modelId) {
	get_model_name_from_id(modelId)
	.done(function(result){
		if(!result.success){
			alert("Problem getting model name: " + result.msg);
		}
		else{
            var msg = '{{_("Really delete the model ")}}' + result.name + " ( " + modelId + " ) ?";
            $("#model_confirm_delete").html(msg);
            $("#model_confirm_delete").data('modelId', modelId);
            $("#model_confirm_delete").dialog("open");
		}
	});
}


$(function() {		
    $("#model_copy_dialog_form").dialog({
	resizable: false,
      	modal: true,
	autoOpen:false,
     	buttons: {
	    '{{_("OK")}}':	function() {
		var srcModelId = $("#model_copy_dlg_from_name").data('modelId');
		var dstName = $("#model_copy_dlg_new_name").val();
		if (dstName == "") {
		    alert('{{_("You must specify a name for the copy")}}');
		}
		else {
		    $( this ).dialog( "close" );
		    $.getJSON('json/copy-model',{srcModelId:srcModelId,dstName:dstName})
			.done(function(data) {					
			    if (data.success) {
				$("#manage_models_grid").trigger("reloadGrid");
			    }
			    else {
				alert('{{_("Failed: ")}}'+data.msg);
			    }
			})
  			.fail(function(jqxhr, textStatus, error) {
  			    alert("Error: "+jqxhr.responseText);
			});
		}
            },
            Cancel: function() {
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
});


$(function() {
	$('#model_edit_note_dialog').dialog({
		autoOpen:false,
		modal:true,
		height:"auto",
		width:"auto",
		buttons:{
			'{{_("Save")}}': function(){
				$.ajax({
					url:'{{rootPath}}edit/update-model-name-note',
					dataType:'json',
					type:'POST',
					data:{'modelId':$(this).data('modelId'),
						  'newName':$('#model_dialog_name_edit').val(),
						  'newNote':$('#model_dialog_note_edit').val()},
					success:function(result){
						if(!result.success){
							if(result.type == "nameExists"){
								alert('{{_("This model name already exists in the database.  Please choose another name")}}');	
							}
							else{
								$("#model_edit_note_dialog").dialog("close");
								alert(result.msg);
							}
						}
						else{
							$('#model_edit_note_dialog').dialog("close");
							$("#manage_models_grid").trigger("reloadGrid");
						}
					}
				});
			},
			'{{_("Cancel")}}':function(){
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
	
    $("#model_confirm_delete").dialog({
	autoOpen:false, 
	height:"auto", 
	width:"auto",
     	buttons: {
	    '{{_("Delete")}}': function() {
		$( this ).dialog( "close" );
	    	$.getJSON('edit/edit-models.json',
			  {id: $("#model_confirm_delete").data('modelId'), 
			   oper:'del'})
	    	    .done(function(data) {
	        	if (data.success) {
			    $("#manage_models_grid").trigger("reloadGrid");
	        	}
	        	else {
	        	    alert('{{_("Failed: ")}}'+data.msg);
	        	}
	    	    })
	    	    .fail(function(jqxhr, textStatus, error) {
	    		alert('{{_("Error: ")}}'+jqxhr.responseText);
	    	    });
		lastsel_models=null;
		
            },
            '{{_("Cancel")}}': function() {
          	$( this ).dialog( "close" );
            }
     	}
    });
});

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });

</script>
 
