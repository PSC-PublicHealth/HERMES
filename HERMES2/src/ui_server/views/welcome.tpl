%rebase outer_wrapper _=_,title_slogan=_('Supply Chain Modeling Tool'),inlizer=inlizer

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
	position: relative;
	width:80%;
	float:none;
	margin: 0 auto;
}
.big_title{
	font-size:32px;
	opacity:0;
}
.second_title{
	font-size:18px;
	opacity:0;
}
#welcome_options{
	padding-top:30px;
	opacity:0;
}
.welcome_item{
	font-size:18px;
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

<div id="sp_top_div" class="sp_top_div">
	<div id="sp_content_div" class="content_div">
		<div class = "options_div">
			<div id="welcome_title">
				<span class="big_title">
					{{_("Welcome to HERMES")}}
				</span>
				<br>
				<span class="second_title">
					{{_("What would you like to do?")}}
				</span>
			</div>
			
			<div id="welcome_options">
				<p>
					<span class="welcome_item">
						<a id='create_model_link' href="#" 
							title='{{_("Create a new model from scratch")}}'>{{_("Create a New Model")}}</a>
					</span>
				</p>
				<p>
					<span class="welcome_item">
						<a href="{{rootPath}}models-top"
							title='{{_("Open and modify an existing model")}}'>{{_("Open and Modify a Model")}}</a>
					</span>
				</p>
				<p>
					<span class="welcome_item">
						<a href="{{rootPath}}results-top"
							title='{{_("View and compare results for models that have already been run")}}'>{{_("View and Compare Results")}}</a>
					</span>
				</p>
				<p>
					<span class="welcome_item">
						<a href="#"
							title='{{_("View and modify vaccine, population, vehicle and storage device databases")}}'>{{_("View and Modify Databases")}}</a>
					</span>
				</p>
				<p>
					<span class="welcome_item">
						<a href="{{rootPath}}tutorial" target=_blank
							title='{{_("Demonstration of the HERMES platform")}}'>{{_("HERMES Demo")}}</a>
					</span>
				</p>
			</div>
			<div id="dev_page_hidden"><span class="hrm_invisible"><a id="toggle_dev_mode" href="#">Toggle Dev Mode</a></span></div>
		</div>
	</div>
</div>
<!--- STB Recreating this from the models_top form to give the functionality here too.-->
<div id="model_create_dialog_form" title='{{_("Create a New Model")}}'>
	<form>
		<fieldset>
			<table>
				<tr>
					<td><span title='{{_("The name of the model is entered here and can be anything you would like (e.g. the name of a country, state, province, etc...).")}}'>
						{{_('Please provide a name for the the new model.')}}</span></td>
					<td>
						<input type="text" name="model_create_dlg_new_name" 
							id="model_create_dlg_new_name" class="text ui-widget-content ui-corner-all" />
					</td>
				</tr>
			</table>
		</fieldset>
	</form>
</div>

<div id="model_confirm_delete" title='{{_("Delete Model")}}'>
</div>

<div id="model_create_existing_dialog" title='{{_("Model Creation Started")}}'>

<p>{{_('You have already started creating this model, would you like to continue or start over?')}}; </div>

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
	
	$("#create_model_link").click(function(e){
		e.preventDefault();
		$("#model_create_dialog_form").dialog('open');
	});
	
	$("#toggle_dev_mode").click(function() {
	    $.getJSON("{{rootPath}}json/toggle-devel-mode",{})
        .done(function(json) { console.log("developer mode toggled"); })
        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
        location.reload();
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

function deleteModel(modelId, modelName) {
    var msg = '{{_("Really delete the model ")}}' + modelName + " ( " + modelId + " ) ?";
    $("#model_confirm_delete").html(msg);
    $("#model_confirm_delete").data('modelId', modelId);
    $("#model_confirm_delete").dialog("open");
}
</script>
<!--<div class="art-postcontent art-postcontent-0 clearfix">
  <div class="art-content-layout">
	<div class="art-content-layout-row">
	  <div class="art-layout-cell layout-item-0" style="width: 33%" >
	    <p style="text-align: center; font-size: 16px; font-weight: bold; color: #FB8B13;"><span style="color: #303269;">{{_('Vision')}}</span></p>
	    <p style="text-align: center;"><img width="166" height="127" alt="" class="art-lightbox" src="static/images/tmpF14D.png"><br></p>
	    <p style="text-align: center;"><a href="http://hermes.psc.edu/vision.html" class="art-button">{{_('Read more')}}</a></p>
	  </div>
	  <div class="art-layout-cell layout-item-0" style="width: 34%" >
        <p style="text-align: center; font-size: 16px; font-weight: bold; color: #1864C9;"><span style="color: #303269;">{{_('Team')}}</span></p>
        <p style="text-align: center;"><img width="185" height="63" alt="" class="art-lightbox" src="static/images/HERMESTeam.png" style="margin-top: 38px; margin-bottom: 39px;"><br></p>
        <p style="text-align: center;"><a href="http://hermes.psc.edu/team.html" class="art-button">{{_('Read more')}}</a></p>
      </div>
      <div class="art-layout-cell layout-item-0" style="width: 33%" >
	    <p style="font-size: 16px; font-weight: bold; text-align: center; color: #878787;"><span style="color: #303269;">{{_('Publications')}}</span></p>
	    <p style="text-align: center;"><img width="180" height="124" alt="" class="art-lightbox" src="static/images/Benin_ZS_Rota_Util_sm.jpg"><br></p>
	    <p style="text-align: center;"><a href="http://hermes.psc.edu/publications.html" class="art-button">{{_('Read more')}}</a></p>
	  </div>
    </div>
  </div>
  <div class="art-content-layout">
    <div class="art-content-layout-row">
	  <div class="art-layout-cell layout-item-1" style="width: 100%" >
	    <h3><span style="vertical-align: sub; color: #303269;">{{_('A Computational Tool to Design, Plan and Improve Supply Chains')}}</span></h3>
	    <p>{{_('Supply chains are the series of steps involved in transporting vaccines from manufacturers all the way to patients.&nbsp; Distributing vaccines (and other health care products) can be a complex process, integrating many steps, locations, personnel, and equipment.&nbsp; HERMES (Highly Extensible Resource for Modeling Supply-chains) is a computational framework for modeling and optimizing supply chains.')}}</p>
	    <p style="text-align: center;">{{_('The HERMES Project is a collaboration involving...')}}<br></p>
	    <p style="text-align: center;"><img width="79" height="79" alt="" class="art-lightbox" src="static/images/pitt_bluegold_seal1.gif">&nbsp; &nbsp;&nbsp;<img width="211" height="79" alt="" class="art-lightbox" src="static/images/PSClogo_secondary.png"><br></p>
	    <p style="text-align: center;">{{_('Funded through grants from the Bill and Melinda Gates Foundation and the National Institutes of Health.')}}</p>
	  </div>
    </div>
  </div>
</div>-->
