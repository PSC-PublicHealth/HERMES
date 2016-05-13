%rebase outer_wrapper title_slogan=_('Edit Model Geographic Coordinates'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId
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
</style>
<html>

<script type="text/javascript" src="{{rootPath}}static/editor-widgets/geoCoordinateGrid.js"></script>
<h2>{{_("Edit the Geographic Coordinates for ")}}</h2>
<h4>
{{_("Please enter in the geographic coordinates of individual locations in the table below. Your entries will be saved automatically as you add them.")}}
<div id = "geo_grid"></div>

<script>
$("#uploadSpreadSheetButton").button();
$("#doneButton").button();
$("#geo_grid").geoCoordinateGrid({
	modelId:{{modelId}},
	rootPath:'{{rootPath}}'
});
$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>