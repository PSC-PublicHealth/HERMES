/*
*/

;(function($){
	$.widget("modelWidgets.copyModelDialog",{
		options:{
			modelId:'',
			name:'',
			resultUrl:null,
			title: "",
			text:"",
			autoOpen: false,
			initCopyName:"",
			trant:{
				title: "{{_('Make a copy of model')}}"
			}
		},
		open:function(){
			this.containerId = $(this.element).attr('id');	
			var thisContainerId = this.containerId;
			
			$("#"+thisContainerId).dialog("open");
		},
		_destroy:function(){
			this.containerId = $(this.element).attr('id');	
			var thisContainerId = this.containerId;
			$("#"+thisContainerId).dialog("destroy");
		},
		_create: function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			
			var thisContainerId = this.containerId;
			var orgModelInputId = thisContainerId + "_org_input";
			var newModelInputId = thisContainerId + "_new_input";
		
			var thisOptions = this.options;
			
			htmlString = "<div class='hermes_flex_dialog_row1'><div class='hermes_flex_dialog_col12'>" + thisOptions.text + "<br><hr></div></div>";
			htmlString += "<div class='hermes_flex_dialog_main'>";
			htmlString += "<div class='hermes_flex_dialog_row2'><div class='hermes_flex_dialog_col1'>{{_('Model To Copy')}}</div>";
			htmlString += "<div class='hermes_flex_dialog_col2' id='" + orgModelInputId + "'>" + thisOptions.name + "</div>";
			htmlString += "</div>";
			
			htmlString += "<div class='hermes_flex_dialog_row3'><div class='hermes_flex_dialog_col1'>{{_('Name of the Copied Model')}}</div>";
			htmlString += "<div class='hermes_flex_dialog_col2'><input style='width:300px;' type='text' name='" + newModelInputId + "' id='" + newModelInputId + "' class='ext ui-widget-content ui-corner-all' value='"+ thisOptions.initCopyName + "'/></div>";
			htmlString += "</div></div>";
			
			$("#"+thisContainerId).html(htmlString);
			
			$("#"+thisContainerId).dialog({
		    	resizable: false,
		      	modal: true,
		      	width:"auto",
		      	autoOpen:thisOptions.autoOpen,
		      	title:thisOptions.title,
		     	buttons: {
		     		'{{_("Save")}}': function() {
						var srcModelId = thisOptions.modelId;
						var dstName = $("#"+newModelInputId).val();
						if (dstName == "") {
						    alert('{{_("Please provide a name for the new model to proceed.")}}');
						}
						else {
						    $.ajax({
						    	url:'{{rootPath}}json/get-existing-model-names'
						    })
						    .done(function(result){
						    	if(!result.success){
						    		alert("{{_('Failure in Coping Model dialog getting existing model names: ')}}" + result.msg);
						    	}
						    	else{
						    		if(result.names.indexOf(dstName) !== -1){
						    			alert(dstName +": " + "{{_('This model name already exists. Please select another')}}");
						    			$("#"+newModelInputId).focus().select();
						    		}
						    		else{
						    			$("#"+thisContainerId).dialog("close");
									    $.ajax({
									    	url:'{{rootPath}}json/copy-model',
									    	data: {srcModelId:srcModelId,dstName:dstName}
									    })
										.done(function(results) {
										    if (results.success) {
										    	if(thisOptions.resultUrl){
										    		window.location = thisOptions.resultUrl + "_experiment?modelId="+results.value;
										    	}
										    }
										    else {
										    	alert('{{_("Model Copy Success Failed: ")}}'+data.msg);
										    }
										})
							  			.fail(function(jqxhr, textStatus, error) {
							  			    alert("{{_('Model Copy Failed')}}: "+jqxhr.responseText);
										});
						    		}
						    	}
						    });
						}
		     		}, //Save
				    '{{_("Cancel")}}': function() {
				    	$(this).dialog( "close" );
				    }
		     	}, //buttons
				open: function(e,ui) {
				    $(this)[0].onkeypress = function(e) {
						if (e.keyCode == $.ui.keyCode.ENTER) {
						    e.preventDefault();
						    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
						}
				    };
				}
			});
		} // _create
	});
})(jQuery);
