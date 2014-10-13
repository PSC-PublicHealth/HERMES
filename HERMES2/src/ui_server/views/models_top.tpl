%rebase outer_wrapper title_slogan=_('Available Models'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<table>
<tr><td  style="border-style:solid">
<h2>{{_('Task:')}}</h2>
<table>
<tr><td><button id="create_model_from_scratch_button" style="width:100%">{{_('Create')}}</button></td></tr>
<!-- tr><td><button id="edit_model_button" style="width:100%" >{{_('Modify An Existing Model')}}</button></td></tr -->
<tr><td><button id="edit_sc_button" style="width:100%">{{_('Modify')}}</button></td></tr>
<tr><td><button id="show_structure_model_button" style="width:100%">{{_('Show')}}</button></td></tr>
<tr><td><button id="copy_model_button" style="width:100%">{{_('Copy')}}</button></td></tr>
<tr><td><button id="upload_model_button" style="width:100%"> {{_('Upload')}}</button></td></tr>
<tr><td><button id="delete_model_button" style="width:100%">{{_('Delete')}}</button></td></tr>
</table>
</td>

<td  style="border-style:solid">
<h3>{{_('Select A Model')}}</h3>
<table id="manage_models_grid"></table>
<div id="manage_models_pager"> </div>
</td>
</tr>
</table>

<input id="zipmodelupload" type="file" name="files[]" 
	data-url="{{rootPath}}upload-model" style="display:none">
<div id="progress">
    <div class="bar" style="width: 0%;"></div>
</div>

<div id="model_show_dialog_form" title={{_('Show Supply Chain For A Model')}}>
  <form>
  <fieldset>
  	<table>
	  	<tr>
  			<td><label for="model_show_dlg_model_select">{{_('Model To Show')}}</label></td>
  			<td><select name="model_show_dlg_model_select" id="model_show_dlg_model_select"></select></td>
  		</tr>
    </table>
  </fieldset>
  </form>
</div>

<div id="model_edit_sc_dialog_form" title={{_('Edit Supply Chain For A Model')}}>
  <form>
  <fieldset>
  	<table>
	  	<tr>
  			<td><label for="model_edit_sc_dlg_model_select">{{_('Model To Edit')}}</label></td>
  			<td><select name="model_edit_sc_dlg_model_select" id="model_edit_sc_dlg_model_select"></select></td>
  		</tr>
    </table>
  </fieldset>
  </form>
</div>

<div id="model_copy_dialog_form" title={{_("Copy A Model")}}>
  <form>
  <fieldset>
  	<table>
	  	<tr>
  			<td><label for="model_copy_dlg_model_select">{{_('Model To Copy')}}</label></td>
  			<td><select name="model_copy_dlg_model_select" id="model_copy_dlg_model_select"></select></td>
  		</tr>
  		<tr>
    		<td><label for="model_copy_dlg_new_name">{{_('Name Of The Copy')}}</label></td>
    		<td><input type="text" name="model_copy_dlg_new_name" id="model_copy_dlg_new_name" class="text ui-widget-content ui-corner-all" /></td>
    	</tr>
    </table>
  </fieldset>
  </form>
</div>


<div id="zipupload-dialog-form" title={{_("Upload a Model in Zip Form")}}>
  <p class="validateTips">{{_('What name should the new model have?')}}</p>
  <form>
  	<fieldset>
  		<table>
  			<tr>
  				<td>
  					<label for="shortname">{{_('Name')}}</label>
  				</td>
  				<td>
  					<input type="text" name="shortname" id="shortname" class="text ui-widget-content ui-corner-all" />
  				</td>
  			</tr>
  			<tr>
  				<td>
  					<label for="filename">{{_('File')}}</label>
  				</td>
  				<td>
  					<input id="zipfilename" type="file" name="files[]" accept="application/zip">
  				</td>
  			</tr>
  		</table>
  </fieldset>
  </form>
</div>

<div id="model_info_dialog" title="This should get replaced">
</div>

<div id="model_confirm_delete" title='{{_("Delete Model")}}'>
</div>

<script>
{{!setupToolTips()}}

function modelsInfoButtonFormatter(cellvalue, options, rowObject) {
	// cellvalue will be an integer
	return "<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>";
}

var lastsel_models;
$("#manage_models_grid").jqGrid({ //set your grid id
   	url:'json/manage-models-table',
	datatype: "json",
	//width: 750, // deprecated with resize_grid
	//height:'auto', //expand height according to number of records
  rowNum:9999, // rowNum=-1 has bugs, suggested solution is absurdly large setting to show all on one page
	colNames:[
		"{{_('Name')}}",
		"{{_('Model ID')}}",
		"{{_('Note')}}",
		"{{_('Download Zip')}}",
		"{{_('Model Status')}}"
	], //define column names
	colModel:[
	{name:'name', index:'name', width:100, editable:true, edittype:'text'},
	{name:'id', index:'id', width:50, key:true, sorttype:'int'},
	{name:'note', index:'note', width:200, editable:true, edittype:'textarea'},
	{name:'download zip', index:'downloadzip'},
	{name:'statinfo', index:'statinfo', width:110, align:'center', formatter:modelsInfoButtonFormatter}
	], //define column models
	pager: '#manage_models_pager', //set your pager div id
	pgbuttons: false, //since showing all records on one page, remove ability to navigate pages
  pginput: false, //ditto
	sortname: 'name', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
	sortorder: "asc", //sort order; optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
   	onSelectRow: function(id){
		if(id && id!==lastsel_models){
			jQuery('#manage_models_grid').jqGrid('saveRow',lastsel_models);
			jQuery('#manage_models_grid').jqGrid('editRow',id,true);
			lastsel_models=id;
		}
	},
	gridComplete: function(){
		$(".hermes_info_button").click(function(event) {
			$.getJSON('json/model-info',{modelId:$(this).attr('id')})
					.done(function(data) {
						if (data.success) {
							$("#model_info_dialog").html(data['htmlstring']);
							$("#model_info_dialog").dialog('option','title',data['title']);
							$("#model_info_dialog").dialog("open");
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
    editurl:'edit/edit-models.json',	
    caption:"{{_("Available Models")}}"

});
$("#manage_models_grid").jqGrid('navGrid','#manage_models_pager',{edit:false,add:false,del:false});
// setup grid print capability. Add print button to navigation bar and bind to click.
setPrintGrid('manage_models_grid','manage_models_pager','{{_("Available Models")}}');


var table_orig_height = $("#manage_models_grid").parent().closest('td').height(); //get original height of table containing jqGrid
// resize jqGrid according to window size
function resize_grid() {
  var idGrid = "#manage_models_grid"
  var offset = $(idGrid).offset() //position of grid on page
 
  //hardcoded minimum width
  if ( $(window).width() > 710 ) {
    $(idGrid).jqGrid('setGridWidth', $(window).width()-offset.left-50);
  }
  //minimum height to correspond to original unresized table, in order to line up with side buttons
  if ( $(window).height() > ( $(idGrid).parent().closest('td').offset().top + table_orig_height + 70) ) {
    $(idGrid).jqGrid('setGridHeight', $(window).height()-offset.top-130);
  }
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
	
    $( "#zipupload-dialog-form" ).dialog({
    	autoOpen: false,
     	height: 300,
    	width: 400,
    	modal: true,
    	buttons: {
        	'OK': {
        		text: "Upload model",
        		click: function() {
          			$("#shortname").removeClass( "ui-state-error" );
          			// Error Checking
          			if(names.indexOf($("#shortname").val()) > -1){
          				alert("The Model Name "+$('#shortname').val()+" already exists. Please choose another.");
          			}
          			else if(!$('#shortname').val()) {
          				alert("The Model Name field must be set to proceed.");
          			}
          			else if(!$('#zipfilename').val()){
          				alert("You must choose a file to be uploaded.");
          			}
          			else {
          				var files = $("#zipfilename").prop("files");
          				$('#zipmodelupload').fileupload('add',{files:files,formData:[{name:'shortname',value:$("#shortname").val()}]});
          				console.log("done submitting");
          				$("#ajax_busy").show();
          				$(this).dialog("close");
          			}
        		}
          	},
          	"CANCEL": {
        		text: "Cancel",
       			click: function() {
          			$( this ).dialog( "close" );
          		}
			}
		},
      	close: function() {
        	$("#shortname").val( "" ).removeClass( "ui-state-error" );
        	$("#zipfilename").val('');
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
    
    $('#zipfilename').change( function () {
    	$("#shortname").val($(this).val().split('\\').pop().replace(/\.[^/.]+$/,""));
    });
    
    $('#zipmodelupload').fileupload({
        dataType: 'json',
        formData: [],
        autoUpload: true,
        url: "{{rootPath}}upload-model",
        // Add is overriden by the programatic call in the dialog box
        done: function (e, data) {
        	if (typeof data.result.files == 'undefined') {
        		alert(data.result.message);
        	}
        	else {
        		$.each(data.result.files, function (index, file) {
        			alert( 'got '+file.name+' '+file.size+' bytes');
        		});
        		$("#ajax_busy").hide()
				$("#manage_models_grid").trigger("reloadGrid"); // so the grid reflects the presence of the new model
        	}
		},
	    progressall: function (e, data) {
  			var progress = parseInt(data.loaded / data.total * 100, 10);
        	$('#progress .bar').css('width',progress + '%');
        }
    });
});

$(function() {

	var btn = $("#create_model_from_scratch_button");
	btn.button();
	btn.click( function() {
		window.location="model-create";
	});

});

$(function() {
	$("#model_copy_dialog_form").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK:	function() {
				var srcModelId = $("#model_copy_dlg_model_select").val();
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

	var btn = $("#copy_model_button");
	btn.button();
	btn.click( function() {
  		$.getJSON('{{rootPath}}list/select-model')
		.done(function(data) {
			var sel = $("#model_copy_dlg_model_select");
    		sel.append(data['menustr']);
			$("#model_copy_dialog_form").dialog("open");
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
	});

});

$(function() {
	$("#model_show_dialog_form").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				var srcModelId = $("#model_show_dlg_model_select").val();
				$( this ).dialog( "close" );
				window.location = "model-show-structure?id="+srcModelId;
        	},
        	Cancel: function() {
          		$( this ).dialog( "close" );
        	}
        },
        open: function(e,ui) {
        	$(this).keypress(function(e) {
        		if (e.keyCode == $.ui.keyCode.ENTER) {
        			e.preventDefault();
        			$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
        		}
        	});
        }
	});

	var btn = $("#show_structure_model_button");
	btn.button();
	btn.click( function() {
  		$.getJSON('{{rootPath}}list/select-model')
		.done(function(data) {
			var sel = $("#model_show_dlg_model_select");
    		sel.append(data['menustr']);
			$("#model_show_dialog_form").dialog("open");
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
	});

});

$(function() {
	$("#model_edit_sc_dialog_form").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				var srcModelId = $("#model_edit_sc_dlg_model_select").val();
				$( this ).dialog( "close" );
				window.location = "model-edit-structure?id="+srcModelId;
        	},
        	Cancel: function() {
          		$( this ).dialog( "close" );
        	}
        },
		open: function(e,ui) {
			$(this).keypress(function(e) {
				if (e.keyCode == $.ui.keyCode.ENTER) {
					e.preventDefault();
					$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
				}
			});
		}
	});

	var btn = $("#edit_sc_button");
	btn.button();
	btn.click( function() {
  		$.getJSON('{{rootPath}}list/select-model')
		.done(function(data) {
			var sel = $("#model_edit_sc_dlg_model_select");
    		sel.append(data['menustr']);
			$("#model_edit_sc_dialog_form").dialog("open");
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
	});

});

$(function() {

	var btn = $("#upload_model_button");
	btn.button();
	btn.click( function() {
		$("#zipupload-dialog-form").dialog("open");
	});

});

$(function() {
	$("#model_confirm_delete").dialog({
		autoOpen:false, 
		height:"auto", 
		width:"auto",
     	buttons: {
			'{{_("Delete")}}': function() {
				$( this ).dialog( "close" );
	    		$.getJSON('edit/edit-models.json',{id:lastsel_models, oper:'del'})
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

	var btn = $("#delete_model_button");
	btn.button();
	btn.click( function() {
		if (lastsel_models==null) {
			alert('{{_("No Selection")}}');
		}
		else {
			$("#manage_models_grid").jqGrid('restoreRow',lastsel_models);
			var modelId = $("#manage_models_grid").jqGrid('getCell', lastsel_models, 'id');
			var modelName = $("#manage_models_grid").jqGrid('getCell', lastsel_models, 'name');
			var myMsg = '{{_("Really delete the model ")}}' + modelName + " ( " + modelId + " ) ? ";
			$("#model_confirm_delete").html(myMsg);
			$("#model_confirm_delete").dialog("open");
		}
	});
});


  
</script>
 