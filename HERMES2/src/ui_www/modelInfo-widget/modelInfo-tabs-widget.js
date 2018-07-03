/*
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
