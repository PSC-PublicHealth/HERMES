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
<script type="text/javascript" src="{{rootPath}}static/editor-widgets/inventory_grid.js"></script>
</head>
<body>

<div id="test_grid"></div>

</body>
<script>
$("#test_grid").grid({
	modelId:{{modelId}},
	invType:"fridges",
	customCols:[['Freeser (L)','freezer','freezer'],['Coolder (L)','cooler','cooler'],['Warm (L)','warm','roomtemperature']],
	rootPath:'{{rootPath}}',
	idcode:{{idcode}},
	loadonce:false,
	editurl: '{{rootPath}}edit/store-edit-edit',
});
</script>
</html>

