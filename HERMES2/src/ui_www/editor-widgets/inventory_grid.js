/*
*/
;(function($){

	$.widget("inventory_grid.inventory_grid",{
		options:{
			rootPath:'',
			modelId:'',
			idcode:'',
			invType:'fridges',
			customCols:[],
			loadonce:false,
			unique:2,
			hiddengrid:false,
			editurl:'edit/store-edit-edit',
			tableId:'',
			pagerId:'',
			infoDialogId:'',
			width:800,
			caption:'Test',
			gridUrl:'',
			gridpostdata:'',
			editUrl:'',
			trant:{
				title:"Inventory Grid"
			}
		},
		
		data:function(){
			var l = [];
			var thisGrid = $("#"+this.options.tableId);
			// Force a local save if necessary
			var selrow = thisGrid.jqGrid('getGridParam','selrow');
			if (selrow) thisGrid.jqGrid("saveRow", selrow);
				
			var gridData = thisGrid.jqGrid('getGridParam','data');
			var delData = thisGrid.data('deletedRowList')
			for (var i in gridData) {
				var o = gridData[i];
				// console.log(o);
				var addflag = true;
				for(var j in l){
					if(l[j]['typename']==o['visibletypestring']){
						l[j]['count'] += parseInt(o['count']);
						addflag = false;
					}
				}
				if(addflag){
					l.push( {typename:o['typestring'], visibletypename:o['visibletypestring'],
								count:o['count'], origcount:o['origcount']} );
				}
			};
			if (typeof delData === "object") {
				for (var i in delData) {
					var o = delData[i];
					l.push( {typename:o, visibletypename:o, count:0} ); // fake
																		// a
																		// delete
																		// request
				};
				grid.data('deletedRowList',[]);
			}

			//console.log(l);
			return l;
		},
		hermesStorageString:function(){
			var l = [];
			var thisGrid = $("#"+this.options.tableId);
			// Force a local save if necessary
			var selrow = thisGrid.jqGrid('getGridParam','selrow');
			if (selrow) thisGrid.jqGrid("saveRow", selrow);
				
			var gridData = thisGrid.jqGrid('getGridParam','data');
			var delData = thisGrid.data('deletedRowList')
			var storeString = ''
			for (var i in gridData) {
				var o = gridData[i];
				// console.log(o);
				var count = parseInt(o['count']);
				var typename = o['visibletypestring'];
				if(count <= 1){
					storeString += typename;
				}
				else{
					storeString += count + "*" + typename;
				}
				if(i < gridData.length - 1){
					storeString += "+";
				}
			}
			if (typeof delData === "object") {
				for (var i in delData) {
					var o = delData[i];
					l.push( {typename:o, visibletypename:o, count:0} ); // fake
																		// a
																		// delete
																		// request
				};
				thisGrid.data('deletedRowList',[]);
			}
			return storeString;
		},
		_create:function(){
			trant = this.options.trant;
			
			this.containerID = $(this.element).attr('id');
			var thiscontainerID = this.containerID;
			
			var thisTableID = this.containerID + "_tbl";
			var thisPagerID = this.containerID + "_pager";
			var thisDialogID = this.options.infoDialogId;
			
			this.options.tableId = thisTableID;
			
			var htmlString = "<table id='"+thisTableID+"'></table>"+
							 "<div id='"+thisPagerID+"'></div>";
			
			if(this.options.infoDialogId == ''){
				thisDialogID = this.containerID + "_dialog";
				htmlString += "<div id='"+thisDialogID+"'></div>";
			}
			
			$("#"+thiscontainerID).html(htmlString);
			
			console.log(this.options.infoDialogId == '');
			console.log(this.options.infoDialogId);
			if(this.options.infoDialogId == ''){
				$("#"+thisDialogID).dialog({autoOpen:false, height:"auto", width:"auto"});
			}
			
			
			
			var thisoptions = this.options;
			
			var rootPath = this.options.rootPath;
			if(rootPath == ''){
				alert('Cannot use inventory_grid without a rootPath');
				return;
			}
			var modelId = this.options.modelId;
			if(modelId == ''){
				alert('Cannot use inventory_grid without a modelId');
			}
			var idcode = this.options.idcode;
			var invType = this.options.invType;
			var customCols = this.options.customCols;
			var infoButtonClassName = "hermes_info_button_"+invType+"_"+ Math.floor((Math.random()*1000000) + 1);
			// Will do translate_phrases after this works
			
			// build colNames
			colNamesBeg = [
			            "",
			            "",
			            "Type",
			            "Description"
			            ];
			colNamesEnd = [
			               "Count",
			               "Details"
			               ];
			
			colNamesMiddle = [];
			for (var i =0; i<customCols.length;++i){
				colNamesMiddle.push(customCols[i][0]);
			}
			
			colNames = colNamesBeg.concat(colNamesMiddle,colNamesEnd);
			colModelBeg = [
			               	{name:'typestring', index:'typestring', key:true, editable:false, hidden:true},
			               	{name:'origcount', index:'origcount', editable:false, hidden:true},
			               	{name:'visibletypestring', index:'visibletypestring', width:275, 
			               		editable:true, edittype:'select', 
			               		editoptions:{ 
			               			dataUrl:rootPath + 'list/select-type-full',
			               			dataInit: function(elt) { elt.focus(); },
			               			beforeProcessing:function(data,status,xhr){
			               				// This will populate the row with the
										// information from the
			               				// first option that pops up in the
										// select box.
			               				var grid = $("#"+thisTableID);
			               				var rowId = grid.getGridParam('selrow');
			               				var typestringval = grid.getRowData(rowId).typestring;
			               				console.log("Type String = " + typestringval)
			               				if(typestringval == ''){
											$.getJSON(rootPath+'json/type-dict', {
												modelId:modelId, 
												typestring:$(this).val()
											})
											.done(function(data) {
												if (data.success) {
													console.log("Value = "+data.value["DisplayName"]);
													
													var grid = $("#"+thisTableID);
													var rowId = grid.getGridParam('selrow');
													
													grid.setCell(rowId,"description",data.value["DisplayName"]);
													for(var i = 0;i<customCols.length;++i){
														grid.setCell(rowId,customCols[i][1],data.value[customCols[i][2]]);
													}
													grid.setCell(rowId,"info",data.value["Name"]);
													attachClickEventToInfoButtons();
												}
												else {
													alert('{{_("Failed4: ")}}'+data.msg);
												}
								    		})
											.fail(function(jqxhr, textStatus, error) {
												alert('{{_("Error: ")}}'+jqxhr.responseText);
											});
			               				}
			               			},
							 		dataEvents: [
							 		    // This will reupdate the information
										// when the select box is changed.
							 			{ type: 'change',
							 				fn: function(e) {
												$.getJSON(rootPath+'json/type-dict', {
													modelId:modelId, 
													typestring:$(this).val()
												})
												.done(function(data) {
													if (data.success) {
														var grid = $("#"+thisTableID);
														var rowId = grid.getGridParam('selrow');
														//console.log("change value = " + data.value["DisplayName"]);
														grid.setCell(rowId,"description",data.value["DisplayName"]);
														for(var i = 0;i<customCols.length;++i){
															grid.setCell(rowId,customCols[i][1],data.value[customCols[i][2]]);
														}
														grid.setCell(rowId,"info",data.value["Name"]);
														attachClickEventToInfoButtons();
													}
													else {
														alert('{{_("Failed1: ")}}'+data.msg);
													}
									    		})
												.fail(function(jqxhr, textStatus, error) {
													alert('{{_("Error: ")}}'+jqxhr.responseText);
												});		
							 				}
							 			}
							 		]
							 	}
							 },
							{name:'description', index:'description', width:275, editable:false}
			               ];
			colModelEnd = [
				       		{name:'count', index:'count', sorttype:'int', align:'right', editable:true,
				       		 edittype:'text', editrules:{integer:true}, 
				       		 editoptions:{
				       		 	defaultValue:1,
				       		 	dataEvents: [{
				       		 		type:'keydown',
				       		 		fn: function(e) {
				       		 			var key = e.charCode || e.keyCode;
				       		 			if (key == 9) // tab
				       		 				{
				       		 					$grid = $("#" + thisTableID);
				       		 					var rowId = $grid.jqGrid('getGridParam','selrow');
				       		 					var ids = $grid.jqGrid('getDataIDs');
				       		 					var indexHere = $grid.jqGrid('getInd',rowId) - 1;
				       		 					var newIndex = (indexHere + 1) % ids.length;
				       		 					if (newIndex == indexHere) {
				       		 						e.preventDefault(); // only
																		// one
																		// row,
																		// so do
																		// nothing
				       		 					}
				       		 					else {
				       								$grid.jqGrid("saveRow", rowId, 
				       									{extraparam: { modelId:modelId, idcode:idcode, invtype:invType }});
				       		 						$grid.jqGrid('setSelection',ids[newIndex]);
				       								e.preventDefault();
				       							}
				       		 				}
				       		 		}
				       		 	}]
				       		 }},
				       		{name:'info', index:'info', width:110, align:'center', sortable:false,
				       		 formatter:function(cellvalue, options, rowObject) {
				       		 	if (cellvalue) {
				       				return "<button type='button' class='"+infoButtonClassName+"' id="+escape(cellvalue)+">Info</button>";
				       			}
				       			else {
				       				return "<button type=\"button\" class='"+infoButtonClassName+"'  id=\"_undefined\" disabled>Info</button>";
				       			}
				       		}}
	
				               ];
			
			colModelMiddle = [];
			for(var i=0;i<customCols.length;++i){
				console.log(customCols[i]);
				if(customCols[i][3] == "float"){
					colModelMiddle.push({name:customCols[i][1],index:customCols[i][1],
						editble:false,align:'right',formatter:'number',formatoptions:{decimalPlaces:2}});
				}
				else{
					colModelMiddle.push({name:customCols[i][1],index:customCols[i][1],
						editble:false,align:'right'});
				}
			
			}
			
			colModels = colModelBeg.concat(colModelMiddle,colModelEnd);
			// console.log(colModels);
			
			var editURLHere = "clientArray";
			if(thisoptions.loadonce == false){
				editURLHere = thisoptions.editurl;
			}
			
			$("#"+thisTableID).jqGrid({
				url:thisoptions.gridurl,
				datatype:'json',
				postData: thisoptions.gridpostdata,
				inlineData: thisoptions.gridpostdata,
				ajaxSelectOptions: { 
					data:{
						modelId:modelId, 
						idcode:idcode,
						invtype:invType,
						typestring: function () { 
							var rowId = $("#"+thisTableID).getGridParam('selrow');
							return $("#"+thisTableID).getGridParam('getCell', rowId, 'visibletypestring'); 
						}
					}
				},
				loadonce:thisoptions.loadonce,
				editurl:editURLHere,
				width:thisoptions.width,
				caption:thisoptions.caption,
				footerrow:true,
				colNames:colNames,
				colModel:colModels,
				hiddengrid:thisoptions.hiddengrid,
				pager: '#'+thisPagerID, // set your pager div id
				sortname: 'typestring', // the column according to which data is
										// to be sorted; optional
				sortorder: "asc", // sort order; optional
				viewrecords: false, // if true, displays the total number of
									// records, etc. as: "View X to Y out of
									// Zâ€� optional
				gridview: true, // speeds things up- turn off for treegrid,
								// subgrid, or afterinsertrow
				userDataOnFooter: true,
				beforeSelectRow: function(rowId, evt) {
					var $this = $(this);
					var oldRowId = $this.getGridParam('selrow');
					// console.log("rowId = "+ rowId + " oldRowId = " +
					// oldRowId);
			        if (oldRowId && (oldRowId != rowId)) {
			        	$this.jqGrid("saveRow", oldRowId, 
			        			{
			        				extraparam: { modelId:modelId, idcode:idcode, invtype:invType},
			        				aftersavefunc:function(rowId, response ){
			        					updateColSums();
			        					// $("#"+thisTableID).trigger("reloadGrid");
			        				}
			        			}
			        	);
					}
				    return true;
				},

				onSelectRow: function(resultsid, status){
			   		if (status) {
			   			if (resultsid) {
							jQuery("#"+thisTableID).jqGrid('editRow',resultsid,
									{
										keys:true,
										extraparam: { modelId:modelId, idcode:idcode, invtype:invType },
										aftersavefunc: function( rowId, response ) {
											updateColSums();
											$("#"+thisTableID).jqGrid("resetSelection");
//											
// //$("#"+thisTableID).trigger("reloadGrid"); // to update checkboxes
										},
										afterrestorefunc: function(rowId) {
											updateColSums();
											$("#"+thisTableID).jqGrid("resetSelection");
						    				// $("#"+thisTableID).trigger("reloadGrid");
											// // to update checkboxes
										}
									}
							);
							lastsel=resultsid;
			   			}
					}
					else {
						// alert('outside click '+resultsid);
					}
				},
				gridComplete: function(){
					attachClickEventToInfoButtons();
			   		var $this = $(this);
			    	$this.keypress( function(event) {
			    		if (event.which == 13) { // user hit return
							var oldRowId = $this.getGridParam('selrow');
			        		$this.jqGrid("saveRow", oldRowId, {extraparam: { 
			        														modelId:modelId, 
			        														idcode:idcode, 
			        														invtype:invType, 
			        														},
			        											aftersavefunc:function(rowid, response){
			        												updateColSums();
			        												// $("#"+thisTableID).trigger("reloadGrid");
			        											}
			        										  }
			        		);
							// Manually re-enable add button
							$("#"+thisTableID+"_iladd").removeClass('ui-state-disabled');
							lastsel = oldRowId;
							// console.log("resetting");
							$("#"+thisTableID).jqGrid("resetSelection");
			    		}
			    	});
			      // resize grid to fit dialog
			    	// var gridParentDialog =
					// $(this).parent().parent().parent().parent().parent().parent().parent().parent().parent();
			    	var uaSpecificWidth = 0; // default tested on Firefox
			    	var uaSpecificHeight = 0;
			    	if (navigator.userAgent.match(/webkit/i)) {
				        uaSpecificWidth = 0;   // Webkit specific
				        uaSpecificHeight = 5;
			    	} else if (navigator.userAgent.match(/trident/i) || navigator.userAgent.match(/msie/i)) {
				        uaSpecificWidth = 0;   // IE specific
				        uaSpecificHeight = 8;
			    	}
			    	// gridParentDialog.bind("dialogresize", function () {
				    // $this.jqGrid('setGridWidth',
					// gridParentDialog.width()-uaSpecificWidth-40);
				    // $this.jqGrid('setGridHeight',
					// gridParentDialog.height()-uaSpecificHeight-150);
			    	// });
				},
				loadError: function(xhr,status,error){
			    	alert('{{_("Error: ")}}'+status);
				},
				beforeProcessing: function(data,status,xhr) {
					if (!data.success) {
			        	alert('{{_("Failed2: ")}}'+data.msg);
					}
				},
			});
			
			var urlHere = rootPath+"clientArray";
			if(thisoptions.loadonce == false){
				urlHere = '';
			}
			
			$("#"+thisTableID).jqGrid('navGrid','#'+thisPagerID,
					{
						edit:false,add:false,del:true,save:false,cancel:false,
						delfunc:function(rowId) { 
							if(thisoptions.loadonce){
								var $this = $( this );
								if (typeof $this.data('deletedRowList') === "undefined")
									$this.data( 'deletedRowList', [] );
								$this.data( 'deletedRowList' ).push( rowId );
								$this.jqGrid('delRowData', rowId);
							}
						},
					},
					{}, // edit params
					{
						keys:true,
						afterSubmit:function(response){}
					}, // add params
					{
						delData:{modelId:modelId, idcode:idcode, unique:thisoptions.unique, invtype:invType },		
						url:urlHere
					} 
				);
				$("#"+thisTableID).jqGrid('inlineNav','#'+thisPagerID,
					{edit:false,add:true,del:true,save:false,cancel:false,restoreAfterSelect:false,
					addParams:{
						keys:true,
						position:'last'
					}
				});
				function attachClickEventToInfoButtons(){
					$("."+infoButtonClassName).click(function(event) {
			    		$.getJSON(rootPath+'json/type-info', {
			    			modelId:modelId, 
			    			typestring:unescape($(this).attr('id'))
			    		})
			    		.done(function(data) {
			        		if (data.success) {
			        			// if (data.success) {
			        				// console.log(thisDialogID);
			        				$("#"+thisDialogID).html(data['htmlstring']);
			        				$("#"+thisDialogID).dialog('option','title',data['title']);
			        				$("#"+thisDialogID).dialog("open");
			        			// }
			    				// else {
			        			// alert('{{_("Failed: ")}}'+data.msg);
			    				// }
			        		}
			        		else {
			        			alert('{{_("Failed3: ")}}'+data.msg);
			        		}
			    		})
			    		.fail(function(jqxhr, textStatus, error) {
			    			alert('{{_("Error: ")}}'+jqxhr.responseText);
			    		});
			    		event.stopPropagation();
			    	});
				};
				
				function updateColSums(){
					var countSum = $("#"+thisTableID).jqGrid('getCol','count',false,'sum');
					$("#"+thisTableID).jqGrid('footerData','set',{count:countSum});
					var cusSums = {};
					for(var i=0;i<thisoptions.customCols.length;++i){
						var entryName = thisoptions.customCols[i][1];
						var sum = 0.0;
						var ids = $("#"+thisTableID).jqGrid('getDataIDs');
						for(var j = 0; j < ids.length;++j){
							var rowData = $("#"+thisTableID).jqGrid('getRowData',ids[j]);
							sum += parseFloat(rowData[entryName])*parseFloat(rowData['count']);
						}
						if(! isNaN(sum)){
							var obj = JSON.parse('[{"'+entryName+'":'+parseFloat(sum).toFixed(2) + '}]');
							
							$("#"+thisTableID).jqGrid('footerData','set',obj[0]);
						}
					}
				}

		}
	});		
})(jQuery);
