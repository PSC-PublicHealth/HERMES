%rebase outer_wrapper _=_,title_slogan=_('Supply Chain Modeling Tool'),inlizer=inlizer
<!---
-->
<style>
#sp_top_div{
	position: relative;
	min-width:600px;
	top: 0px;
	left: 0px;
	border-style: none;
	border-width: 2px;
	text-align: center;
}
#sp_content_div{
	display: block;
	position: relative;
	width:80%;
/*	float:none;
	margin: 0 auto;*/
	margin-left: auto;
	margin-right: auto;
}
.big_title{
	font-size:32px;
	opacity:0;
}
.second_title{
	font-size:18px;
	opacity:0;
}
.large_dialog_font{
	font-size:16px;
	font-family:'Century Gothic', Arial, 'Arial Unicode MS', Helvetica, Sans-Serif;
}
.large_dialog_font p{
	padding:10px;
	text-align:center;
}
#welcome_options{
	padding-top:30px;
	opacity:0;
}
.welcome_item{
	font-size:18px;
	position: relative;

}
.welcome_item a:visited{
	color:#282A57;
}
.welcome_item a:active{
	color:#282A57;
}
.welcome_item a:hover{
	color:#282A57;
}
.welcome_item a:link{
	color:#282A57;
}
.info_item{
        font-size:14px;
}
.info_item a:visited{
        color:#282A57;
}
.info_item a:active{
        color:#282A57;
}
.info_item a:hover{
        color:#282A57;
}
.info_item a:link{
        color:#282A57;
}


#wrappage_help_button{
	opacity:0;
}
#dev_page_hidden{
	position:fixed;
	top:150px;
	left:50px;
	width:50px;
}
</style>
<input id="zipmodelupload" type="file" name="files[]" 
	data-url="{{rootPath}}upload-model" style="display:none">
<div id="progress">
    <div class="bar" style="width: 0%;"></div>
</div>

<div id="sp_top_div" class="sp_top_div">
	<div id="sp_content_div" class="content_div">
		      	<div class="logo_div">
			     <img src="{{rootPath}}static/images/HERMES_Text_RGB_wide.png" style="width: 400px">
			</div>


			<div id="welcome_options">
				<p>
					<span class="welcome_item">
						<a id='create_model_link' href="#" 
							title='{{_("Create a new model from scratch via the Model Creation Guided Workflow. This will walk users step-by-step through the model creation process.")}}'>
							{{_("Create or Upload a New Model")}}
						</a>
					</span>
				</p>
				<p>
					<span class="welcome_item">
						<a href="{{rootPath}}models-top"
							title='{{_("Open and modify an existing model. This will allow users to modify an existing model via step-by-step guided workflow or the Advanced Model Editor.")}}'>
							{{_("Open, Modify, and Run an Existing Model")}}
						</a>
					</span>
				</p>
				<p>
					<span class="welcome_item">
						<a href="{{rootPath}}results-top"
							title='{{_("View and compare results for models that have already been run. This will allow users to select and view results.")}}'>
							{{_("View and Compare Results from Previous Model Runs")}}
						</a>
					</span>
				</p>
				<br><br>
				<p>
					<span class="second_title" color="#282A57">
						{{_("For more information:")}}
					</span>
				</p>
	                        <p>
	                                <span class="info_item">
		                                <a href="http://hermes.psc.edu/release/tutorials.html" target=_blank
		                                        title='{{_("Download PDF containing tutorials for creating and using HERMES models.")}}'>
		                                        {{_("HERMES Tutorials")}}
		                                </a>
	                                </span>
	                        </p>
				<p>
					<span class="info_item">
						<a href="{{rootPath}}vaccines-top"
							title='{{_("View supply chain component databases. Databases include vaccines, population, vehicles, and storage devices. This will allow users to view detailed information about supply chain components available for use in HERMES models.")}}'>
							{{_("View Databases")}}
						</a>
					</span>
				</p>
				<p>
					<span class="info_item">
						<a href="http://hermes.psc.edu" target="blank"
							title='{{_("Visit the HERMES Website to see team members, project details, and publications.")}}'>
						{{_('Visit the HERMES Website for More Information about the Project')}}
						</a>
					</span>
				</p>
			</div>
			<!-- Hiding Developer Mode from Users <div id="dev_page_hidden"><span class="hrm_invisible"><a id="toggle_dev_mode" href="#">Toggle Dev Mode</a></span></div> -->
	</div>
</div>
<!--- STB Recreating this from the models_top form to give the functionality here too.-->
<div id="model_create_or_upload_start" title='{{_("Create or Upload a New Model")}}'>
	<span class="large_dialog_font">
	<p> 
		{{_('Would you like to')}} 
	</p>
	<p style="margin-left:10px;">
		<a href="#" id="create_choice">{{_("Create a New Model")}}</a>
	</p>
	<p>	
		{{_('or')}}
	</p>
	<p style="margin-left:10px;">
		<a href="#" id="upload_choice">{{_("Upload an Existing Model from a HERMES .HZP File")}} ? </a>
	</p>
	</span>
</div>

<div id="model_create_dialog_form" title='{{_("Create a New Model")}}'>
	<form>
		<fieldset>
			<table>
				<tr>
					<td colspan=2>
						{{_("Please create a name for the new model - the new name must be unique from all existing models.")}}
					</td>
				</tr>
				<tr>
					<td><span title='{{_("The name of the model is entered here and can be anything you would like (e.g. the name of a country, state, province, etc...).")}}'>
						{{_('New Model Name.')}}</span></td>
					<td>
						<input type="text" name="model_create_dlg_new_name" 
							id="model_create_dlg_new_name" class="text ui-widget-content ui-corner-all" />
					</td>
				</tr>
			</table>
		</fieldset>
	</form>
