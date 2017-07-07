/*
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
*/

/* Type Explorer Grid Widget 
 * 
 *   Description: This widget can be used for any type in hermes to create a jqGrid that can be used to display types, edit types, or create new ones
 *   
 */
 
var typesMap = {
	'trucks' : { 'dispName' : 'Transport', 
	               'infoUrl'  : '/bottle_hermes/json/truck-info',  
	               'editUrl'  : '/bottle_hermes/truck-edit',
	               'commitUrl': '/bottle_hermes/json/truck-edit-verify-commit',
	               'editFormUrl': '/bottle_hermes/json/truck-edit-form',
	               'editHeader':'Edit Your Transport Type',
	               'createHeader':'Creating Your Transport Type'
	             },
	'people' : { 'dispName' : 'Population', 
	               'infoUrl'  : '/bottle_hermes/json/people-info',  
	               'editUrl'  : '/bottle_hermes/people-edit',
	               'commitUrl': '/bottle_hermes/json/people-edit-verify-commit',
	               'editFormUrl': '/bottle_hermes/json/people-edit-form',
	               'editHeader':'Edit Your Population Type',
	               'createHeader':'Creating Your Population Type'
	             },
	'vaccines' : { 'dispName' : 'Vaccine', 
	               'infoUrl'  : '/bottle_hermes/json/vaccine-info',  
	               'editUrl'  : '/bottle_hermes/vaccine-edit',
	               'commitUrl': '/bottle_hermes/json/vaccine-edit-verify-commit',
	               'editFormUrl': '/bottle_hermes/json/vaccine-edit-form',
	               'editHeader':'Edit Your Vaccine Type',
	               'createHeader':'Creating Your Vaccine Type'
	             },
	'fridges' : { 'dispName' : 'Storage', 
	               'infoUrl'  : '/bottle_hermes/json/fridge-info',  
	               'editUrl'  : '/bottle_hermes/fridge-edit',
	               'commitUrl': '/bottle_hermes/json/fridge-edit-verify-commit',
	               'editFormUrl': '/bottle_hermes/json/fridge-edit-form',
	               'editHeader':'Edit Your Cold Storage Type',
	               'createHeader':'Creating Your Cold Storage Type'
	             },
	'perdiems' : { 'dispName' : 'PerDiems', 
	               'infoUrl'  : '/bottle_hermes/json/perdiem-info',  
	               'editUrl'  : '/bottle_hermes/perdiem-edit',
	               'commitUrl': '/bottle_hermes/json/perdiem-edit-verify-commit',
	               'editFormUrl': '/bottle_hermes/json/perdiem-edit-form',
	               'editHeader':'Edit Your PerDiem Type',
	               'createHeader':'Creating Your PerDiem Type'
	             },
	'staff' : { 'dispName' : 'Staff', 
	               'infoUrl'  : '/bottle_hermes/json/staff-info',  
	               'editUrl'  : '/bottle_hermes/staff-edit',
	               'commitUrl': '/bottle_hermes/json/staff-edit-verify-commit',
	               'editFormUrl': '/bottle_hermes/json/staff-edit-form',
	               'editHeader':'Edit Your Staff Type',
	               'createHeader':'Creating Your Staff Type'
	                 },
};

