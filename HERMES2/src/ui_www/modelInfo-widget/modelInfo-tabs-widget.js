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

	$.widget("modelInfo.modelInfotabs",{
		options:{
			rootPath:'',
			modelId:'',
			modelInfoJson:'',
			trant:{
				title:"Model Information"
			}
		},
		_create:function(){
			trant = this.options.trant;
			this.containerID = $(this.element).attr('id');
			var thiscontainerID = this.containerID;
			var tabs = {
						"gen":"General Information",
					    "vac":"Vaccine Information",
					    "pop":"Population Information",
					    "store":"Storage Device Inventory",
					    "trans":"Transport Inventory"
						};
		
			$("#"+thiscontainerID).append("<div id='modelInfoTabDiv'>")
			
			//$("#modelInfoTabDiv").append("<ul id='mIul'></ul>");
			var ulString = "<ul>"
			for (var key in tabs){
				if(!tabs.hasOwnProperty(key)) continue;
				ulString += "<li><a href='#"+key+"'>"+tabs[key]+"</a></li>";
			}
			ulString += "</ul>";
			$("#modelInfoTabDiv").append(ulString);
			for(var key in tabs){
				$("#modelInfoTabDiv").append("<div id ='"+key+"' class='mi_tab'></div>");
			}
			$("#modelInfoTabDiv").tabs();
			
			$("#vac").append("<table id = 'vaccTable'></table>");
			
		}
	});
})(jQuery);