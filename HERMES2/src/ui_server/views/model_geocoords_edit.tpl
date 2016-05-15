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
</style>

<script type="text/javascript" src="{{rootPath}}static/editor-widgets/geoCoordinateGrid.js"></script>
<h2>{{_("Edit the Geographic Coordinates for ")}}</h2>
<h4>
{{_("Please enter in the geographic coordinates of individual locations in the table below. Your entries will be saved automatically as you add them.")}}
<div id = "geo_grid"></div>

<div id="uploadSpreadsheetDialog" href="#">
	<p>
	{{_("You can upload an excel file that contains the geographic coordinates of locations in your model.")}}
	{{_("Note, that this will be by location name, so if you have locations that have duplicate names, the algorithm will flag this and you will have to manually resolve.")}}
	</p>
	<p>{{_("Would you like to: ")}}
	<ul>
		<li>
			<a class="model-operation-item" id="downloadSpreadsheetLink">
				{{_("Download a preformated spreadhsheet for your model.")}}
			</a>
		</li>
		<li>
			<a class="model-operation-item" id="uploadSpreadsheetLink">
				{{_("Upload a completed spreadhsheet for your model.")}}
			</a>
		</li>
	</ul>
</div>

<script>

$("#uploadSpreadsheetDialog").dialog({
	resizable:false,
	model:true,
	autoOpen:false,
	buttons:{
		'{{_("Close")}}':function(){
			$(this).dialog("close");
		}
	},
	open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER) {
			    e.preventDefault();
			    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
	    };
	}
});

$("#geo_grid").geoCoordinateGrid({
	modelId:{{modelId}},
	rootPath:'{{rootPath}}'
});
$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>