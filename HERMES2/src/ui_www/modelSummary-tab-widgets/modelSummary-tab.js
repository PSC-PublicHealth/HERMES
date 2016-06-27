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

Please make sure that whatever tpl file that you put this widget in has the following includes

*/
;(function($){
	$.widget("modelSummary-tab-widgets.modelSummaryTabs",{
		options:{
			rootPath:'',
			modelId:'',
			modelName:null,
			width:1000,
			height:600,
			mapOn:false,
			diagramOn:false,
			notesOn:true,
			summaryOn:true,
			trant:{
				title:"Model Summary Tab Widget"
			}
		},
		
		_create:function(){
			trant = this.options.trant;
			this.containerID = $(this.element).attr('id');
			var thiscontainerID = this.containerID;
			
			
			var thisoptions = this.options;
			var rootPath = this.options.rootPath;
			
			if(rootPath == ''){
				alert('Cannot use geographicResultsMap without a rootPath');
				return;
			}
			
			var modelId = this.options.modelId;
			if(modelId == ''){
				alert('Cannot use geographicResultsMap without a modelId');
			}
			var modelName = this.options.modelName;
			
			// Make the tab list based on options that are available
			var divIds = {
					'diagramID':thiscontainerID + "_diagram_div",
					'collapseDiagID':thiscontainerID + "_collapsible_network_diagram_div",
					'mapID':thiscontainerID + "_map_div",
					'mapDiagID':thiscontainerID + "_geographic_diagaram_div",
					'noteID':thiscontainerID + "_note_div",
					'noteAreaID':thiscontainerID + "_note_area_div",
					'noteButtonID':thiscontainerID + "_note_submit_div",
					'noteUpdateNotifyID':thiscontainerID + "_note_update_notify_div",
					'summaryID':thiscontainerID + "_summary_div"
			};
			
			var phrases = {
					0:'Model Network',
					1:'Supply Chain Network Diagram',
					2:'This diagram depicts the structure of this supply chain.  Clicking on a location can expand or contract the routes and locations below the selected location. Right-clicking a location or route will bring up more detailed information.',
					3:'Preparing Diagram',
					4:'Model Geography',
					5:'Supply Chain Geographic Map',
					6:'This diagram depicts the geography of this supply  chain.  Cliking on a circle (represents a location) or a line (reprents a route) will give you a dialog with more detailed information about that item.',
					7:'Model Notes',
					8:'Notes',
					9:'Note Updated',
					10:'Save Notes'
			}
			
			translate_phrases(phrases)
				.done(function(results){ //translate_phrases
					var tphrases = results.translated_phrases;
					$("#"+thiscontainerID).append(tabPageHTML(thisoptions,divIds,tphrases));
					$("#"+thiscontainerID).css('width',thisoptions.width);
					$("#"+thiscontainerID).css('height',thisoptions.height);
					$("#"+thiscontainerID).tabs();
					
					var tabHeight = $("li[aria-controls='"+divIds.diagramID+"']").parent().outerHeight();
					
					if(thisoptions.diagramOn){
						//Compute the height of the divs
						//first find that tab divs' height
						var pHeights = 0;
						$(".diagram-height-calc").each(function(index){
							pHeights += $(this).outerHeight(true);
						});
						
						$("#"+divIds.diagramID).outerHeight($("#"+divIds.diagramID).parent().height()-tabHeight);
						
						var svgHeight = $("#"+divIds.diagramID).height()-pHeights;
						var svgWidth = $("#"+divIds.diagramID).width();
						loadNetworkDiagram(svgHeight,svgWidth);
					}; // if diagramOn
					
					if(thisoptions.notesOn){
						$("#"+divIds.noteID).outerWidth($("#"+divIds.noteID).parent().width());
						$("#"+divIds.noteID).outerHeight($("#"+divIds.noteID).parent().height()-tabHeight);
						$("#"+divIds.noteButtonID).outerWidth($("#"+divIds.noteID).width());
						$("#"+divIds.noteButtonID).height(30);
						
						var pHeights = 0;
						$(".note-height-calc").each(function(index){
							pHeights += $(this).outerHeight(true);
						});
						
						$("#"+divIds.noteAreaID).width($("#"+divIds.noteID).width()-5);
						$("#"+divIds.noteAreaID).outerHeight($("#"+divIds.noteID).height()-$("#"+divIds.noteButtonID).outerHeight()-pHeights-20);
						$.ajax({
							url:rootPath+'json/get-model-notes',
							datatype:'json',
							data:{'modelId':modelId},
							method:'post'
						})
						.done(function(results){
							if(!results.success){
								alert(results.msg);
							}
							else{
								$("#"+divIds.noteAreaID).val(results.notes);
							}
						})
						.fail(function(jqxhr, textStatus, error) {
					    	alert("Error: " + jqxhr.responseText);
					    });
						
						$("#"+divIds.noteButtonID).button();
						$("#"+divIds.noteButtonID).click(function(){
							$.ajax({
								url:rootPath+"edit/update-model-name-note",
								method:"post",
								datatype:"json",
								data:{"modelId":modelId,
									  "newName":modelName,
									  "newNote":$("#"+divIds.noteAreaID).val()}
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
					}; // if notesOn
				})
				.fail(function(data){ //translate_phrases
					alert(data);
				});
			
			
			//rootPath,divIds and modelId are in this scope	
			function loadNetworkDiagram(diagHeight,diagWidth){
				$.ajax({
					url:rootPath+'json/model-structure-tree-d3?modelId='+modelId,
					dataType:'json'
				})
				.done(function(result){
					if(!result.success){
						alert(results.msg);
					}
					else{
						$("#"+divIds.collapseDiagID).diagram({
							jsonData:result,
							storeDialogDivID:null,
							rootPath:rootPath,
							modelId:modelId,
							absoluteWidth:diagWidth,
							absoluteHeight:diagHeight,
							//minWidth:490,
							resizeOn:false,
							hideRouteNames:false
						});
					}
				})
				.fail(function(data){ 
					alert(data);
				});
			};
			
			function tabPageHTML(options,containerIDs,tphrases){
				listString = "<ul>";
				divString = "";
				if(options.diagramOn){
					listString += '<li><a href="#'+containerIDs.diagramID+'">'+tphrases[0]+'</a></li>';
					divString += '<div class="model-summary-tab-inner" id="'+containerIDs.diagramID+'">';
					divString += '<p class="diagram-height-calc"><span class="model-diagram-title">'+tphrases[1]+'</span></p>';
					divString += '<p class="diagram-height-calc"><span class="model-diagram-note">'+tphrases[2]+'</span></p>';
					divString += '<div class="model-collapse-diagram-div" id="'+containerIDs.collapseDiagID+'"></div>';
					divString += '</div>';
				}
				if(options.mapOn){
					listString += '<li><a href="#'+containerIDs.mapID+'">'+tphrases[4]+'</a></li>';
					divString += '<div  id="'+containerIDs.mapID+'">';
					divString += '<p><span class="model-diagram-title">'+tphrases[5]+'</span></p>';
					divString += '<p><span class="model-diagram-note">'+tphrases[6]+'</span></p>';
					divString += '<div id="'+containerIDs.mapDiagID+'"></div>';
					divString += '</div>';
				}
				if(options.notesOn){
					listString += '<li><a href="#'+containerIDs.noteID+'">'+tphrases[7]+'</a></li>';
					divString += '<div  id="'+containerIDs.noteID+'">';
					divString += '<p class="note-height-calc"><span class="model-diagram-title">'+tphrases[8]+'</span></p>';
					divString += '<textarea id="'+containerIDs.noteAreaID+'"></textarea>';
					divString += '<p class="note-height-calc"></p>';
					divString += '<div style="width:100%;" id="'+containerIDs.noteButtonID+'">'+tphrases[10]+'</button>';
					divString += '<div id="'+containerIDs.noteUpdateNotifyID+'" style="display:none;"><p>'+tphrases[9]+'</p></div>'
					divString += '</div>';
				}
				listString += "</ul>"
				return listString +" "+divString;
			}// tabPageHTML
		} //_create
	}); //Widget
})(jQuery);