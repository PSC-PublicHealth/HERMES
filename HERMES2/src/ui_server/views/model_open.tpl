%rebase outer_wrapper title_slogan=_('Model'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,maymodify=maymodify
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
<script src="{{rootPath}}static/d3/d3.min.js" charset="utf-8"></script>
<script src="{{rootPath}}static/hermes_info_dialogs.js"></script>
<script src="{{rootPath}}static/hermes-ui-utils.js"></script>
<script src="{{rootPath}}static/collapsible-network-diagram/collapsible-network-diagram.js"></script>

<script src="{{rootPath}}static/spin/spin.js"></script>
<script src="{{rootPath}}static/vakata-jstree-841eee8/dist/jstree.min.js"></script>
<!--<link rel="stylesheet" href="{{rootPath}}static/bootstrap-3.3.5-dist/css/bootstrap.css"/>-->
<link rel="stylesheet" href="{{rootPath}}static/collapsible-network-diagram/collapsible-network-diagram.css"/>
<link rel="stylesheet" href="{{rootPath}}static/vakata-jstree-841eee8/dist/themes/default/style.min.css"/>
<script>

var mayModify = "{{maymodify}}" == "True" ? true : false ;

//console.log(mayModify);
function updateNetworkDiagram(){
	$('#ajax_busy_image').show();
	$('#model_operations_holder').fadeTo(500,1.0);
	getModelJson().done(function(result){
		if (!result.success){
			alert(result.msg);
		}
		else{
			//$("#collapsible-network-diagram").remove();
			//$("#model_show_diagram").append("<div id='collapsible-network-diagram'/>");
			$("#collapsible-network-diagram").diagram({
				jsonData:result,
				storeDialogDivID:'model_store_info',
				rootPath:'{{rootPath}}',
				modelId:'{{modelId}}',
				minHeight:500,
				minWidth:490,
				resizeOn:false
				//jsonUrl:'{{rootPath}}json/model-structure-tree-d3?modelId={{modelId}}'
			});
			$("#loading-notify").fadeTo(400,0.0).hide();
			//$("#tooldiv").show();
			$("#ajax_busy_image").hide();
		}
	});
};

function getModelJson(){
	return $.ajax({
		url:'{{rootPath}}json/model-structure-tree-d3?modelId={{modelId}}',
		dataType:'json'
	}).promise();
};

//$(document).ready(function(){
//	//$("#model_diagram_holder").corner();
//	$('#ajax_busy_image').show();
//});

//updateNetworkDiagram();
</script>
<style>
#collapsible-network-diagram{
	width:100%;
	height:100%;
	min-height:500px;
	min-width:380px;
	background:whitesmoke;
}

#model_holder{
	#width:100%;
	#height:100%;
	min-height:500px;
	max-height:700px;
	min-width:800px;
	max-width:1000px;
}
#model_operations_holder{
	float:left;
	#width:45%;
	#height:100%;
	min-width:200px;
	max-width:400px;
	opacity:0;
	#display:none;
}
#model_diagram_holder{
	float:left;
	width:50%;
	height:100%;
	#background-color:;
	padding:10px;
	min-width:400px;
	z-index:5;
	display:inline;
}
#model_show_diagram{
	width:100%;
	height:100%;
	display:inline;
}
.model-operation-title{
	font-size:20px;
	font-weight:bold;
}
.model-operation-second{
	font-size:11px;
}
a.model-operation-item:link{
	font-size:14px;
	color:#282A57;
}
a.model-operation-item:visited{
	font-size:14px;
	color:#282A57;
}
ul.option-list{
	list-style-type:initial;
	margin-left:20px;
	padding:0px;
	font-size:14px;
}
ul.option-list-inner{
	list-style-type:initial;
	margin-left:30px;
	padding:0px;
}

ul.option-list li{
	margin:10px;
}

ul.option-list-inner li{
	margin:10px;
}
.model-diagram-title{
	font-size:14px;
	font-weight:bold;
}
.model-diagram-note{
	font-size:11px;
	font-weight:normal;
	font-style:italics;
}
.notification{
	padding:30px;
	position:absolute;
	top:40%;
	left:40%;
	background-color:#A0A3A6;
	color:white;
	font-weight:bold;
	opacity:0;
	z-index:100;
	display:none;
}
.action-underline{
    border-bottom: 1px dashed;
}
a.model-operation-item:hover{
    text-decoration: none;
    /* border-bottom: none; */
    border-bottom: thin solid;
}
#loading-notify{
	display:inline;
	opacity:0.0;
	position:absolute;
	padding:20px;
	top: 55%;
	left: 32%;
	background:grey;
	font-weight:bold;
	color:white;
}