</div>

<div id="zipupload-dialog-form" title={{_("Upload a Model in .HZP Form")}}>
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
						<input id="zipfilename" type="file" name="files[]" accept=".hzp">
					</td>
				</tr>
			</table>
		</fieldset>
	</form>
</div>
	
<div id="model_confirm_delete" title='{{_("Delete Model")}}'></div>

<div id="model_create_existing_dialog" title='{{_("Model Creation Started")}}'>
	<p>{{_('You have already started creating this model, would you like to continue or start over?')}} 
</div>

<script>
$(function(){
	//$(".big_title").addClass('animated fadeIn');
	$(".big_title").fadeTo(2000,1.0);
	setTimeout(function(){
		$(".second_title").fadeTo(2000,1.0);
	},500);
	setTimeout(function(){
		$('#welcome_options').fadeTo(2000,1.0);
	},1000);
	setTimeout(function(){
		$('#logo_div').fadeTo(2000,1.0);
	},1500);
	
	$("#create_model_link").click(function(e){
		e.preventDefault();
		$("#model_create_or_upload_start").dialog('open');
	});
	
	$("#toggle_dev_mode").click(function() {
	   // $.getJSON("{{rootPath}}json/toggle-devel-mode",{})
	    $.ajax({
	    	url:"{{rootPath}}json/toggle-devel-mode",
	    	data:'json'
	    })
        .done(function(json) { 
        	if(!json.success){
        		alert(json.msg);
        	}
        	else{
        	console.log("developer mode toggled"); 
        	}
        //.fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
        	location.reload();
        });
	});
	
	$("#model_create_or_upload_start").dialog({
		resizable: false,
		modal: true,
		autoOpen: false,
		width:500,
		buttons:{
			'{{_("Cancel")}}':function(){
				$(this).dialog("close");
			}
		}
	});
	
	$("#create_choice").click(function(){
		$("#model_create_or_upload_start").dialog("close");
		$("#model_create_dialog_form").dialog("open");
	});

	$("#upload_choice").click(function(){
		$("#model_create_or_upload_start").dialog("close");
		$("#zipupload-dialog-form").dialog("open");
	});
	
	$("#model_create_dialog_form").dialog({
		resizable: false,
	  	modal: true,
		autoOpen:false,
		width:500,
	 	buttons: {
	    	'{{_("Create")}}': function() {
	    		$.ajax({
	    			url:'{{rootPath}}json/get-existing-models-creating',
	    			async:false,
					dataType:'json',
					success: function(json){
						if (json.names.indexOf($("#model_create_dlg_new_name").val())>-1){
							$('#model_create_dialog_form').dialog("close");
							$('#model_create_existing_dialog').dialog("open");
						}
						else if (!$("#model_create_dlg_new_name").val()){
				    		alert("{{_('The New Model Name fields must be set to proceed.')}}");
				    	}
				    	else if (json.dbnames.indexOf($("#model_create_dlg_new_name").val()) >-1){
				    		alert("{{_('Model name already exists in the database, please use another name.')}}");
				    	}
				    	else{
				    		$("#model_create_dialog_form").dialog('close');
				    		window.location="model-create?name="+$("#model_create_dlg_new_name").val();
				    	}
					}
	    		});
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
	
	$("#model_create_existing_dialog").dialog({
		resizable: false,
		model: true,
		autoOpen:false,
		buttons:{
			'{{_("Continue")}}': function() {
				$(this).dialog("close");
				window.location="model-create?name="+$("#model_create_dlg_new_name").val();
			},
			'{{_("Restart")}}': function(){
				$(this).dialog("close");
				$.ajax({
					url:'{{rootPath}}json/get-newmodelinfo-from-session',
					async:false,
					dataType:'json',
					success: function(json){
						if ($("#model_create_dlg_new_name").val() in json.data){
							thisModelJSon = json.data[$("#model_create_dlg_new_name").val()];
							$.ajax({
								url:'{{rootPath}}json/delete-model-from-newmodelinfo-session?name='+$("#model_create_dlg_new_name").val(),
			    				async:false,
								dataType:'json',
								success:function(data){
									if ('modelId' in thisModelJSon){
										if(json.modelExists){
										/// must delete this model first
											deleteModel(thisModelJSon.modelId,$("#model_create_dlg_new_name").val());
										}
									}
									window.location='{{rootPath}}model-create?name='+$("#model_create_dlg_new_name").val()
								}
							});
						}
					}
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
	
	$( "#zipupload-dialog-form" ).dialog({
    	autoOpen: false,
     	height: 300,
    	width: 400,
    	modal: true,
    	buttons: {
        	'OK': {
        		text: "Upload model",
        		click: function() {
        			get_existing_model_names().done(function(results){
        				var names = results.names;
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
	          				$('#zipupload-dialog-form').dialog("close");
	          			}
        			});
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
	$("#model_confirm_delete").dialog({
		autoOpen:false, 
		height:"auto", 
		width:"auto",
		buttons: {
			'{{_("Delete")}}': function() {
				$( this ).dialog( "close" );
				$.getJSON('edit/edit-models.json',
					{id: modelInfo.modelId, 
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
%if defined('createnew'):
%	if createnew == 1:
	$("#create_model_link").click();
%	end
%end
});

function deleteModel(modelId, modelName) {
    var msg = '{{_("Really delete the model ")}}' + modelName + " ( " + modelId + " ) ?";
    $("#model_confirm_delete").html(msg);
    $("#model_confirm_delete").data('modelId', modelId);
    $("#model_confirm_delete").dialog("open");
}
</script>
