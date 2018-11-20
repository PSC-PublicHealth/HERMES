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
	$.widget("typeWidgets.vaccineDosePerPersonGrid",{
		options:{
			modelId:'',
			height: 300,
			width:400,
			deletable: false,
			onSaveFunc: function(){},
			filterList: [],
			title: "",
			trant:{
				title: "{{_('Vaccine Dose Grid')}}"
			}
		},
		resultJson:function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			
			var gridData = $("#"+thisTableId).jqGrid("getRowData");
			return JSON.stringify(gridData);
		},
		validate:function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			
			var gridData = $("#"+thisTableId).jqGrid("getRowData");
			var badEntries = []
			for(var i=0; i<gridData.length;++i){
				var nonZero = false;
				for(var prop in gridData[i]){
					if (prop != "vId" && prop != "vName"){
						if(gridData[i][prop] > 0){
							nonZero = true;
						}
					}
				}
				if (!nonZero){
					badEntries.push(gridData.vId);
				}
			}
			
			if(badEntries.length > 0){
				alert("{{_('All Vaccines need to have at least one dose given.')}}");
				return false;
			}
			return true;
		},
		createGrid:function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			var thisPagerId = thisContainerId + "_pg";
			
			var thisOptions = this.options;
			
			var modelId = this.options.modelId;
			var colNames = ["HEREMSVaccId","{{_('Vaccine')}}"]
			var colModels = [{name:'vId',index:'vId',key:true,hidden:true},
			                 {name:'vName',index:'vName',sortable:true,sorttype:'string',sortorder:'asc'}];
			$.ajax({
				url: '{{rootPath}}json/get-all-typenames-in-model',
				data: {modelId:thisOptions.modelId, typeClass:"people"}
			})
			.done(function(results){
				if(results.success){
					//console.log(results);
					for(p in results.typedisplaynames){
						colNames = colNames.concat([results.typedisplaynames[p]]);
						colModels = colModels.concat([{name:results.typenames[p],index:results.typenames[p],
							editable:true,editrules:{integer:true,minValue:0}}]);
					}
				}
				else{
					alert("{{_('in vaccineDosePerPersonGrid widget: success failed in getting people names: ')}}" + results.msg);
				}
				
				console.log(colNames);
				console.log(colModels);
				$("#"+thisTableId).jqGrid({
					url:{{rootPath}} + "json/get-vaccine-doses-person-table-manager",
					datatype:'json',
					mtype:'post',
					postData:{modelId:modelId,filterList:thisOptions.filterList},
					jsonReader:{repeatitems:false},
					colNames:colNames,
					colModel:colModels,
					loadonce:true,
					height:'auto',
					gridview:true,
					pgbuttons:false,
					pginput:false,
					pgtext:false,
					pager:thisPagerId,
					viewrecords: false,
					editurl:'{{rootPath}}edit/edit-demand',
					beforeSelectRow: function(rowId, evt) {
						var $this = $(this);
						var oldRowId = $this.getGridParam('selrow');
						if(oldRowId && (oldRowId != rowId)) {
							$this.jqGrid("saveRow",oldRowId,
										{extraparam: {modelId:modelId}}
							);
						}
						return true;
					},
					onSelectRow: function(rowId){
						console.log("modelId = " + modelId);
						$("#"+thisTableId).jqGrid('editRow',rowId,{
							keys:true,
							extraparam:{modelId:modelId,vaccine:rowId},
							aftersavefunc:function(rowId,response){
								$("#"+thisTableId).jqGrid('resetSelection');
								thisOptions.onSaveFunc();
							},
							afterrestorrefunc:function(rowId,response){
								$("#"+thisTableId).jqGrid('resetSelection');
							}
						});
					},
					loadError: function(xhr,status,error){
						alert("{{_('in vaccineDosePerPersonGrid widget: loadError in creating table: ')}}" + status);
					},
					beforeProcessing: function(data,status,xhr){
						if (!data.success) {
							alert("{{_('in vaccineDosePerPersonGrid widget: Failed to create data for table: ')}}" + status);
						}
					},
				});
			})
			.fail(function(jqxfr, textStatus, error){
	 			alert("{{_('in vaccineDosePerPersonGrid widget: fail in getting people names: ')}}" + textStatus);
			});
		},
		_create: function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			var thisPagerId = thisContainerId + "_pg";
			
			var thisOptions = this.options;
			
			var class_pre = "hermes_vac_dose_per_person_";
			$("#"+thisContainerId).addClass(class_pre + "main_div");
			
			htmlString = "<table id = '" + thisTableId + "' class='" + class_pre + "_table'></table>";
			htmlString += "<div id = '" + thisPagerId + "' class='" + class_pre + "_pg'></div>";
			
			$("#"+thisContainerId).html(htmlString);
			var modelId = this.options.modelId;
			if(modelId == ''){
				alert("{{_('vaccineDosesPerPersonGrid Widget: No modelId specified as an option.')}}");
			}
			
			this.createGrid();
			//$("#"+thisTableId).jqGrid('sortGrid','vName',true);
			//$("#"+thisTableId).jqGrid().trigger("reloadGrid");			
			
		},
		_destroy:function(){
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var thisTableId = thisContainerId + "_tbl";
			
			$("#"+thisTableId).jqGrid("GridDestroy");
		}
	});
})(jQuery);
