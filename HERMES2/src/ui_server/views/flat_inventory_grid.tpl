$("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").jqGrid({ //set your grid id
	url:'{{rootPath}}json/store-edit-manage-table',
	datatype: "json",
	postData: {
		modelId:{{modelId}}, idcode:{{idcode}}, unique:{{unique}}, invtype:'{{invtype}}'
	},
	inlineData: {
		modelId:{{modelId}}, idcode:{{idcode}}, unique:{{unique}}, invtype:'{{invtype}}'
	},
	ajaxSelectOptions: { 
		data:{
			modelId:{{modelId}}, 
			idcode:{{idcode}},
			invtype:'{{invtype}}',
			typestring: function () { 
				var rowId = $("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").getGridParam('selrow');
				return $("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").getGridParam('getCell', rowId, 'visibletypestring'); 
			}
		}
	},
	% if defined('loadonce') and loadonce:
	loadonce:true,
	editurl: 'clientArray',
	% else:
	editurl: '{{rootPath}}edit/store-edit-edit',
	% end
	width: 800, //specify width; optional
	caption:"{{caption}}",
	footerrow:true,
	%if defined('hiddengrid') and hiddengrid:
	hiddengrid:true,
	%end
	colNames:[
		"",
		"",
		"{{_('Type')}}",
		"{{_('Description')}}",
		% for a,b,c in customCols:
		  "{{a}}",
		% end
		"{{_('Count')}}",
		"{{_('Details')}}"
	],
	colModel:[
		{name:'typestring', index:'typestring', key:true, editable:false, hidden:true},
		{name:'origcount', indexx:'origcount', editable:false, hidden:true},
		{name:'visibletypestring', index:'visibletypestring', width:275, 
		 	editable:true, edittype:'select', 
		 	editoptions:{ 
		 		dataUrl:'{{rootPath}}list/select-type-full',
		 		dataInit: function(elt) { elt.focus(); },
		 		dataEvents: [
		 			{ type: 'change',
		 				fn: function(e) {
    						$.getJSON('{{rootPath}}json/type-dict', {
    							modelId:{{modelId}}, 
    							typestring:$(this).val()
    						})
    						.done(function(data) {
        						if (data.success) {
        							var grid = $("#store_edit_wgt_{{invtype}}_tbl_{{unique}}")
        							var rowId = grid.getGridParam('selrow');
        							grid.setCell(rowId,"description",data.value["DisplayName"]);
        							% for a,b,c in customCols:
        							grid.setCell(rowId,"{{b}}",data.value["{{c}}"]);
        							%end
        							var infoButton = grid.find("button#"+escape(rowId))[0];
        							if (infoButton) {
        								infoButton.disabled = false;
        								$(infoButton).attr('id',escape(data.value['Name']));
									}
									else {
										infoButton = grid.find("button#_undefined")[0];
										if (infoButton) {
        									infoButton.disabled = false;
        									$(infoButton).attr('id',escape(data.value['Name']));
        								}
									}
        						}
    							else {
        							alert('{{_("Failed: ")}}'+data.msg);
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
		{name:'description', index:'description', width:275, editable:false},
		% for a,b,c in customCols:
		{name:'{{b}}', index:'{{b}}', editable:false, align:'right'},
		%end
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
		 					$grid = $("#store_edit_wgt_{{invtype}}_tbl_{{unique}}");
		 					var rowId = $grid.jqGrid('getGridParam','selrow');
		 					var ids = $grid.jqGrid('getDataIDs');
		 					var indexHere = $grid.jqGrid('getInd',rowId) - 1;
		 					var newIndex = (indexHere + 1) % ids.length;
		 					if (newIndex == indexHere) {
		 						e.preventDefault(); // only one row, so do nothing
		 					}
		 					else {
								$grid.jqGrid("saveRow", rowId, 
									{extraparam: { modelId:{{modelId}}, idcode:{{idcode}}, invtype:'{{invtype}}' }});
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
				return "<button type=\"button\" class=\"hermes_info_button\" id="+escape(cellvalue)+">Info</button>";
			}
			else {
				return "<button type=\"button\" class=\"hermes_info_button\"  id=\"_undefined\" disabled>Info</button>";
			}
		}}
	],
	pager: '#store_edit_wgt_{{invtype}}_tbl_pager_{{unique}}', //set your pager div id
	sortname: 'typestring', //the column according to which data is to be sorted; optional
	sortorder: "asc", //sort order; optional
	viewrecords: false, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
	userDataOnFooter: true,
	beforeSelectRow: function(rowId, evt) {
		var $this = $(this);
		var oldRowId = $this.getGridParam('selrow');
        if (oldRowId && (oldRowId != rowId)) {
        	$this.jqGrid("saveRow", oldRowId, {extraparam: { modelId:{{modelId}}, idcode:{{idcode}}, invtype:'{{invtype}}' }});
		}
        return true;
	},
	onSelectRow: function(resultsid, status){
   		if (status) {
   			if (resultsid) {
				jQuery("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").jqGrid('editRow',resultsid,{
					keys:true,
					extraparam: { modelId:{{modelId}}, idcode:{{idcode}}, invtype:'{{invtype}}' },
					aftersavefunc: function( rowId, response ) {
	    				$("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").trigger("reloadGrid"); // to update checkboxes
					},
					afterrestorefunc: function(rowId) {
	    				$("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").trigger("reloadGrid"); // to update checkboxes
					}
				});
   			}
		}
		else {
			//alert('outside click '+resultsid);
		}
	},
	gridComplete: function(){
   		$(".hermes_info_button").click(function(event) {
    		$.getJSON('{{rootPath}}json/type-info', {
    			modelId:{{modelId}}, 
    			typestring:unescape($(this).attr('id'))
    		})
    		.done(function(data) {
        		if (data.success) {
        			if (data.success) {
        				$("#store_type_info_dialog_{{unique}}").html(data['htmlstring']);
        				$("#store_type_info_dialog_{{unique}}").dialog('option','title',data['title']);
        				$("#store_type_info_dialog_{{unique}}").dialog("open");
        			}
    				else {
        				alert('{{_("Failed: ")}}'+data.msg);
    				}
        		}
        		else {
        			alert('{{_("Failed: ")}}'+data.msg);
        		}
    		})
    		.fail(function(jqxhr, textStatus, error) {
    			alert('{{_("Error: ")}}'+jqxhr.responseText);
    		});
    		event.stopPropagation();
    	});
    	var $this = $(this);
    	$this.keypress( function(event) {
    		if (event.which == 13) { // user hit return
				var oldRowId = $this.getGridParam('selrow');
        		$this.jqGrid("saveRow", oldRowId, {extraparam: { modelId:{{modelId}}, idcode:{{idcode}}, invtype:'{{invtype}}' }});
				// Manually re-enable add button
				$("#store_edit_wgt_{{invtype}}_tbl_{{unique}}_iladd").removeClass('ui-state-disabled');
    		}
    	});
      // resize grid to fit dialog
    	var gridParentDialog = $(this).parent().parent().parent().parent().parent().parent().parent().parent().parent();
    	var uaSpecificWidth = 0; //default tested on Firefox
    	var uaSpecificHeight = 0;
    	if (navigator.userAgent.match(/webkit/i)) {
        uaSpecificWidth = 0;   //Webkit specific
        uaSpecificHeight = 5;
    	} else if (navigator.userAgent.match(/trident/i) || navigator.userAgent.match(/msie/i)) {
        uaSpecificWidth = 0;   //IE specific
        uaSpecificHeight = 8;
    	}
    	gridParentDialog.bind("dialogresize", function () {
        $this.jqGrid('setGridWidth', gridParentDialog.width()-uaSpecificWidth-40);
        $this.jqGrid('setGridHeight', gridParentDialog.height()-uaSpecificHeight-150);
    	});
    },
	loadError: function(xhr,status,error){
    	alert('{{_("Error: ")}}'+status);
	},
	beforeProcessing: function(data,status,xhr) {
		if (!data.success) {
        	alert('{{_("Failed: ")}}'+data.msg);
		}
	},
});	
$("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").jqGrid('navGrid','#store_edit_wgt_{{invtype}}_tbl_pager_{{unique}}',
	{edit:false,add:false,del:true,save:false,cancel:false
	% if defined('loadonce') and loadonce:
	,delfunc:function(rowId) { 
		var $this = $( this );
		if (typeof $this.data('deletedRowList') === "undefined")
			$this.data( 'deletedRowList', [] );
		$this.data( 'deletedRowList' ).push( rowId );
		$this.jqGrid('delRowData', rowId);
	}
	% end
	},
	{}, // edit params
	{keys:true}, // add params
	{delData:{modelId:{{modelId}}, idcode:{{idcode}}, unique:{{unique}}, invtype:'{{invtype}}' }
	% if defined('loadonce') and loadonce:
	,url:"{{rootPath}}clientArray"
	% end
	} // del params
);
$("#store_edit_wgt_{{invtype}}_tbl_{{unique}}").jqGrid('inlineNav','#store_edit_wgt_{{invtype}}_tbl_pager_{{unique}}',
	{edit:false,add:true,del:true,save:false,cancel:false,restoreAfterSelect:false,addParams:{keys:true}
});
