/*
*/

/* Type Explorer Grid Widget 
 * 
 *   Description: This widget can be used for any type in hermes to create a jqGrid that can be used to display types, edit types, or create new ones
 *   
 */
typeInfos = {
			'vaccines': {
				'url':'json/manage-vaccine-explorer',
				'labels': ["{{_('Manufacturer')}}","{{_('Presentation')}}"],//,"{{_('Volume Per Dose (cc)')}}","{{_('Doses Per Vial')}}"],
				'models': [
				           {name:'manufacturer',index:'manufacturer',width:100},
				           {name:'presentation',index:'presentation',width:150},
				           //{name:'volume',index:'volume',formatter:'number',formatoptions:{decimalPlaces:2}},
				           //{name:'dosespervial',index:'dosespervial',formatter:'integer'}
				           ],
				'title':"{{_('Vaccine Type Explorer')}}",
				'searchTitle':"{{_('Search for Vaccines')}}",
				'createTitle':"{{_('Create a New Vaccine')}}",
				'eg':"BCG",
				'groupByType':true
			},
			'trucks': {
				'url':'json/manage-truck-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('Transport Type Explorer')}}",
				'searchTitle':"{{_('Search for Transportation Modes')}}",
				'createTitle':"{{_('Create a New Transportation Mode')}}",
				'eg':'Motorcycle',
				'groupByType':true
			},
			'fridges': {
				'url':'json/manage-fridge-explorer',
				'labels':["{{_('Model')}}","{{_('Energy Type')}}"],
				'models':[
					{name:'model',index:'model',width:200},
					{name:'energy',index:'energy',width:200}
				],
				'title':"{{_('Storage Device Type Explorer')}}",
				'searchTitle':"{{_('Search for Storage Device')}}",
				'createTitle':"{{_('Create a New Storage Device')}}",
				'eg':'RCW25',
				'groupByType':true
			},
			'people':{
				'url':'json/manage-people-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('People Type Explorer')}}",
				'searchTitle':"{{_('Search for People Types')}}",
				'createTitle':"{{_('Create a New People Type')}}",
				'eg':'Newborn',
				'groupByType':false
			},
			'staff':{
				'url':'json/manage-staff-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('Staff Type Explorer')}}",
				'searchTitle':"{{_('Search through Staff')}}",
				'createTitle':"{{_('Create a New Staff Type')}}",
				'eg':'EPI Manager',
				'groupByType':false
			},
			'perdiems':{
				'url':'json/manage-perdiems-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('Perdiem Type Explorer')}}",
				'searchTitle':"{{_('Search through Perdiems')}}",
				'createTitle':"{{_('Create a New Perdiem Rule')}}",
				'eg':'By Day',
				'groupByType':false
			}
			
};

function infoButtonFormatter(cellvalue, options, rowObject){
	var typeName = rowObject.id.replace(".","PeRiOd");
	return "<div class='hermes_info_button_div' id='" +options.gid + "_" + typeName+ "_info_button_div'></div>";
};

function deleteInfoButtonFormatter(cellvalue, options, rowObject){
	var typeName = rowObject.id.replace(".","PeRiOd");
	return "<div class='hermes_info_del_button_container' id='" + options.gid + "_" + typeName+ "_button_container'>" + 
		   "<div class='hermes_info_button_div' id='" +options.gid + "_" + typeName + "_info_button_div'></div>" + 
		   "<div class='hermes_del_button_div' id='" + options.gid + "_" + typeName + "_del_button_div'>" +
		   		"<button class='hermes_del_buttons' id ='"+ options.gid + "_" + typeName + "_del_button'>{{_('Delete')}}</button></div></div>" 
}

function checkBoxFieldFormatter(cellvalue, options, rowObject){
	//var nom = rowObject.id
	var typeName = rowObject.id.replace(".","PeRiOd");
	return "<input type='checkbox' class='hermes_type_explorer_checkbox' id='"+ options.gid + "_" + typeName + "_checkbox'>";
}

