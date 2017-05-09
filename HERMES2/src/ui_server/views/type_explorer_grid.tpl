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
typeInfos = {
			'vaccines': {
				'url':'json/manage-vaccine-explorer',
				'labels': ["{{_('Manufacturer')}}","{{_('Presentation')}}"],//,"{{_('Volume Per Dose (cc)')}}","{{_('Doses Per Vial')}}"],
				'models': [
				           {name:'manufacturer',index:'manufacturer',width:300},
				           {name:'presentation',index:'presentation',width:250},
				           //{name:'volume',index:'volume',formatter:'number',formatoptions:{decimalPlaces:2}},
				           //{name:'dosespervial',index:'dosespervial',formatter:'integer'}
				           ],
				'title':"{{_('Vaccine Type Explorer')}}",
				'searchTitle':"{{_('Search for Vaccines')}}",
				'eg':"BCG",
				'groupByType':true
			},
			'trucks': {
				'url':'json/manage-truck-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('Transport Type Explorer')}}",
				'searchTitle':"{{_('Search for Transportation Modes')}}",
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
				'eg':'RCW25',
				'groupByType':true
			},
			'people':{
				'url':'json/manage-people-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('People Type Explorer')}}",
				'searchTitle':"{{_('Search for People Types')}}",
				'eg':'Newborn',
				'groupByType':false
			},
			'staff':{
				'url':'json/manage-staff-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('Staff Type Explorer')}}",
				'searchTitle':"{{_('Search through Staff')}}",
				'eg':'EPI Manager',
				'groupByType':false
			},
			'perdiems':{
				'url':'json/manage-perdiems-explorer',
				'labels':[],
				'models':[],
				'title':"{{_('Perdiem Type Explorer')}}",
				'searchTitle':"{{_('Search through Perdiems')}}",
				'eg':'By Day',
				'groupByType':false
			}
			
};

function infoButtonFormatter(cellvalue, options, rowObject){
	return "<div class='hermes_info_button_div' id='"+cellvalue+"_button_div'></div>";
};

function checkBoxFieldFormatter(cellvalue, options, rowObject){
	var nom = rowObject.id
	return "<input type='checkbox' class='hermes_type_explorer_checkbox' id='"+nom+"_checkbox'>";
}

