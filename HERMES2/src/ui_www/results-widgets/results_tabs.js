;(function($){
	
	var tabList = [];
	
	$.widget("results_widgets.results_tabs",{
		options:{
			randMon:'',
			rootPath:'',
			scrollable:true,
			resizable:false,
			trant:{
				title:"Summary of Results"
			}
		},
		
		add: function(modelId,resultsId,tabText){
			var thisID = modelId + "_" + resultsId;
			var tabTitle = "Summary: Model"
			if(tabList.indexOf(thisID) > -1){
				$("#"+this.containerID).tabs("option", "active", tabList.indexOf(thisID));
			}
			else{
				var num_tabs = $("#"+this.containerID+" ul li").length + 1;
				var tab_name = "tab_"+ thisID;
				$("#"+this.containerID+" ul").append("<li><a href='#"+ tab_name + "'>"+
						tabText + "</a>"+
						"<span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>");
				$("#"+this.containerID).append("<div id='" + tab_name + "' class='rs_summary'></div>");
				$("#"+this.containerID).tabs("refresh");
				$("div#"+tab_name).results_summary_page({
					resultsId:resultsId,
					modelId:modelId,
					rootPath:this.options.rootPath
				});
				// manage the tabs list
				tabList.push(thisID);
				$("#"+this.containerID).tabs("option", "active", num_tabs-1);
			}
		},
		
		remove: function(modelId,resultsId){
			var thisID = modelId + "_" + resultsId;
			if(tabList.indexOf(thisID) > -1){
				// This tab is actually open
				var div = $("#tab_"+thisID);
				var ariaLab = div.attr("aria-labelledBy");
				var linkLi = $("#"+ariaLab).closest("li");
				//Remove the elements
				linkLi.remove();
				div.remove();
				if(tabList.length>1){
					if($("#"+this.containerID).tabs("option","active")==tabList.indexOf(thisID)){
						if(tabList.indexOf(thisID)==0){
							$("#"+this.containerID).tabs("option", "active", tabList.indexOf(thisID)+1);
						}
						else{
							$("#"+this.containerID).tabs("option", "active", tabList.indexOf(thisID)-1);
						}
					}
				}	
				tabList.splice(tabList.indexOf(thisID),1);
			}
		},
			


		_create:function(){
			trant = this.options.trant;
			
			this.containerID = $(this.element).attr('id');
			var containerID = this.containerID;
			
			
			$("#"+this.containerID).tabs();
			$("#"+this.containerID).addClass("rs_tabs");
			
			
			$("#"+this.containerID).delegate( "span.ui-icon-close", "click", function() {
			      var panelId = $( this ).closest( "li" ).remove().attr( "aria-controls" );
			      $( "#" + panelId ).remove();
			      var toDeleteId = panelId.replace("tab_","");
			      tabList.splice(tabList.indexOf(toDeleteId),1);
			      $('#results_summary_tabs').tabs( "refresh" );
			});
		}	
	});		
})(jQuery);