%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs, _=_, inlizer=inlizer

<script src="{{rootPath}}static/uisession.js"></script>
<script>
var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
var modelInfo = ModelInfoFromJson(modJson);
</script>
<style>
.editable{
	text-align:center;
}
.namecol{
	padding-left:40px !important;
}
.jqgroup {
	background:whitesmoke;
}
</style>
<p>
	<span class="hermes-top-main">
		{{_('What Equipment And Population Exist At Each Level?')}}
	</span>
</p>

<p>
	<span class="hermes-top-sub">
		{{_('Now, we need to allocate the equipment for storage and population that will be served for each location at each level.').format(name)}}
		{{_('To add an item to all of the location, edit the cell to indicate the number to be added.  You can modify individual locations by editing the model.')}}
	</span>
</p>
<p>
	<span class="hermes-top-sub">
		{{_('NOTE: The count should be the number you would like at each location in the level (e.g. if you specify 100 Newborns at the Health Post level, each location at that level will be assigned 100 Newborns)"')}}
	</span>
</p>

<table id = "provision_table"></table>
<form>
  	<!--<table id = "provision_levels"></table>-->

    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value="{{_("Previous Screen")}}"></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value="{{_("Next Screen")}}"></td>
      </tr>
    </table>
</form>
<div id="model_store_add_dialog">
 	<div id="model_store_add_div"></div>
</div>


<script>

function itemsInfoButtonFormatter(cellvalue,options,rowObject){
	return "<button type='button' class='hermes_info_button' id="+cellvalue+">"+'{{_("Info")}}'+"</button>";
}

for(var i = 0; i < modelInfo.nlevels; i++){
	var locString = '{{_("For the locations at level: ")}}';
	if(modelInfo.levelcounts[i] == 1)
		locString = '{{_("For the location at level: ")}}';
	
	$('#provision_levels').append("<tr><td>"+locString+"</td><td><div id = 'model_create_prov_b_"+i+"'>"+modelInfo.levelnames[i]+"</div></td></tr>");
}