#note-update-notify{
	display:inline;
	#opacity:0.0;
	position:absolute;
	padding:20px;
	top: 50%;
	left: 36%;
	background:grey;
	font-weight:bold;
	color:white;
}
#model_dialog_note_edit{
	width:100%;
	height:500px;
}
</style>

<div id="model_holder">
	<div id="model_operations_holder">
		<p>
			<span class="hermes-top-main">
				{{_(u"{0} Model".format(name))}}
			</span>
		</p>
		<!--<p><span class="model-operation-second">{{_("Below is a list of operations that you can perform on the model you currently have selected.")}}</span></p>-->
		<br>
		<p><span class="model-operation-title">{{_("Please select what you would like to do with this model:")}}</span></p>
		<ul class="option-list">
		<li><span class="model-operation-item">{{_("Edit model:")}}</span>
			<ul class="option-list-inner">
				<!--<li>
					<span class="model-operation-item">
						<a class="model-operation-item" href="#" title='{{_("Edit the model using a simplified guided process that will give the ability to change important aspects of the supply chain model.")}}'
							id="edit_basic_model_link">{{_("Using the Basic Model Editor")}}</a>
					</span>-->
				<li>
					<span class="model-operation-item">
						<a class="model-operation-item" href="#" title='{{_("Edit the model via the Advanced Model Editor. This will allow users to edit detailed model parameters, including individual route and location characteristics.")}}'
							id="edit_adv_model_link">{{_('Modify structure with the')}} <span class="action-underline">{{_('Advanced Model Editor') }}</span></a>
					</span>
				<li>
				<span class="model-operation-item">
					<a class="model-operation-item" href="#" title='{{_("Populate the model with different components that can then be placed at different locations in the supply chain model.")}}'
						id="types_model_link"><span class="action-underline">{{_('Add or remove model components')}} </span> {{_('(e.g. vaccines, storage devices, vehicles, and population categories)')}}</a>
				</span>	
				<li>
				<span class="model-operation-item">
					<a class="model-operation-item" href="#" title='{{_("Upload a spreadsheet or enter into a table the geographic coordinates of each location in the model")}}'
						id="geocoord_model_link"><span class="action-underline">{{_('Edit Storage Location Geographic Coordinates')}} </span> </a>
				</span>	
				<li>
				<span class="model-operation-item">
					<a class="model-operation-item" href="#" title='{{_("Specify the vaccine dosage schedule for all population categories throughout the year.")}}'
						id="dose_sched_link">{{_('Modify the')}} <span class="action-underline"> {{_('Vaccine Dose Schedule')}} </span></a>
				</span>	
				<li>
				<span class="model-operation-item">
					<a class="model-operation-item" href="#" title='{{_("Define the details needed to implement the HERMES microcosting model, including storage, building, labor, transportation and vaccine costs.")}}'
						id="costs_model_link">{{_('Add and modify')}} <span class="action-underline">{{_('costs')}}</span></a>
				</span>	
				<li>
				<span class="model-operation-item">
					<a class="model-operation-item" href="#" title='{{_("Open the HERMES Transport Loop Generator to explore the effects of implementing transport loops at various levels in your system.")}}'
						id="loop_model_link">{{_('Transform the system with automatically created')}} <span class="action-underline">{{_('transport loops')}}</span></a>
				</span>	
			</ul>
		<li><span class="model-operation-item">
			<a class="model-operation-item" href="#" title='{{_("Run a simulation experiment using the existing model. This allows users to run HERMES in order to simulate a the healthcare supply chain over a specified period of time. Users can then view the results of the run(s) via the results page.")}}'
				id="run_model_link"><span class="action-underline">{{_('Run')}}</span> {{_('a Simulation Experiment with this Model')}}</a>
		</span>
		<li><span class="model-operation-item">
			<a class="model-operation-item" href="#" title='{{_("Access a wide array of visualizations and data from the results of all simulation experiments run with this model")}}'
				id="result_model_link"><span class="action-underline">{{_('View Results')}} </span> {{_('from previously saved Simulation Experiments')}}</a>
		</span>
		<li>
		<span class="model-operation-item">
			<a class="model-operation-item" href="#" title='{{_("Export the current model as a .zip file, in order to save, send and view the model and its results on any other HERMES-installed computer.")}}' 
				id="download_model_link"><span class="action-underline">{{_('Export Model')}} </span> {{_('as a HERMES Zip File')}}</a>
		</span>
		</ul>
	</div>
	
	<div id="model_diagram_holder">
		<ul>
			<li><a href="#model_show_diagram">{{_('Model Network')}}</a></li>
			<li><a href="#model_test">{{_('Notes')}}</a></li>
		</ul>
		<div id="model_test">
			<p><span class="model-diagram-title">{{_(u'Notes for {0} model'.format(name))}}</span></p>
			<span class="model-diagram-note"><textarea rows="30" cols="55" id="model_dialog_note_edit"></textarea></span>
			<button style="width:100%;" id="submit_note">{{_("Save Notes")}}</button>
			<div id="note-update-notify">
				<p>{{_("Note Updated")}}</p>
			</div>
		</div>
		<div id="model_show_diagram">
			<p><span class="model-diagram-title">{{_("Supply Chain Network Diagram")}}</span></p>
			<p><span class="model-diagram-note">{{_("This diagram depicts the structure of this supply chain.  Clicking on a location can expand or contract the routes and locations below the selected location. Right-clicking a location or route will bring up more detailed information.")}}</span></p>
			</div>
			<div id="collapsible-network-diagram"></div>
			<div id="loading-notify">{{_("Preparing Diagram")}}</div>
		</div>
	</div>