;(function($){
	$.widget("typeWidgets.typeEditorDialog",{
		options:{
			modelId:'',
			typeClass:'',
			height: 300,
			width:700,
<<<<<<< HEAD
			saveFunc:function(newName){},
=======
			saveFunc:function(){},
>>>>>>> Added a typeEditorDialog Widget that provides a popup for creating new types.  It is not working for existing types yet, and specification in years breaks it on saves.
			title:'',
			trant:{
				title: "{{_('Type Explore Grid')}}"
			}
		},
		open:function(){
			this.containerId = $(this.element).attr('id');
			
			// So the div that the widget is derived from will be the main dialog
			// and then the other dialogs will be added to the body
			var thisContainerId = this.containerId;
		},
		_create:function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			// So the div that the widget is derived from will be the main dialog
			// and then the other dialogs will be added to the body
			var thisContainerId = this.containerId;
			var thisMainDialogId = thisContainerId + "_main_dialog";
			var thisOptions = this.options;
			
			var thisEditFormId = thisContainerId + "_edit_form_content";
			var thisSaveNameModalId = thisContainerId + "_save_name_modal";
			var thisSaveNameExistsModalId = thisContainerId + "_save_name_exists_modal";
			var thisReqModal = thisContainerId + "_req_modal";
			
			var thisNewTypeDBName = thisSaveNameModalId + "_new_type_dbname_text";
			var thisNewTypeName = thisSaveNameModalId + "_new_type_name_text";
			var SNhtmlString = "<div id='" + thisSaveNameModalId + "'>";
			
			SNhtmlString += "<form><fieldset><table><tr><td>";
			SNhtmlString += "{{_('What would you like to name your new type?')}}";
			SNhtmlString += "</td></tr><tr><td>";
			SNhtmlString += "<input type='hidden' name='"+ thisNewTypeDBName + "'";
			SNhtmlString += "id='"+ thisNewTypeDBName + "' />";
			SNhtmlString += "<input type='text' name='" + thisNewTypeName +"'";
			SNhtmlString += "id='" + thisNewTypeName +"' style='width:100%'";
			SNhtmlString += "class='text ui-widget-content ui-corner-all' />";
			SNhtmlString += "</td></tr></table></fieldset></form>";
			
			var SNEhtmlString = "<div id='" + thisSaveNameExistsModalId + "'>{{_('Notifications')}}</div>";
			var RMhtmlString = "<div id='" + thisReqModal + "'>{{_('There are required entries that have invalid values, please correct the fields that are highlighted in red.')}}</div>"
			
			htmlString = "<div id='"+thisMainDialogId+"' class='type_editor_dialog_dialog'>" +
					"<div id='"+ thisEditFormId +"' class='type_editor_dialog_editform'></div></div>" + 
					SNhtmlString + SNEhtmlString + RMhtmlString;
			$("#"+thisContainerId).addClass('hermes_type_editor_dialog_widget_main');
			$("#"+thisContainerId).html(htmlString);
			
			//$("#"+thisContainerId).append("<div id='" + thisEditFormId + "'></div>");
			//').append(SNhtmlString);
			//$('body').append(SNEhtmlString);
			//('body').append(RMhtmlString);
			
			//Set up the Required Warning Modal
			$("#" + thisReqModal).dialog({
				autoOpen:false, 
				height:"auto", 
				width:"auto", 
				modal:true,
				buttons:{
					'{{_("OK")}}':function(){
						$(this).dialog("close");
					}
				}
			});
			
			// Set up the Save Name Modal
			$("#" + thisSaveNameModalId).dialog({
				autoOpen:false,
				height: 300,
				width: 400,
				modal: true,
				open: function(e,ui) {
				    $(this)[0].onkeypress = function(e) {
				    	if (e.keyCode == $.ui.keyCode.ENTER) {
				    		e.preventDefault();
				    		$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
				    	}
				    };
			    },
			    buttons:{
					'{{_("Save")}}':function(){
						doesTypeExistInModel($("#"+ thisNewTypeDBName).val(),$("#"+thisNewTypeName).val())
						.done(function(result){
							if(result.success){
								if(result.exists){
									if (result.which == 'type'){
										var textString = "The " + typesMap[thisOptions.typeClass].dispName + " type " + $("#"+ thisNewTypeDBName).val() 
														+ " you shouldn't see this.";
									}
									else{
										var textString = "{{_('The ')}}" + typesMap[thisOptions.typeClass].dispName + "{{_(' type ')}}" + $("#" + thisNewTypeName).val() 
											+ "{{_(' already exists in this Model, please provide a new name.')}}";
									} // if result.which == type
									$("#"+thisSaveNameExistsModalId).text(textString);
									$("#"+thisSaveNameExistsModalId).dialog("open");
								} // if result.exists
								else{
									// Test if the new type name is blank
									if(!$("#"+ thisNewTypeDBName).val()){
										var textString = '{{_("The new type name cannot be left blank.")}}';
										$("#"+thisSaveNameExistsModalId).text(textString);
										$("#"+thisSaveNameExistsModalId).dialog("open");
									}
									else {
										$("#"+thisSaveNameExistsModalId).dialog("close");
										/* Need to figure out what to do here */
										//var dict = $("#" + thisEditFormId).editFormManager('getEntries');
										//dict['Name'] = $("#"+ thisNewTypeDBName).val();
										//dict['DisplayName'] = $("#" + + thisNewTypeDBName).val();
										$.ajax({
				    						url:typesMap[thisOptions.typeClass].commitUrl,
				    						data:dict,
				    					})
				    					.done(function(result){
				    						if(result.success && (result.value == undefined || result.value)) {
				    							$("#" + thisSaveNameModalId).dialog("close");
				    							$("#" + thisContainerId).dialog("close");
				    							thisOptions.saveFunc();
				    						}
				    						else{
				    							alert(result.msg);
				    						}
				    					}); 
									} // if not new_type_name_text
								}// else results.exists
							} // if results.success
							else{
								alert("{{_('Save Name Dialog: problem with getting existing names");
							}
						}) // done results ajax
						fail(function(jqxhr, textStatus, error) {
							alert("Error: "+jqxhr.responseText);
						});
					}, // end Save Button
					'{{_("Cancel")}}':function(){
						$(this).dialog("close");
					} // end Cancel Button
				}
			}); // Save Name Modal Dialog
	
		// Now we get to the meat of it all
		
		editNewType();
		
		function editNewType(){
			// get a new type number
			var new_inc = 0;
			$.ajax({
				url:'{{rootPath}}json/get-new-type-number',
				data:{
					'modelId':thisOptions.modelId,
					'type':thisOptions.typeClass
					}
				})
				.done(function(result){
					if(result.success){
						new_inc = result.inc;
						var modelId = thisOptions.modelId;
						var name = "model_"+modelId+"_"+thisOptions.typeClass+"_"+new_inc;
						$.ajax({
							url:typesMap[thisOptions.typeClass].editFormUrl,
							data:{
								'modelId':modelId,
								'protoname':'new_type',
								'newname':name
							}
						})
						.done(function(data){
							console.log(data);
							$("#"+thisMainDialogId).dialog({
								autoOpen:true,
								modal:true,
								//height: thisOptions.height,
								width:thisOptions.width,
				    			title:typesMap[thisOptions.typeClass].editHeader,
				    			close:function(){
				    				//$("#"+thisEditFormId).html('');
				    				$("#"+thisContainerId).typeEditorDialog("destroy");
				    			},
				    			create:function(){
				    				$("#" + thisEditFormId).hrmWidget({
						    			widget:'editFormManager',
						    			html:data['htmlstring'],
						    			modelId:thisOptions.modelId
						    		});
				    			},
				    			buttons:{
				    				'{{_("Cancel")}}':function(){
				    					$(this).dialog("close");
				    				},
				    				'{{_("Save")}}':function(){
				    					var flag = validate_fields();
				    					if(!flag){
					    					var dict = $('#' + thisEditFormId).editFormManager('getEntries');
					    					dict['overwrite'] = 1;
					    					$.ajax({
					    						url:typesMap[thisOptions.typeClass].commitUrl,
					    						data:dict,
					    					})
					    					.done(function(result){
					    						if(result.success && (result.value == undefined || result.value)) {
					    							$("#"+thisMainDialogId).dialog("close");
<<<<<<< HEAD
					    							thisOptions.saveFunc(name);
=======
					    							thisOptions.saveFunc();
>>>>>>> Added a typeEditorDialog Widget that provides a popup for creating new types.  It is not working for existing types yet, and specification in years breaks it on saves.
					    						}
					    						else{
					    							alert(result.msg);
					    						}
					    					}); 
					    				}
				    					else{
				    						$("#" + thisReqModal).dialog("open");
				    					}
				    				}
				    			}
				    		});
						})
						.fail(function(jqxhr, textStatus, error) {
							alert("Error: "+jqxhr.responseText);
						});
						//$("#"+thisCreateDialogId).dialog("open");
					}
					else{
						alert('{{_("There was a problem getting the new increment for the new type name")}}');
					}
				})
				.fail(function(jqxhr, textStatus, error) {
					alert("Error: "+jqxhr.responseText);
				});
		}
		
		function editExisting(){
			upId = unpackId(id); 
			var modelId = upId.modelId;
			var name = upId.name; 
			var grid = upId.grid;
		    $.ajax({
		    	url:typesMap[thisOptions.typeClass].editFormUrl,
		    	data:{
		    		'modelId':modelId,
		    		'protoname':name,
		    		'newname':'None',
		    		'overwrite':1,
		    		'backUrl':B64.encode(myURL + "&startClass=" + thisOptions.typeClass)
		    	}
		    })
		    .done(function(data){
		    	if(data.success){
		    		$("#" + thisEditFormId).hrmWidget({
		    			widget:'editFormManager',
		    			html:data['htmlstring'],
		    			modelId:modelId
		    		});
		    		$("#" + thisContainerId).dialog({
		    			title:typesMap[thisOptions.typeClass].editHeader,
		    			buttons:{
		    				'{{_("Cancel")}}':function(){
		    					$(this).dialog("close");
		    				},
		    				'{{_("Save")}}':function(){
		    					var dict = $('#' + thisEditFormId).editFormManager('getEntries');
		    					dict['overwrite'] = 1;
		    					$.ajax({
		    						url:typesMap[thisOptions.typeClass].commitUrl,
		    						data:dict,
		    					})
		    					.done(function(result){
		    						if(result.success && (result.value == undefined || result.value)) {
		    							$("#" + thisContainerId).dialog("close");
		    							thisOptions.saveFun();
		    						}
		    						else{
		    							alert(result.msg);
		    						}
		    					}); 
		    				},
		    				'{{_("Save As New Component")}}':function(){
		    					var dict = $('#'+thisEditFormId).editFormManager('getEntries');
		    					$.ajax({
		    						url:'{{rootPath}}json/get-all-typenames-in-model',
		    						data:{
		    							'modelId':thisOptions.modelId
		    						}
		    					})
		    					.done(function(result){
		    						if(result.success){
		    							count=0;
		    							typename = dict['Name'];
		    							while(result.typenames.indexOf(typename)!=-1){
		    								typename = typename.slice(0,typename.length-1)+count;
		    								count++;
		    							}
		    							$("#" + thisNewTypeDBName).val(typename);
		    	    					$("#" + + thisNewTypeDBName).val(dict['DisplayName'] + " (modified)");
		    	    					
		    	    					$("#"+ thisModelNameModalId).dialog("open");
		    						}
		    						else{
		    							alert(result.msg);
		    						}
		    					})
		    					.fail(function(jqxhr, textStatus, error) {
		    						alert("Error: "+jqxhr.responseText);
		    					});
		    					
		    				}
		    			}
		    		});
		    		$("#" + thisContainerId).dialog("open");
		 
		    	}
		    	else{
		    		alert('{{_("Failed11: ")}}'+data.msg);
			    }  
			})
			.fail(function(jqxhr, textStatus, error) {
			    alert("Error: "+jqxhr.responseText);
			});
		}
		// helper functions
		function doesTypeExistInModel(typename,displayname){
			return $.ajax({
				url:'{{rootPath}}json/check-if-type-exists-for-model',
				data:{
					'modelId':thisOptions.modelId,
					'typename':typename,
					'displayname':displayname
				}
			}).promise();
		};
		
		function validate_fields(){
			var flag = false;
			var debug = false;
			$(".required_string_input").each(function(){
				var value = $(this).val();
				if(!value || value.length === 0 || !value.trim()){
					$(this).css("border-color","red");
					if(debug) alert("String Bad " + $(this).attr('id'))
					flag=true;
				}
			});
			$(".required_int_input").each(function(){
				var value = $(this).val();
				if(!value || value.length === 0 || !value.trim()){
					$(this).css("border-color","red");
					if(debug) alert("int Bad " + $(this).attr('id'))
					flag=true;
				}
				if($(this).hasClass("canzero")){
					if(value < 0.0){
						$(this).css("border-color","red");
						flag=true;
						if(debug) alert("int zero Bad " + $(this).attr('id'))
					}
				}
				else{
					if(value <= 0.0){
						$(this).css("border-color","red");
						flag=true;
						if(debug) alert("int eq zero Bad " + $(this).attr('id'))
					}
				}
			});
			$(".required_float_input").each(function(){
				var value = $(this).val();
				//alert("could be zero");}
				if(!value || value.length === 0 || !value.trim() || isNaN(parseFloat(value))){
					$(this).css("border-color","red");
					if(debug) alert("float Bad " + $(this).attr('id') + "Value = " + value)
					flag=true;
				}
				if($(this).hasClass("canzero")){
					if(value < 0.0){
						$(this).css("border-color","red");
						if(debug) alert("float zero Bad " + $(this).attr('id'))
						flag=true;
					}
				}
				else{
					if(value <= 0.0){
						$(this).css("border-color","red");
						if(debug) alert("float eq zero Bad " + $(this).attr('id'))
						flag=true;
					}
				}
			});
			return flag;
		}

	
		}, // end _create
		_destroy:function(){
			this.containerId = $(this.element).attr('id');
			
			// So the div that the widget is derived from will be the main dialog
			// and then the other dialogs will be added to the body
			var thisContainerId = this.containerId;
			var thisMainDialogId = thisContainerId + "_main_dialog";
			var thisOptions = this.options;
			
			var thisEditFormId = thisContainerId + "_edit_form_content";
			var thisSaveNameModalId = thisContainerId + "_save_name_modal";
			var thisSaveNameExistsModalId = thisContainerId + "_save_name_exists_modal";
			var thisReqModal = thisContainerId + "_req_modal";
			
			$("#"+thisReqModal).dialog("destroy");
			if($("#"+ thisSaveNameExistsModalId).hasClass('ui-dialog')){
				$("#"+thisSaveNameExistsModalId).dialog("destroy");
			}
			$("#"+thisSaveNameModalId).dialog("destroy");
			$("#"+thisMainDialogId).dialog("destroy");
			$("#"+thisContainerId).html("");
			//var thisNewTypeDBName = thisSaveNameModalId + "_new_type_dbname_text";
			//var thisNewTypeName = thisSaveNameModalId + "_new_type_name_text";
			//var SNhtmlString = "<div id='" + thisSaveNameModalId + "'>";
		}
	});
})(jQuery);
		
