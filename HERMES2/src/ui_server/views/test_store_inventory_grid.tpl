%rebase outer_wrapper title_slogan=_('test Storage Inventory Grid'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,storeId=storeId
<!---
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
-->
<style>
.model-operation-title{
	font-size:20px;
	font-weight:bold;
}
.model-operation-second{
	font-size:11px;
}
a.model-operation-item:link{
	font-size:14px;
	color:#282A57;
}
a.model-operation-item:visited{
	font-size:14px;
	color:#282A57;
}
.large_dialog_font{
	font-size:16px;
	font-family:'Century Gothic', Arial, 'Arial Unicode MS', Helvetica, Sans-Serif;
}
.large_dialog_font p{
	padding:10px;
	text-align:center;
}
</style>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/type_editor_dialog_widget.css" />
<script src="{{rootPath}}widgets/type_editor_dialog_widget.js" type="text/javascript"></script>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/type_explorer_grid_widget.css" />
<script src="{{rootPath}}widgets/type_explorer_grid.js" type="text/javascript"></script>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/route_specifier_form_widget.css" />
<script src="{{rootPath}}widgets/route_specifier_form_widget.js" type="text/javascript"></script>

<!--<div id="test_store_grid"></div>
<div id="selects_tests">
	<div id="test_store_select"></div>
	<div id="test_vaccine_select"></div>
	<div id="test_truck_select"></div>
	<div id="test_people_select"></div>
	<div id="test_staff_select"></div>
	<div id="test_perdiem_select"></div>
</div>
<div id="button_tests">
	<div id="test_type_info_button"></div>
	<div id="test_type_truck_button"></div>
</div>-->
<!--<div id="typeGrids_tests">
	<div id="test_vaccine_typeGrid"></div>
</div>-->
<div id="test_truck_select"></div>
<div id="test_vaccine_select"></div>
<div id="route_form_test"></div>
<script>
$("#route_form_test").routeSpecifyFormWidget({
	modelId:{{modelId}},
	includeStops:false,
});

//$(function(){
//	$("#test_store_grid").hrmWidget({
///		widget:'simpleStorageDeviceTable',
//		modelId:{{modelId}},
//		storeId:{{storeId}},
//		showHead:false,
//		showGrid:false
//	});
//	
//	$("#test_store_grid").simpleStorageDeviceTable("reloadGrid");
//	
//	$("#test_store_select").hrmWidget({
//		widget:'simpleTypeSelectField',
//		modelId:{{modelId}},
//		invType:'fridges',
//		default:"MF214_E",
//		maxHeight:200
//	});
//	
	$("#test_vaccine_select").hrmWidget({
		widget:'simpleTypeSelectField',
		modelId:{{modelId}},
		invType:'vaccines',
		persistent:true
	});

	$("#test_truck_select").hrmWidget({
		widget:'simpleTypeSelectField',
		modelId:{{modelId}},
		invType:'trucks',
		persistent:true
	});
//	$("#test_people_select").hrmWidget({
//		widget:'simpleTypeSelectField',
//		modelId:{{modelId}},
//		invType:'people'
//	});
//	$("#test_staff_select").hrmWidget({
//		widget:'simpleTypeSelectField',
//		modelId:{{modelId}},
//		invType:'staff'
//	});
//		
//	$("#test_perdiem_select").hrmWidget({
//		widget:'simpleTypeSelectField',
//		modelId:{{modelId}},
//		invType:'perdiems'
//	});
//	
//	$("#test_type_info_button").hrmWidget({
//		widget:'typeInfoButtonAndDialog',
//		modelId: {{modelId}},
//		typeId: "MF214_E",
//		typeClass: 'fridges'
//	});
//	
//	$("#test_type_truck_button").hrmWidget({
//		widget:'typeInfoButtonAndDialog',
//		modelId: {{modelId}},
//		typeId: "truck_district",
//		typeClass: 'trucks'
//	});
//	$("#test_vaccine_typeGrid").typeExplorerGrid({
//		modelId: {{modelId}},
//		typeClass: 'fridges',
//		min_height:100,
//		min_width:200,
//		height:200,
//		width:1000
//	});
//	
	
	$("#test_type_info_button").hrmWidget({
		widget:'typeInfoButtonAndDialog',
		modelId: {{modelId}},
		typeId: "MF214_E",
		typeClass: 'fridges'
	});
	
	$("#test_type_truck_button").hrmWidget({
		widget:'typeInfoButtonAndDialog',
		modelId: {{modelId}},
		typeId: "truck_district",
		typeClass: 'trucks'
	});
	$("#test_vaccine_typeGrid").typeExplorerGrid({
		modelId: 1,
		typeClass: 'vaccines'
	});
	
	
});
</script>