;(function($){
	$.widget("typeWidgets.typeExplorerGrid",{
		options:{
			modelId:'',
			typeClass:'',
			height: 300,
			selectEnabled:true,
			checkBoxes: true,
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
					console.log(this.id);
					selectedRows.push(this.id.replace("_checkbox",""));
				});
				return selectedRows
			}
			else{
				return [$("#"+thisTableId).jqGrid('getGridParam','selrow')];
			}
		},
		createGrid: function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			var thisPagerId = thisContainerId + "_pb";
			
			var thisOptions = this.options;
			
			colInfo = typeInfos[thisOptions.typeClass];
			console.log(typeInfos);
			
			var colNames = ["ID"];
			var colModels = [{name:'id',index:'id',key:true,hidden:true,sortable:true,sorttype:'string',sortorder:'asc'}];
			
			
			if (colInfo.groupByType){
				colNames = colNames.concat([" ","{{_('Category')}}"]);
				colModels = colModels.concat([{name:'placeholder',index:'placeholder',width:20,label:""},
				                              {name:'type',index:'type',sortable:true,sorttype:'string',sortorder:'asc'}]);
			}

			if (thisOptions.checkBoxes){
				colNames = colNames.concat(" ");
				colModels = colModels.concat([{name:'selected',index:'selected',width:40,align:'center',formatter:checkBoxFieldFormatter}]);
			}
			
			
			colNames = colNames.concat(["{{_('Name')}}"]).concat(colInfo.labels).concat(["{{_('Info')}}"]);           
			colModels = colModels.concat([{name:'name', index:'name',width:300, sortable: true, sorttype:'string', sortorder:'asc', search:true}])
			                 .concat(colInfo.models).concat([{name:'details',index:'details',align:'center',width:100,formatter:infoButtonFormatter}]);
			

			var gridHeight = thisOptions.height;
			//windowHeight = $(window).height()*.45;
			//if(thisOptions.height >)
			console.log("modelid = " + thisOptions.modelId);
			console.log("url = " + colInfo.url);
			$("#"+thisTableId).jqGrid({
				url:{{rootPath}} + colInfo.url,
				datatype:'json',
				postData: {
					modelId:thisOptions.modelId,
				},
				mtype:'post',
				jsonReader: {repeatitems:false},
				colNames: colNames,
				colModel: colModels,
				rowNum: -1,
				caption: colInfo.title,
				gridview:true,
				autoencode:true,
				loadonce:true,
				height: gridHeight,
				pgbuttons:false,
				pginput:false,
				pgtext:false,
				pager:"#"+thisPagerId,
				viewrecords:true,
				sortname:'type asc id asc',
				multiSort:true,
				sortable:true,
				grouping:colInfo.groupByType,
				loadtext:"Gathering Data",
				groupingView: {
					groupField: ['type'],
					groupColumnShow: [false],
					groupText : ['{0} - {1} Types(s)'],
					groupCollapse: true,
					groupOrder: ['asc']
				},
				forceClientSorting: true, // need jqGrid free to implement this.
				search: true,
				loadError: function(xhr,status,error){
					alert("typeExplorerGrid jqGrid:loadError: "+ status);
				},
				beforeSelectRow: function(rowId, e){
					if(! thisOptions.selectEnabled || thisOptions.checkBoxes){
						return false;
					}
				},
				beforeProcessing: function(data,status,xhr){
					if(!data.success){
						alert("typeExplorerGrid jqGrid:FailError: "+ data.msg);
					}
				},
				gridComplete: function(){
					$(".hermes_info_button_div").each(function(){
						$this = $(this);
						$this.hrmWidget({
							widget:'typeInfoButtonAndDialog',
							modelId: thisOptions.modelId,
							typeId: $this.attr("id").replace("_button_div",""),
							typeClass: thisOptions.typeClass,
							autoOpen: false
						});
						
					});
				}
				
			});
		},
		_create:function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			var thisPagerId = thisContainerId + "_pg";
			var thisSearchId = thisContainerId + "_srch";
			var thisSearchButDivId = thisContainerId + "_div_sb";
			var thisSearchButtonId = thisContainerId + "_sb";
			var thisSearchInputId = thisSearchId + "_input";
			var thisSearchTextId = thisSearchId + "_text";
			var showAllResultsButtonId;
			
			var thisOptions = this.options;
			
			$("#"+thisContainerId).addClass("hermes_type_explorer_grid_main_div");
			//Add the necessary HTML
			htmlString = "<table id = '" + thisTableId + "' class='hermes_type_explorer_grid_table'></table>";
			htmlString += "<div id = '" + thisPagerId + "' class='hermes_type_explorer_grid_pager'></div>";
			htmlString += "<div id = '" + thisSearchId + "' class='hermes_type_explorer_grid_search'></div>";
			htmlString += "<div id = '" + thisSearchButDivId + "' class='hermes_type_explorer_grid_sb_div'>";
			htmlString += "<button id = '" + thisSearchButtonId + "' class='hermes_type_explorer_grid_sb'>{{_('Search')}}</button>";
			htmlString += "<button id = '" + showAllResultsButtonId + "' class='hermes_type_explorer_grid_sb'>{{_('Show All Items')}}</button>";
			htmlString += "<div id = '" + thisSearchTextId + "' class='hermes_type_explorer_grid_st'></div>";
			//htmlString += "<div id = '" + loadingDiv + "' class='hermes_
			$("#"+thisContainerId).html(htmlString);
			
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
			// Set up search capability
			
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
								searchterm: $("#"+thisSearchInputId).val()
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
						searchterm: ""
					}
				}).trigger("reloadGrid", { fromServer: true});
				$("#"+thisSearchTextId).html("");
				resButt.hide();
			});
		}
	});
})(jQuery);