</div>

<div id="result_dialog" title='{{_("Simulation Experiment Results")}}'>
<div id="result"></div>
</div>

<div id="model_dowantcopy_dialog">
	{{_("This model already has Simulation Experiments associated with it, so you will need to make a copy if you would like to edit it. Would you like to make a copy now?")}}
</div>

<div id="model_copy_dialog_form" title='{{_(u"Make a copy of model {0}".format(name))}}'>
	<form>
		<fieldset>
			<table style="width:100%;">
			  	<tr>
					<td>
						{{_('Model To Copy')}}
					</td>
					<td id='model_copy_dlg_from_name'>
						replace me
					</td>
				</tr>
				<tr>
		  			<td>
		  				<label for="model_copy_dlg_new_name">
		  					{{_('Name Of The Copy')}}
		  				</label>
		  			</td>
		  			<td>
		  				<input type="text" name="model_copy_dlg_new_name" id="model_copy_dlg_new_name" style="width:100%;" class="text ui-widget-content ui-corner-all" />
		  			</td>
		  		</tr>
		  	</table>
		</fieldset>
	</form>
</div>

<div id="download_model_dialog" title='{{_("Export model".format(name))}}'>
	<table style="width:100%;">
		<tr>
			<td>
				{{_("Please name the export file name: ")}}
			</td>
			<td style="width:70%;">
				<input type="text" id="export_filename" style="width:100%">
			</td>
			<td>
				.zip
			</td>
		</tr>
	</table>
</div>

<div id="downloading_notify" class="notification">
	{{_("Exporting HERMES Model File")}}
</div>

<div id="dialog-modal" title='{{_("Invalid Entry")}}'>
	<div id="dialog-modal-text"/></div>
</div>

<div id="not-implemented-modal" title='{{_("Feature is not yet implemented")}}'>
	<p>   {{_('The Basic Model Editor is not yet implemented. We apologize for the inconvenience.  Please try editting the model with the advanced editor.')}} </p>
</div>


<script>

