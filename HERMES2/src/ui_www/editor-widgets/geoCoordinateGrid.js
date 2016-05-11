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

	$.widget("modelEdit.geoCoordinateGrid",{
		options:{
			rootPath:'',
			modelId:'',
			trant:{
				title:"Geo Coordinate Editor"
			}
		},
		_create:function(){
			trant = this.options.trant;
			this.containerID = $(this.element).attr('id');
			var thiscontainerID = this.containerID;
			var thisTableID = thiscontainerID + "_tbl";
			var thisPagerID = thiscontainerID + "_pager";
			
			$("#"+thiscontainerID).append("<table id='" + thisTableID + "'></table>");
			$("#"+thiscontainerID).append("<div id='" + thisPagerID+ "'></div>");
			
			var thisoptions = this.options;
			var rootPath = this.options.rootPath;
			
			if(rootPath == ''){
				alert('Cannot use inventory_grid without a rootPath');
				return;
			}
			
			var modelId = this.options.modelId;
			if(modelId == ''){
				alert('Cannot use inventory_grid without a modelId');
			}
			
			var colNames = ["idcode","Location Name","Supply Chain Level"]
		}
	});
})(jQuery);