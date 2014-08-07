// Dialog box functions

// Example HTML Code To go with this
//<div id="model_store_info_dialog" title="This should get replaced">
//	<div id = "model_store_info_content">
//		<ul>
//			<li style="font-size:small">
//				<a href='#tab-1'>General Info</a>
//			</li>
//			<li style="font-size:small">
//				<a href='#tab-2'>Population Info</a>
//			</li>
//			<li style="font-size:small">
//				<a href="#tab-3">Storage Devices</a>
//			</li>
//		</ul>
//		<div id='tab-1'><table id='GenInfo'></table></div>
//		<div id='tab-2'><table id='PopInfo'></table></div>
//		<div id='tab-3'><table id='StoreDevInfo'></table></div>
//	</div>
//</div>
function initStoreInfoDialogNoResults(divName){
	$("#"+divName).dialog({
		autoOpen:false, 
		height:"auto", 
		width:"auto",
		close: function() {
			console.log("closing");
			$("#model_store_info_content").tabs();
			$("#model_store_info_content").tabs('destroy');
			$("#model_store_info_content").innerHtml = "";
			$("#GenInfo").jqGrid("GridUnload");
			$("#PopInfo").jqGrid("GridUnload");
			$("#StoreDevInfo").jqGrid("GridUnload");
		}
	});
}
function populateStoreInfoDialogNoResults(rootPath,divName,modId,storId){
	console.log("creating for div "+divName+ " modelID = " + modId + " storeID = " + storId);
	$("#" + divName).tabs();
	$("#GenInfo").jqGrid({
		url:rootPath + 'json/get-general-info-for-store',
			//&modelId='+modId+'&storeId='+storId,
		datatype: 'json',
		mtype:'GET',
		postData:{modelId:modId,storeId:storId},
		jsonReader: {
			repeatitems: false,
			id:"id",
			root:"rows"
		},
		sortable:false,
		captions:"{{_('General Information')}}",
		width: 300,
		height:'auto',
		colNames: ['Feature','Value'],
		colModel : [{
			name : 'feature',
			index : 'feature',
			width : '30%',
			sortable : false
		}, {
			name : 'value',
			id : 'value',
			width : '70%',
			sortable : false
		}],
	});
	$("#GenInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();
	$("#PopInfo").jqGrid({
		url:rootPath + 'json/get-population-listing-for-store',
		postData:{modelId:modId,storeId:storId},
		datatype:'json',
		jsonReader: {
			repeatitems: false,
			id:"id",
			root:"rows"
		},
		height : 'auto',
		width : 300,
		scroll : false,
		scrollOffset : 0,
		colNames : ['Category', 'Count'],
		colModel : [{
			name : 'class',
			index: 'class',
			width : 200
		}, {
			name : 'count',
			index : 'count',
			align : 'right',
			sortable: false
				
		}],
		caption : 'Population Information'
	});
	$("#StoreDevInfo").jqGrid({
		url:rootPath + 'json/get-device-listing-for-store',
		postData:{modelId:modId,storeId:storId},
		datatype:'json',
		jsonReader: {
			repeatitems: false,
			id:"id",
			root:"rows"
		},
		height : 'auto',
		width : 'auto',
		scroll : false,
		scrollOffset : 0,
		colNames : ['Name', 'Count', '2-8C<br>Net Storage (L)', 'Below 2C<br>Net Storage (L)'],
		colModel : [{
			name : 'name',
			index: 'name',
			width : 200
		}, {
			name : 'count',
			index : 'count',
			align : 'right',
			width : 60,
			sortable : false
		}, {
			name : 'cooler',
			index : 'cooler',
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}, {
			name : 'freezer',
			id : 'freezer',
			align : 'right',
			formatter : "number",
			formatoptions : {
				decimalPlaces : 2
			}
		}],
		caption : 'Storage Devices'
	})
	
}