;(function($){
	$.widget("typeWidgets.typeExplorerGrid",{
		options:{
			modelId:'',
			typeClass:'',
			height: 300,
			selectEnabled:true,
			checkBoxes: true,
			expandAll: false,
			groupingEnabled: true,
			createEnabled: true,
			createDialogTitle: '',
			namesOnly: false,
			searchEnabled: true,
			width:400,
			min_width:400,
			max_width:1000,
			height:400,
			deletable: false,
			colorNewRows:true,
			includeCount:false,
			newRowColor:"grey",
			forLevelOnly:"",
			excludeTypesFromModel:-1,
			newOnly:false,
			addFunction: function(){},
			delFunction: function(){},
			createFunction: function(){},
			onSelectFunction: function(){},
			title: "",
			trant:{
				title: "{{_('Type Explore Grid')}}"
			}
		},
		getSelectedElements:function(){
			// this will always return an array of values to stay consistent, even if the behavior is not checkboxes.
			thisTableId = $(this.element).attr('id') + "_tbl";
			if(this.options['checkBoxes']){
				var selectedRows = []
				$("#"+thisTableId+" .hermes_type_explorer_checkbox:checked").each(function(){
					console.log("this ID = "+ this.id);
					selectedRows.push(this.id.replace(thisTableId + "_","").replace("_checkbox",""));
				});
				return selectedRows
			}
			else{
				return [$("#"+thisTableId).jqGrid('getGridParam','selrow')];
			}
		},
		getNewTypes:function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			
			return $("#"+thisContainerId).data("newTypes");
		},
		getDeviceCounts:function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			console.log("Counts");
			console.log($("#"+thisContainerId).data("deviceCounts"));
			return $("#"+thisContainerId).data("deviceCounts");
		},
		add: function(typesIdsToAdd,srcModelId){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			
			var modelId = this.options.modelId;
			var typeClass = this.options.typeClass;
			var thisOptions = this.options;
			
			$.ajax({
				url:{{rootPath}} + 'json/copyMultipleTypesToModel',
				data: {modelId:modelId, 
					   srcModelId: srcModelId, 
					   typeNamesArray: JSON.stringify(typesIdsToAdd),
					   ignoreExists:true}
			})
			.done(function(results){
				if(results.success){
					//var news = $("#"+thisContainerId).data("newTypes");
					//news.push(typeName);
					//console.log("adding = " + typeName )
					//$("#"+thisContainerId).data("newTypes",news);
					//console.log("Typ = "+ i + " " + typesIdsToAdd.length);
					
					var news = $("#"+thisContainerId).data("newTypes");
					news = news.concat(typesIdsToAdd);
					$("#"+thisContainerId).data("newTypes",news);
					
					console.log("newsHere = " + $("#"+thisContainerId).data("newTypes",news));
					$("#" + thisTableId).jqGrid("setGridParam",{postData:{
																		modelId:thisOptions.modelId,
																		excludeTypesFromModel:thisOptions.excludeTypesFromModel,
																		forLevelOnly:thisOptions.forLevelOnly,
																		newTypesOnly:thisOptions.newOnly,
																		newTypes:JSON.stringify(news),
																		deviceCounts:JSON.stringify($("#"+thisContainerId).data("deviceCounts"))}
					}).trigger("reloadGrid",{fromServer: true});
						
					if(thisOptions.includeCount){
						counts = $("#"+thisContainerId).data("deviceCounts");
						for(var i=0;i<news.length;i++){
							counts[news[i]] = 1;
						}
						$("#"+thisContainerId).data("deviceCounts",counts);
					}
					thisOptions.addFunction(typesIdsToAdd);
				}
				else{
					alert("{{_('typeExplorerGrid: add success fail in adding type')}}" + results.msg);
				}
			})
			.fail(function(jqxfr, textStatus, error){
 				alert("{{_('typeExplorerGrid:add fail event in adding type')}}");
			});
		},
		removeGrid: function(typesToDel){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			console.log("Grid Rem = " + typesToDel);
			for(typ in typesToDel){
				$("#"+thisTableId).jqGrid("delRowData",typesToDel[typ]);
			}
			$("#"+thisTableId).jqGrid().trigger("reloadGrid");
		},
		remove: function(typesIdsToDel){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			var deleteConfirmDialogId = thisContainerId + "_del_confirm_dialog";
			
			var modelId = this.options.modelId;
			var typeClass = this.options.typeClass;
			var thisOptions = this.options;
			$("#"+deleteConfirmDialogId).html("{{_('Are you sure that you want to delete this type from the model?')}}");
			$("#"+deleteConfirmDialogId).dialog({
				autoOpen:true,
				modal:true,
				position:{my:"center",at: "center", of: window},
				title: "{{_('Confirm Deletion of Types')}}",
				buttons:{
					"{{_('OK')}}": function(){
						$(this).dialog("close");
						for(typ in typesIdsToDel){
							console.log("Deleting = "+ typesIdsToDel[typ]);
							var tName = typesIdsToDel[typ].replace("PeRiOd",".");
							$.ajax({
								url:"{{rootPath}}json/removeTypeFromModel",
								data: {modelId: modelId, typeName: tName},
							})
							.done(function(results){
								if(results.success){
									if(typ == typesIdsToDel.length-1){
										$("#" + thisTableId).trigger("reloadGrid",{fromServer: true});
									}
									thisOptions.delFunction();
								}
								else{
									alert("{{_('typeExplorerGrid: del success fail in deleting type')}}" + results.msg);
								}
							})
							.fail(function(jqxfr, textStatus, error){
								alert("{{_('typeExplorerGrid:del fail event in adding deleting')}}");
							});
						}
					},
					"{{_('Cancel')}}": function(){
						$(this).dialog("close");
					}
				},
				open: function(){
					//$(this).html();
				},
				close: function(){
					$(this).html("");
					$(this).dialog("destroy");
				}
			});
		},
		reloadGrid: function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			
			$("#"+thisTableId).jqGrid().trigger('reloadGrid',{fromServer:true});
		},
		createGrid: function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			var thisPagerId = thisContainerId + "_pg";
			
			var thisOptions = this.options;
			
			colInfo = typeInfos[thisOptions.typeClass];
			console.log(typeInfos);
			console.log(this.options.width);
			var colNames = ["ID","RANK"];
			var colModels = [{name:'id',index:'id',key:true,hidden:true,sortable:true,sorttype:'string',sortorder:'asc'},
			                 {name:'rank',index:'rank',hidden:true,sortable:true,sortorder:'asc'}];
			
			
			if (colInfo.groupByType && thisOptions.groupingEnabled){
				colNames = colNames.concat([" ","{{_('Category')}}"]);
				colModels = colModels.concat([{name:'placeholder',index:'placeholder',width:20,label:""},
				                              {name:'type',index:'type',hidden:true, sortable:true,sorttype:'string',sortorder:'asc'}]);
			}

			if (thisOptions.checkBoxes){
				colNames = colNames.concat([" "]);
				colModels = colModels.concat([{name:'selected',index:'selected',width:30,align:'center',formatter:checkBoxFieldFormatter}]);
			}
			
			
			colNames = colNames.concat(["{{_('Name')}}"])     
			colModels = colModels.concat([{name:'name', index:'name',width:200, sortable: true, sorttype:'string', sortorder:'asc', search:true}]);
			
			if(! thisOptions.namesOnly){
				colNames = colNames.concat(colInfo.labels);
				colModels = colModels.concat(colInfo.models);
			}
			
			if (thisOptions.includeCount){
				thisOptions.selectEnabled = true;
				$("#"+thisContainerId).data("deviceCounts",{});
				colNames = colNames.concat(["{{_('Count')}}"])
				colModels = colModels.concat([{name:'count',index:'count',width:50,formatter:'integer',editable:true,defaultValue:'1'}]);
			}
			
			colNames = colNames.concat(["{{_('Info')}}"]);
			if (thisOptions.deletable){
				colModels = colModels.concat([{name:'details',index:'details',width:125,fixed:true,align:'center',formatter:deleteInfoButtonFormatter}]);
			}
			else{
				colModels = colModels.concat([{name:'details',index:'details',align:'center',width:60,fixed:true,formatter:infoButtonFormatter}]);
			}
			
			

			//add blank column for scrollbar
			colNames = colNames.concat([" "]);
			colModels = colModels.concat([{name:'empty1',index:'empty1',width:15,sortable:false,
							   search:false,resizable:false,fixed:true}]);
			
			var gridHeight = thisOptions.height;
			if(thisOptions.searchEnabled){
				gridHeight -= 50;
			}
			//windowHeight = $(window).height()*.45;
			//if(thisOptions.height >)
			console.log("modelid = " + thisOptions.modelId);
			console.log("url = " + colInfo.url);
			
			var title = colInfo.title;
			
			$("#"+thisContainerId).data("newTypes",[]);
			
			console.log(thisOptions.title);
			if(thisOptions.title != ""){
				title = thisOptions.title;
			}
			
			var thisUrl = {{rootPath}} + colInfo.url;
			console.log("For Level Only " + thisOptions.forLevelOnly);
			var thisPostData = {
								modelId:thisOptions.modelId,
								excludeTypesFromModel:thisOptions.excludeTypesFromModel,
								forLevelOnly:thisOptions.forLevelOnly,
								newTypesOnly:thisOptions.newOnly,
								newTypes:"[]",
								deviceCounts:"{}"//JSON.stringify($("#"+thisTableId).typeExplorerGrid("getNewTypes"))
								};
			var thisMtype = 'post';
			var thisDataType = 'json';
			var lastSel;
			$("#"+thisTableId).jqGrid({
				url:thisUrl,
				datatype:thisDataType,
				postData: thisPostData,
				mtype:thisMtype,
				jsonReader: {repeatitems:false},
				colNames: colNames,
				colModel: colModels,
				rowNum: -1,
				caption: title,
				shrinkToFit:true,
				width:thisOptions.width,
				gridview:true,
				autoencode:true,
				loadonce:true,
				height: thisOptions.height-120,
				//maxHeight: thisOptions.height-120,
				pgbuttons:false,
				pginput:false,
				pgtext:false,
				pager:"#"+thisPagerId,
				viewrecords:true,
				sortname:'rank asc type asc id asc',
				multiSort:true,
				sortable:true,
				loadtext:"Gathering Data",
				groupingView: {
					groupField: ['type'],
					groupColumnShow: [false],
					groupText : ['{0} - {1} Types(s)'],
					groupCollapse: function(){
						if(thisOptions.expandAll){
							return false;
						}
						else{
							return true;
						}
					},
					groupOrder: ['asc']
				},
				forceClientSorting: true, // need jqGrid free to implement this.
				search: true,
				loadError: function(xhr,status,error){
					alert("typeExplorerGrid jqGrid:loadError: "+ status);
				},
				beforeSelectRow: function(rowId, e){
					if((! thisOptions.selectEnabled || thisOptions.checkBoxes ) && ! thisOptions.includeCount){
						return false;
					}
					else if(thisOptions.includeCount){
						var oldRowId = $("#"+thisTableId).getGridParam('selrow');
						if(oldRowId && (oldRowId != rowId)){
							$("#"+thisTableId).jqGrid("saveRow",oldRowId);
						}
					}
					return true;
				},
				onSelectRow: function(rowId){
					if(thisOptions.includeCount){
						if(rowId && rowId!==lastSel){
							$("#"+thisTableId).jqGrid("restoreRow",lastSel);
							lastSel=rowId;
						}
						$("#"+thisTableId).jqGrid("editRow",rowId,{
							keys:true,
							aftersavefunc:function(rowId,response){
								var typeName = $("#"+thisTableId).jqGrid("getCell",rowId,'id');
								var count = $("#"+thisTableId).jqGrid("getCell",rowId,'count');
								
								var counts = $("#"+thisContainerId).data("deviceCounts");
								console.log("HERE");
								console.log(count);
								console.log(counts);
								counts[typeName] = count;
								console.log(counts);
								$("#"+thisContainerId).data("deviceCounts",counts);
							}
						});
					}
					thisOptions.onSelectFunction();
				},
				beforeProcessing: function(data,status,xhr){
					if(!data.success){
						alert("typeExplorerGrid jqGrid:FailError: "+ data.msg);
					}
				},
				gridComplete: function(){
					console.log("News = " + $("#" + thisContainerId).data("newTypes"));
					
					if(!thisOptions.groupingEnabled){
						$("#" + thisTableId).jqGrid('setGridParam',{'grouping': false}).trigger('reloadGrid');
					}
					else{
						$("#" + thisTableId).jqGrid('setGridParam',{'grouping': true}).trigger('reloadGrid');
					}
					
					$("#" + thisTableId + " .hermes_info_button_div").each(function(){
						$this = $(this);
						var typeNameHere = $this.attr("id").replace("_info_button_div","").replace(thisTableId + "_","");
						if(typeNameHere == "Std_VC_BK1.7CF"){
							console.log("HERE VC" + typeNameHere);
						}
						$this.hrmWidget({
							widget:'typeInfoButtonAndDialog',
							modelId: thisOptions.modelId,
							typeId: typeNameHere,
							typeClass: thisOptions.typeClass,
							autoOpen: false
						});
						
					});
					
					if(thisOptions.deletable){
						$("#" + thisTableId + " .hermes_del_buttons").each(function(){
							$this = $(this);
							//console.log($(this));
							var typeNameHere = $this.attr("id").replace("_del_button","").replace(thisTableId + "_","");
							var delButton = $this.button();
							delButton.click(function(e){
								e.preventDefault();
								$("#"+thisContainerId).typeExplorerGrid("remove",[typeNameHere]);
							});
						});
					}
					
				}
				
			});
		},
		_create:function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			var thisPagerId = thisContainerId + "_pg";
			var thisBottomButtonContainerId  = thisContainerId + "_bottom_button_div";
			var thisSearchId = thisContainerId + "_srch";
			var thisSearchButDivId = thisContainerId + "_div_sb";
			var thisSearchButtonId = thisContainerId + "_sb";
			var thisSearchInputId = thisSearchId + "_input";
			var thisSearchTextId = thisSearchId + "_text";
			var showAllResultsButtonId = thisSearchId + "_all_but";
			var deleteConfirmDialogId = thisContainerId + "_del_confirm_dialog";
			var thisCreateButtonId = thisContainerId + "_create_but";
			var thisCreateDialogId = thisContainerId + "_create_dialog";
			
			var thisOptions = this.options;
			
			$("#"+thisContainerId).addClass("hermes_type_explorer_grid_main_div");
			//Add the necessary HTML
			htmlString = "<table id = '" + thisTableId + "' class='hermes_type_explorer_grid_table'></table>";
			htmlString += "<div id = '" + thisPagerId + "' class='hermes_type_explorer_grid_pager'></div>";
			htmlString += "<div id = '" + thisBottomButtonContainerId + "' class='hermes_type_explorer_grid_bottom_button_div'></div>";
			
			if(thisOptions.deletable) {
				htmlString += "<div id='" + deleteConfirmDialogId + "' class='hermes_type_explorer_grid_delconf'></div>";
			}
			
			$("#"+thisContainerId).html(htmlString);
			$("#" + thisContainerId).css("min-height",thisOptions.height + "px");
			$("#" + thisContainerId).css("min-width",thisOptions.min_width + "px");
			$("#" + thisContainerId).css("max-height",thisOptions.height + "px");
			$("#" + thisContainerId).css("max-width",thisOptions.max_width + "px");
			bbHtmlString = "";
			
			if(thisOptions.createEnabled){
				bbHtmlString += "<div class='hermes_type_explorer_bb_div'>";
				bbHtmlString += "<div id = '" + thisCreateButtonId + "' class='hermes_type_explorer_grid_cb'>{{_('Create a New Type')}}</div>";
				bbHtmlString += "</div>";
				$("#"+thisContainerId).append("<div id='" + thisCreateDialogId + "'></div>");
			}
			
			if(thisOptions.searchEnabled){
				bbHtmlString += "<div id = '" + thisSearchId + "' class='hermes_type_explorer_grid_search'></div>";
				//
				bbHtmlString += "<div class='hermes_type_explorer_bb_div'>";
				//bbHtmlString += "<div id = '" + thisSearchButDivId + "' class='hermes_type_explorer_grid_sb_div'>";
				bbHtmlString += "<button id = '" + thisSearchButtonId + "' class='hermes_type_explorer_grid_sb'>{{_('Search')}}</button>";
				bbHtmlString += "</div>";
				bbHtmlString += "<div class='hermes_type_explorer_bb_div'>";
				bbHtmlString += "<button id = '" + showAllResultsButtonId + "' class='hermes_type_explorer_grid_sb'>{{_('Show All Items')}}</button>";
				bbHtmlString += "</div>";
				bbHtmlString += "<div class='hermes_type_explorer_bb_div'>";
				bbHtmlString += "<div id = '" + thisSearchTextId + "' class='hermes_type_explorer_grid_st'></div>";
				bbHtmlString += "</div>";
			}
				
			$("#" + thisBottomButtonContainerId).html(bbHtmlString);
			//htmlString += "<div id = '" + loadingDiv + "' class='hermes_
			
			var modelId = this.options.modelId;
			if(modelId == ''){
				alert("{{_('typeExplorerGrid Widget: No modelId specified as an option.')}}");
			}
			
			var typeClass = thisOptions.typeClass;
			if(! (typeClass in typeInfos)){
				alert("{{_('typeExplorerGrid Widget: Unsupported typeClass: ')}}" + typeClass + ".");
			}
			
			this.createGrid();
			$("#"+thisTableId).jqGrid('sortGrid','type',true);
			$("#"+thisTableId).jqGrid().trigger("reloadGrid");
			
			typeInfo = typeInfos[typeClass];
			
			
			// Set up create capability
			
			if(thisOptions.createEnabled){
				var but = $("#"+thisCreateButtonId).button();
				but.click(function(){
					$("#"+ thisCreateDialogId).typeEditorDialog({
						modelId: thisOptions.modelId,
						typeClass: thisOptions.typeClass,
					        title: thisOptions.createDialogTitle,	
						saveFunc: function(newName){
							var news = $("#"+thisContainerId).data("newTypes");
							news = news.concat([newName]);
							$("#"+thisContainerId).data("newTypes",news);
							if(thisOptions.includeCount){
								var curDevCount = $("#"+thisContainerId).data("deviceCounts");
								curDevCount[newName] = 1;
								$("#"+thisContainerId).data("deviceCounts",curDevCount);

							}

							$("#"+thisTableId).jqGrid('setGridParam',
							{
								postData:{
									modelId:thisOptions.modelId,
									excludeTypesFromModel:thisOptions.excludeTypesFromModel,
									forLevelOnly:thisOptions.forLevelOnly,
									newTypesOnly:thisOptions.newOnly,
									newTypes:JSON.stringify(news),
									deviceCounts:JSON.stringify($("#"+thisContainerId).data("deviceCounts"))
								}
							}).trigger('reloadGrid',{fromServer:true});

							thisOptions.createFunction(newName);
							
						}
					});
				});
			}
			// Set up search capability
			if(thisOptions.searchEnabled){
				var but = $("#" + thisSearchButtonId).button();
				var resButt = $("#"+ showAllResultsButtonId).button();
				
				resButt.hide();
				
				sHtmlString = "<table>";
				sHtmlString += "<tr><td>{{_('Please enter your search words?(e.g. ')}}"+ typeInfo.eg + "):</td></tr>";
				sHtmlString += "<tr><td><input id = '" + thisSearchInputId + 
								"' class='hermes_type_explorer_grid_search_input' "+
								"style='width:250px;'></td></tr>";
				sHtmlString += "</table>";
				
				 
				$("#"+thisSearchId).html(sHtmlString);
				$("#"+thisSearchId).dialog({
					autoOpen: false,
					modal: true,
					width: "auto",
					title: typeInfo.searchTitle,
					buttons: {
						{{_('Search')}}: function(){
							$(this).dialog("close");
							//console.log("Searching for: " + $("#"+ thisSearchInputId).val());
							//$(".loading").text("Filtering...");
							$(".hermes_type_explorer_grid_main_div").children('.ui-jqgrid').children('.loading').css({'padding-left':"55px"});
							$("#"+thisTableId).jqGrid("setGridParam",{loadtext:'Filtering'});
							$("#"+thisTableId).jqGrid("setGridParam", {
								postData: {
									modelId: thisOptions.modelId,
									searchterm: $("#"+thisSearchInputId).val(),
									deviceCounts: JSON.stringify($("#"+thisContainerId).data("deviceCounts"))
								}
							}).trigger("reloadGrid", { fromServer: true});
							$("#"+showAllResultsButtonId).show();
							$("#"+thisSearchTextId).html("Showing Results for term: '" + $("#"+thisSearchInputId).val() + "'");
						},
						{{_('Cancel')}}: function(){
							$(this).dialog("close");
						}
					},
					open: function(e,ui) {
						$("#"+thisSearchInputId).val("");
					    $(this)[0].onkeypress = function(e) {
							if (e.keyCode == $.ui.keyCode.ENTER) {
							    e.preventDefault();
							    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
							}
					    };
					}
				});
				
				but.click( function (){
					$("#"+thisSearchId).dialog("open");
				});
				
				resButt.click( function(){
					$("#"+thisTableId).jqGrid("setGridParam",{loadtext:'Clearing Search'});
					$("#"+thisTableId).jqGrid("setGridParam", {
						postData: {
							modelId: thisOptions.modelId,
							searchterm: "",
							deviceCounts:JSON.stringify($("#"+thisContainerId).data("deviceCounts"))
						}
					}).trigger("reloadGrid", { fromServer: true});
					$("#"+thisSearchTextId).html("");
					resButt.hide();
				});
			}
		},
		_destroy:function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			
			$("#thisContainerId").html("");
		}
	});
})(jQuery);