$(document).ready(function(){
	$.ajax({
		url:'{{rootPath}}json/set-selected-model?id={{modelId}}',
		dataType:'json',
		success:function(result){
			if(!result.success){
				alert(result.msg);
			}
		}
	});
	
	//$("#model_diagram_holder").corner();
	$("#model_diagram_holder").tabs();
	$(".notification").corner();
	$("#note-update-notify").corner();
	$("#note-update-notify").hide();
	$("#loading-notify").corner();
	$("#loading-notify").fadeTo(400,1.0);
	$("#submit_note").button();
	$.ajax({
		url:'{{rootPath}}json/get-model-notes',
		datatype:'json',
		data:{'modelId':{{modelId}}},
		method:'post'
	})
	.done(function(results){
		if(!results.success){
			alert(results.msg);
		}
		else{
			$("#model_dialog_note_edit").val(results.notes);
		}
	})
	.fail(function(jqxhr, textStatus, error) {
    	alert("Error: " + jqxhr.responseText);
    });
	
	updateNetworkDiagram();
});
	
	$("#submit_note").click(function(){
		$.ajax({
			url:"{{rootPath}}edit/update-model-name-note",
			method:"post",
			datatype:"json",
			data:{"modelId":{{modelId}},
				  "newName":"{{name}}",
				  "newNote":$("#model_dialog_note_edit").val()}
		})
		.done(function(results){
			if(!results.success){
				alert(results.msg);
			}
			else{
				$("#note-update-notify").fadeIn(400).delay(200).fadeOut(400);
			}
		})
		.fail(function(jqxhr, textStatus, error) {
	    	alert("Error: " + jqxhr.responseText);
	    });
	});
	
	$("#not-implemented-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			'{{_("OK")}}': function() {
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
	$("#result_dialog").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
		buttons:{
			'{{_("Close")}}':function(){
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
	
//	$.ajax({
//		url:'{{rootPath}}json/results-tree-for-model?modelId={{modelId}}',
//		dataType:'json',
//		success: function(result){
//			if(!result.success){
//				alert(result.msg);
//			}
//			else{
//				if(result.rgnames.length == 0){
//					$("#result").text("{{_('This Model has no Simulation Experiments.')}}");
//				}
//				else{
//					window.location = '{{rootPath}}/results-top?modelId={{modelId}}';
//				//{ 'data': result.rgnames }});
//				}
//			}
//		}
//	});
	
	//Link Actions
	$("#edit_basic_model_link").click(function(){
		//editBasicModel({{modelId}});
		$("#not-implemented-modal").dialog("open");
	});
	$("#edit_adv_model_link").click(function(){
		editAdvancedModel({{modelId}});
	});
	
	$("#types_model_link").click(function(){
		editTypes({{modelId}});
	});
	
	$("#geocoord_model_link").click(function(){
		editGeoCoords({{modelId}});
	});
	$("#dose_sched_link").click(function(){
		editDoseSched({{modelId}});
	});
	
	$("#run_model_link").click(function(){
		runHermes({{modelId}});
	});
	
	$("#download_model_link").click(function(){
		$("#download_model_dialog").dialog("open");
	});
	
	$("#costs_model_link").click(function(){
		editCosts({{modelId}});
	})
	$("#result_model_link").click(function(){
		openResults({{modelId}});
		//$("#result_dialog").dialog("open");
	});
	
	$("#loop_model_link").click(function(){
		createLoops({{modelId}});
	});
	
	//Dialog box code
	$("#dialog-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			'{{_("OK")}}': function() {
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
	
	$("#download_model_dialog").dialog({
		resizable:false,
		modal:true,
		autoOpen:false,
		width:400,
		buttons:{
			'{{_("Save")}}':function(){
				if(!$("#export_filename").val()){
					alert("A name must be specified for the exported zip file");
					$("#export_filename").focus().select();
				}
				else{
					$(this).dialog('close');
					$("#downloading_notify").show();
					$("#downloading_notify").fadeTo(200,1.0);
					$.ajax({
						url:'{{rootPath}}json/prepare-download-model?model={{modelId}}&form=zip&fname='+$("#export_filename").val(),
						dataType:'json',
						success:function(result){
							$("#downloading_notify").fadeOut(200,function(){
								$(this).remove();
							});
							window.location='{{rootPath}}download-model?filename='+result.filename+'&zipfilename='+ result.zipname;
						}
							
					});
				}
			},
			'{{_("Cancel")}}':function(){
				$(this).dialog('close');
			}
		},
		open: function(e,ui) {
			$("#export_filename").val('{{name}}_{{modelId}}');
			$("#export_filename").focus().select();
		    $(this)[0].onkeypress = function(e) {
				if (e.keyCode == $.ui.keyCode.ENTER) {
				    e.preventDefault();
				    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
				}
		    };
		}	
	});
	
	$("#model_dowantcopy_dialog").dialog({
		resizable:false,
		modal:true,
		autoOpen:false,
		buttons:{
			'{{_("Yes")}}':function(){
				$(this).dialog("close");
				$("#model_copy_dlg_from_name").text("{{name}}")
				$("#model_copy_dlg_new_name").val(new_model_copy_name("{{name}}"));
				$("#model_copy_dlg_from_name").data('modelId',{{modelId}});
				$("#model_copy_dialog_form").dialog("open");
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
			
   $("#model_copy_dialog_form").dialog({
    	resizable: false,
      	modal: true,
      	autoOpen:false,
      	width:400,
     	buttons: {
     		'{{_("Save")}}':	function() {
				var srcModelId = $("#model_copy_dlg_from_name").data('modelId');
				console.log(srcModelId);
				var dstName = $("#model_copy_dlg_new_name").val();
				if (dstName == "") {
				    alert('{{_("A name for the newly copyied model must be given to proceed.")}}');
				}
				else {
				    $.getJSON('json/get-existing-model-names')
				    .done(function(result){
				    	if(!result.success){
				    		alert("Failure in Coping Model dialog getting existing model names: " + result.msg);
				    	}
				    	else{
				    		if(result.names.indexOf(dstName) !== -1){
				    			alert(dstName +": " + "{{_('This model name already exists. Please select another')}}");
				    			$("#model_copy_dlg_new_name").focus().select();
				    		}
				    		else{
				    			$("#model_copy_dialog_form").dialog("close");
							    $.getJSON('json/copy-model',{srcModelId:srcModelId,dstName:dstName})
								.done(function(data) {
								    if (data.success) {
								    	window.location = '{{rootPath}}model-open?modelId='+data.value;
								    }
								    else {
								    	alert('{{_("Model Copy Failed: ")}}'+data.msg);
								    }
								})
					  			.fail(function(jqxhr, textStatus, error) {
					  			    alert("Error: "+jqxhr.responseText);
								});
				    		}
				    	}
				    });
				}
     		},
		    '{{_("Cancel")}}': function() {
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
//});

function editBasicModel(modelId){
	// check if this model has already been run
	if(!mayModify){
		$('#model_dowantcopy_dialog').dialog("open");
	}
	else{
		alert("The Basic Model Editor has not been implemented yet");
	}
};

function editAdvancedModel(modelId){	
	if(!mayModify){
		$('#model_dowantcopy_dialog').dialog("open");
	}
	else{
		window.location = '{{rootPath}}model-edit-structure?id=' + modelId;
	}
};

function editTypes(modelId){
	if(!mayModify){
		$('#model_dowantcopy_dialog').dialog("open");
	}
	else{
		window.location = '{{rootPath}}model-add-types?id=' + modelId + '&create=false';
	}
};

function editDoseSched(modelId){
	if(!mayModify){
		$("#model_dowantcopy_dialog").dialog("open");
	}
	else{
		window.location = '{{rootPath}}demand-top?modelId='+modelId;
	}
}
function editCosts(modelId){
	if(!mayModify){
		$("#model_dowantcopy_dialog").dialog("open");
	}
	else{
		window.location = '{{rootPath}}cost-top?modelId='+modelId;
	}
}
function runHermes(modelId){
	window.location = "{{rootPath}}model-run?modelId="+modelId;
};

function editGeoCoords(modelId){
	if(!mayModify){
		$("#model_dowantcopy_dialog").dialog("open");
	}
	else{
		window.location='{{rootPath}}model-edit-geocoords-tabular?modelId='+modelId;
	}
}

function createLoops(modelId){
	if(!mayModify){
		$("#model_dowantcopy_dialog").dialog("open");
	}
	else{
		window.location='{{rootPath}}loops-top?modelId='+modelId;
	}
}
function openResults(modelId){
	$.ajax({
		url:'{{rootPath}}json/has-results?modelId='+modelId,
		dataType:'json',
		success:function(result){
			if(result.hasResults){
				window.location = '{{rootPath}}results-top?modelId='+modelId;
			}
			else{
				alert("{{_('This model has no results')}}");
			}
		}
	});
}

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });

</script>

