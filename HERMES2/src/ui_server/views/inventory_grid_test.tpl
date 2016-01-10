%rebase outer_wrapper _=_,title_slogan=_('Supply Chain Modeling Tool')
<!DOCTYPE html>
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
<html>
<head>
<link rel="stylesheet" href="{{rootPath}}static/jquery-ui-1.10.2/themes/base/jquery-ui.css" />
<link rel="stylesheet" type="text/css" media="screen" href="{{rootPath}}static/jqGrid-4.4.4/css/ui.jqgrid.css" />
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/hermes_custom.css" />
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/jquery-rcrumbs-3234d9e/jquery.rcrumbs.css" />
<script src="//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
<script src="{{rootPath}}static/jquery-ui-1.10.2/ui/jquery-ui.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jstree-v.pre1.0/jquery.jstree.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jqGrid-4.4.4/js/i18n/grid.locale-en.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery-rcrumbs-3234d9e/jquery.rcrumbs.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jqGrid-4.4.4/js/jquery.jqGrid.min.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jQuery-File-Upload-7.4.1/js/jquery.fileupload.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery-form-3.45.0.js"></script>
<script type="text/javascript" src="{{rootPath}}static/editor-widgets/inventory_grid.js"></script>
</head>
<body>
<form id='grid_test_form' action='json/throw-error'>
<div>
<div id="test_grid"></div>
</div>
<div>
<div id="test_grid_submit_button" style="float:right">Submit</div>
<div id="test_grid_cancel_button" style="fload:right">Cancel</div>
</div>
</form>

</body>
<script>
$("#test_grid").inventory_grid({
	modelId:{{modelId}},
	invType:"fridges",
	customCols:[['Freeser (L)','freezer','freezer','float'],['Coolder (L)','cooler','cooler','float'],['Warm (L)','warm','roomtemperature','float']],
	rootPath:'{{rootPath}}',
	caption:'Storage Devices',
	loadonce:true,
	unique:2,
	idcode:"truck_district",
	gridurl:"{{rootPath}}json/manage-truck-storage-table",
	gridpostdata:{"modelId":{{modelId}},"typename":"truck_district","unique":2},
	editurl: '{{rootPath}}edit/store-edit-edit',
});

$("#test_grid_submit_button").button();
$("#test_grid_cancel_button").button();

$("#test_grid_submit_button").click(function(e){
	$("#grid_test_form").submit();
});

$("#grid_test_form").submit( function(event){
	event.preventDefault();
	console.log('data here');
	console.log($('#test_grid').inventory_grid("data"));
	$(this).ajaxSubmit({
		data:{
			modelId:{{modelId}},
			typename:"truck_district",
			unique:2,
			storedata:$('#test_grid').inventory_grid("data"),
		},
		url:'{{rootPath}}json/update-truck-storage',
		dataType:'json',
		type:'POST',
		success:(function(data){
			if(data.success){
				alert("truck updated successfully");
			}
			else {
				alert(data['msg']);
				//if (opFuncs && opFuncs.onServerError) opFuncs.onServerError.bind(home.first())(data,opFuncs.callbackData);
			}
		
		}),
		error:  (function(jqxhr, textStatus, error) {
			alert('{{_("Error: ")}}'+jqxhr.responseText);
		}),
	})
});
</script>
</html>