var selICol;
var selIRow;
var ids;
$.ajax({
	url:'{{rootPath}}json/table-for-store-provision?modelId='+modelInfo['modelId'],
	datatype:'json'
})
.done(function(results){
	if(!results.success){
		alert(results.msg);
	}
	else{
		
		// Build the ColModel and column datastructures outside so they can be dynamic
		var colNames = ['ID',
						'Type',
						"{{_('Name')}}",
						"{{_('Info')}}"
						]
		for (var i = 0; i < results.levels.length;i++){
			colNames.push(results.levels[i]);
		}
		
		var colModel = [
		                {name:'id',index:'id',jsonmap:'id',hidden:true},
		                {name:'type',index:'type',jsonmap:'type',classes:'groupcol'},
		                {name:'name',index:'name',jsonmap:'name',classes:'namecol'},
		                {name:'info',index:'info',align:'center',width:50,formatter:itemsInfoButtonFormatter}
		                ]
		var errFlag = false;
		for (var i=0;i<results.levels.length;i++){
			if (i == results.levels.length -1){
				colModel.push({name:results.levels[i],
							   index:results.levels[i],
							   jsonmap:results.levels[i],
							   align:'center',width:50,
							   editable:true,
							   //edittype:'number'});
							   editoptions:{size:4,
								   dataInit: function(element){
									   $(element).keyup(function(){
										   var val1=element.value;
										   var num = parseInt(val1);
										   if((isNaN(num)) && (val1 != '')){
											   alert("{{_('Please enter an integer')}}");
											   errFlag = true;
										   }
									   });
								   },
								   dataEvents:[
								               {
								            	   type:'keydown',
								            	   fn:function(e){
								            		   var key = e.charCode || e.keyCode;								            	
								            		   if(key == 9){
								            			   thisId = $("#"+ids[ids.indexOf(selRowID)])[0].rowIndex;
								            			   if(errFlag){
								            				   e.preventDefault();
								            				   setTimeout("jQuery('#provision_table').editCell(" + thisId + ",4,true);",100);
								            				   
								            				   errFlag = false;
								            			   }
								            			   else if(ids.indexOf(selRowID) != ids.length-1){
									            			   newId = $("#"+ids[ids.indexOf(selRowID)+1])[0].rowIndex;
									            			   setTimeout("jQuery('#provision_table').editCell(" + newId + ",4,true);",100);
								            			   }
								            			   else{
								            				   e.preventDefault();
								            				   setTimeout("jQuery('#next_button').focus();",100);
								            				   //setTimeout("jQuery('#provision_table').editCell(" + thisId + ",4,true);",100);
								            			   }
								            		   }
								            		   if(key == 13){
														   thisId = $("#"+ids[ids.indexOf(selRowID)])[0].rowIndex;
														   if(errFlag){
								            				   e.preventDefault();
								            				   setTimeout("jQuery('#provision_table').editCell(" + thisId + ",4,true);",100);
								            				   
								            				   errFlag = false;
								            			   }
														   else if(ids.indexOf(selRowID) != ids.length-1){
															   newId = $("#"+ids[ids.indexOf(selRowID)+1])[0].rowIndex;
															   setTimeout("jQuery('#provision_table').editCell(" + newId + ","+selICol+",true);",100);
														   }
														   else{
															   e.preventDefault();
															   setTimeout("jQuery('#next_button').focus();",100);
															   //setTimeout("jQuery('#provision_table').editCell(" + thisId + ",4,true);",100);
														   }
													   }
								            	   }
								               }
								             ]
							   },
							   editrules:{integer:true}});
			}
			else{
				colModel.push({name:results.levels[i],
					   index:results.levels[i],
					   jsonmap:results.levels[i],
					   align:'center',width:50,
					   editable:true,
					   //edittype:'number'});
					   editoptions:{size:4,
						   dataInit: function(element){
							   $(element).keyup(function(){
								   var val1=element.value;
								   var num = parseInt(val1);
								   if((isNaN(num)) && (val1 != '')){
									   alert("{{_('Please enter an integer')}}");
									   errFlag = true;
								   }
							   });
						   },
						   dataEvents:[
						               {
											type:'keydown',
											fn:function(e){
												   var key = e.charCode || e.keyCode;								            	
												   if(key == 13){
													   thisId = $("#"+ids[ids.indexOf(selRowID)])[0].rowIndex;
													   if(errFlag){
							            				   e.preventDefault();
							            				   setTimeout("jQuery('#provision_table').editCell(" + thisId + ",4,true);",100);
							            				   
							            				   errFlag = false;
							            			   }
													   else if(ids.indexOf(selRowID) != ids.length-1){
														   newId = $("#"+ids[ids.indexOf(selRowID)+1])[0].rowIndex;
														   setTimeout("jQuery('#provision_table').editCell(" + newId + ","+selICol+",true);",100);
													   }
													   else{
														   e.preventDefault();
														   setTimeout("jQuery('#next_button').focus();",100);
														   //setTimeout("jQuery('#provision_table').editCell(" + thisId + ",4,true);",100);
													   }
												   }
											}
						               }
						             ]
					   				}
					});
			}
		}
		
		console.log(results.data);
		var lastsel;
		$("#provision_table").jqGrid({
			datastr:results.data,
			datatype:"jsonstring",
			treeGrid:true,
			grouping:true,
			groupingView: {
				groupField:['type'],
				groupColumnShow:[false]
			},
			jsonReader: {
				root:'rows',
				repeatitems: false,
				id:'id'
			},
			width:'auto',
			height:'auto',
			viewrecords:false,
			gridview:false,
			colNames:colNames,
			colModel:colModel,
			ExpandColumn:'type',
			sortname:'id',
			cellEdit:true,
			cellsubmit:'clientArray',
			beforeEditCell: function(rowId, cellname, value, iRow, iCol){
				selICol = iCol;
				selIRow = iRow;
				selRowID = rowId;
			},
			afterEditCell:function(rowId,cellname,value,iRow,iCol){
				$("#" + this.id + " tbody>tr:eq(" + iRow + ")>td:eq(" + iCol + ") input, select, textarea").css("text-align","center");
				$("#" + this.id + " tbody>tr:eq(" + iRow + ")>td:eq(" + iCol + ") input, select, textarea").select();
			},
			afterSaveCell:function(rowId,cellname,value,iRow,iCol){
				if(value > 0){
					$("#" + this.id + " tbody>tr:eq(" + iRow + ")>td:eq(" + iCol +")").css("background","grey");
					$("#" + this.id + " tbody>tr:eq(" + iRow + ")>td:eq(" + iCol +")").css("color","white");
				}
			},
			editurl:'clientArray',
			gridComplete: function(){
				$('.hermes_info_button').click(function(event){
					alert("info goes here");
				});
				ids = $("#provision_table").getDataIDs();
			}
		}).jqGrid('hermify',{debug:true, resizable_hz:true});
		
		
	}
	
});

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/back"
	});
});
	
$(function() {
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		// First Make sure we are editting a cell that can't be editted
		$("#provision_table").editCell(0,0);
		// Now we can get the row data
		rowData = $("#provision_table").jqGrid("getRowData");
		/// clean this a bit
		for(var i = 0; i < rowData.length;i++){
			delete rowData[i].info;
		}
		rowDataJsonString = JSON.stringify(rowData);
		
		data = {
				'modelId':{{modelId}},
				'itemData':rowDataJsonString,
				'reset':true
				};
		$.ajax({
			url:'{{rootPath}}json/provision-stores',
			datatype:'json',
			data:data,
			method:'post'
		})
		.done(function(result){
			if(!result.success){
				alert(result.msg);
			}
			else{
				window.location = "{{rootPath}}model-create/next";
			}
		})
		.fail(function(jqxhr, textStatus, error) {
			alert("Error: " + jqxhr.responseText);
		});	
		
		//console.log(rowDataJsonString);
		
		  // settings already sent via ajax
	});
});



</script>
