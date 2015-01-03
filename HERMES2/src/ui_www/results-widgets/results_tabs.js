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
				//Not created yet
			
				var num_tabs = $("#"+this.containerID+" ul li").length + 1;
				var tab_name = "tab_"+ thisID;
				$("#"+this.containerID+" ul").append("<li><a href='#"+ tab_name + "'>"+
						tabText + "</a>"+
						"<span class='ui-icon ui-icon-close' role='presentation'>Remove Tab</span></li>");
				$("#results_summary_tabs").append("<div id='" + tab_name + "' class='rs_summary'></div>");
				//var resultsMon = node_instance.id.replace('r_','');
				//var modelId = parseInt(resultsMon.split("_")[0]);
				//var resultsId = parseInt(resultsMon.split("_")[1]);
				$("#"+this.containerID).tabs("refresh");
				$("div#"+tab_name).results_summary_page({
					resultsId:resultsId,
					modelId:modelId,
					rootPath:this.options.rootPath
				});
				// manage the tabs list
				tabList.push(thisID);
				$("#results_summary_tabs").tabs("option", "active", num_tabs-1);
				
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