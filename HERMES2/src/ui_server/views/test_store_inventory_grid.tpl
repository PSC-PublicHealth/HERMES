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

<div id="test_store_grid"></div>
<div id="test_store_select"></div>
<div id="test_type_info_button"></div>
<script>
$(function(){
	$("#test_store_grid").hrmWidget({
		widget:'simpleStorageDeviceTable',
		modelId:{{modelId}},
		storeId:{{storeId}},
		showHead:false,
		showGrid:false
	});
//	
//	$("#test_store_grid").simpleStorageDeviceTable("reloadGrid");
//	
	$("#test_store_select").hrmWidget({
		widget:'simpleTypeSelectField',
		modelId:{{modelId}},
		invType:'fridges'
	});
	
	$("#test_type_info_button").hrmWidget({
		widget:'typeInfoButtonAndDialog',
		modelId: {{modelId}},
		typeId: "MF214_E",
		typeClass: 'fridges'
	});
});
</script>