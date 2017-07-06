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

;(function($){

	$.widget("modelEdit.storeInvGrid",{
		options:{
			rootPath:'',
			modelId:'',
			trant:{
				title:"Store Inventory Grid Editor"
			}
		},
		createGrid:function(){
			
			function editInventoryButtonFormatter(cellvalue, options,rowObject){
				//cellvalue will be an integer
				return "<div class='hermes_button_single' id='"+escape(cellvalue)+"'/>";
			};
			
			function storageInventoryGridFormatter(cellvalue,options,rowObject){
				//console.log('cellvalue = '+cellvalue);
				return "<div class='hermes_storage_inv_grid' id = 'hermes_store_inv_grid_" + escape(cellvalue) +"'/>";
			};
			
			this.containerID = $(this.element).attr('id');
			var thiscontainerID = this.containerID;
			var thisTableID = thiscontainerID + "_tbl";
			var thisPagerID = thiscontainerID + "_pager";
			
			var thisoptions = this.options;
			var rootPath = this.options.rootPath;
			
			var colNames = ["idcode",
			                "Location Name",
			                "Supply Chain Level",			
			                "Inventory",
			                ]
			
			var colModels = [
			                 {name:'idcode',index:'idcode',key:true, editiable:false, hidden:true},
			                 {name:'name',index:'name',editable:false},
			                 {name:'level',index:'level',editable:false},
			                 {name:'inventory', index:'inventory',editable:false,classes:'hermes_store_inv_grid_cell',
			                	 cellLayout:0,width:250,formatter:storageInventoryGridFormatter},
			                 //{name:'editinv', index:'editinv',width:100,formatter:editInventoryButtonFormatter}
			                 
			                 //{name:'latitude',index:'latitude',editable:true, edittype:'text',editrules:'number'},
			                 //{name:'longitude',index:'longitude',editable:true, edittype:'text',editrules:'number'},
			                // {name:'oldlatitude',index:'oldlatitude',hidden:true,editable:false, edittype:'text',editrules:'number'},
			                // {name:'oldlatitude',index:'oldlongitude',hidden:true,editable:false, edittype:'text',editrules:'number'},
			                 
			                ]
			
			
			var gridHeight = 300;
			var windowHeight = $(window).height()*.45;
			//console.log(windowHeight);
			//console.log(gridHeight);
			if(windowHeight < gridHeight){
				console.log("good");
			}
			else{
				gridHeight = windowHeight;
			}
			//console.log("gridHeight: " + gridHeight);
			$('#'+ thisTableID).jqGrid({
				url:rootPath + "json/manage-store-inventory-grid",
				datatype:'json',
				postData: {modelId:thisoptions.modelId},
				inlineData: {modelId:thisoptions.modelId},
				jsonReader: {repeatitems:false},
				colNames: colNames,
				colModel: colModels,
				gridview: true,
				loadonce:true,
				height:gridHeight,
				autowidth:true,
				width:'auto',
				rowNum:-1,
				pgbuttons:false,
				pginput:false,
				pgtext:false,
				pager:"#"+thisPagerID,
				viewrecords:false,
				//editurl:rootPath + 'edit/verify-edit-grid',
//				beforeSelectRow: function(rowId, evt) {
//					var $this = $(this);
//					var oldRowId = $this.getGridParam('selrow');
//					if(oldRowId && (oldRowId != rowId)) {
//						$this.jqGrid("saveRow",oldRowId,
//									{extraparam: {modelId:thisoptions.modelId}}
//						);
//					}
//					return true;
//				},
//				onSelectRow: function(resultsId, status){
//					if(status){
//						if(resultsId) {
//							$("#"+thisTableID).jqGrid('editRow',resultsId,
//									{
//										keys:true,
//										extraparam: {modelId:thisoptions.modelId},
//										aftersavefunc: function(rowId,response){
//											$("#"+thisTableID).jqGrid("resetSelection");
//										},
//										afterstorefunc: function(rowId,response){
//											alert("here");$("#"+thisTableID).jqGrid("resetSelection");
//										},
//										afterrestorefunc: function(rowId,response){$("#"+thisTableID).jqGrid("resetSelection");}
//									}
//							);
//							lastsel=resultsId;
//						}
//						else {
//							alert('outside click '+ resultsId);
//						}
//					}
//				},
				gridComplete: function(){
					var $this = $(this);
//					$this.keypress( function(event) {
//						if(event.which == 13) { //user hits enter
//							var oldRowId = $this.getGridParam('selrow');
//							$this.jqGrid('saveRow',oldRowId,
//									{extraparam: {modelId:thisoptions.modelId}}
//							);
//							lastsel=oldRowId;
//							$("#"+thisTableID).jqGrid("resetSelection");
//						}
//					});
					
					
					$('.hermes_storage_inv_grid').each(function(){
						//console.log($(this).attr('id'));
						storeId = $(this).attr('id').replace('hermes_store_inv_grid_','');
						$(this).hrmWidget({
							widget:'simpleStorageDeviceTable',
							modelId:  thisoptions.modelId,
							storeId:  storeId,
							showHead: false,
							showGrid: false,
							onSelectOpen:function(){
								console.log(thiscontainerID);
								$("#"+thiscontainerID).children(".ui-jqgrid").children(".ui-jqgrid-view").children(".ui-jqgrid-bdiv").css({"overflow":"hidden"});
							},
							onSelectClose:function(){
								$("#"+thiscontainerID).children(".ui-jqgrid").children(".ui-jqgrid-view").children(".ui-jqgrid-bdiv").css({"overflow":"scroll"});
							}
						
						
						});
					});
					
					//$(".hermes_store_inv_grid_cell").css('cssText','padding-top: 0px !important;');
				
					
//						hrmWidget({
//					}
//						widget:'simpleStorageDeviceTable',
//						modelId:  thisoptions.modelId,
//						storeId:  100000,
//						showHead: false,
//						showGrid: false
//						
//					});
				},
				loadError: function(xhr,status,error){
			    	alert('"Error: "'+status);
				},
				beforeProcessing: function(data,status,xhr) {
					if (!data.success) {
			        	alert("Failed2: "+data.msg);
					}
				},
				
				
			})		
		},
		reloadGrid:function(){
			this.containerID = $(this.element).attr('id');
			var thisTableID = this.containerID + "_tbl";
			$("#"+thisTableID).jqGrid("GridUnload");
			this.createGrid();
			
		},
		_create:function(){
			trant = this.options.trant;
			this.containerID = $(this.element).attr('id');
			var thiscontainerID = this.containerID;
			var thisTableID = thiscontainerID + "_tbl";
			var thisPagerID = thiscontainerID + "_pager";
			
			$("#"+thiscontainerID).append("<table id='" + thisTableID + "' class='hermes_storage_inventory_grid_table'></table>");
			$("#"+thiscontainerID).append("<div id='" + thisPagerID+ "'></div>");
			
			var thisoptions = this.options;
			var rootPath = this.options.rootPath;
			
			if(rootPath == ''){
				alert('Cannot use popDemandGrid without a rootPath');
				return;
			}
			
			var modelId = this.options.modelId;
			if(modelId == ''){
				alert('Cannot use popDemandGrid without a modelId');
			}
			
			this.createGrid();
		},	
			
			
	});
})(jQuery);