/*
*/

;(function($){
	$.widget("typeWidgets.supplyChainLevelSelector",{
		options:{
			modelId:'',
			type:'selectBox',
			title: "",
			width:500,
			excludeRootAndClients:false,
			excludeClients:false,
			belowLevel:'',
			addOptions: [],
			routeOrig:false,
			onChangeFunc:function(){},
			trant:{
				title: "{{_('Supply Chain Level Selector')}}"
			}
		},
		getSelected: function(){
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var selectBoxId = thisContainerId + "_select_id";
			var thisOptions = this.options;
			
			var selected = $("#"+selectBoxId + " :radio:checked");
			
			if(selected.length == 0){
				return "None";
			}
			else{
				return selected.attr('id');
			}
		},
		getSelectedParsed: function(){
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var selectBoxId = thisContainerId + "_select_id";
			var thisOptions = this.options;
			
			var selected = $("#"+selectBoxId + " :radio:checked");
			if(selected.length == 0){
				return "None";
			}
			else{
				return selected.attr('id').replace(selectBoxId + "_radio_",'');
			}
		},
		_create: function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var selectBoxId = thisContainerId + "_select_id";
			var thisOptions = this.options;
			
			var class_pre = "hermes_supply_chain_level_selector__";
			$("#"+thisContainerId).addClass(class_pre + "main_div");
			var thisURL = "{{rootPath}}json/get-levels-in-model";
			if (thisOptions.belowLevel != ''){
				thisURL = "{{rootPath}}json/get-levels-below-level";
			}
			else if (thisOptions.excludeRootAndClients){
				thisURL = "{{rootPath}}json/get-levels-sans-clients-and-root";
			}
			else if (thisOptions.excludeClients){
				thisURL = "{{rootPath}}json/get-levels-sans-clients";
			}
			else if(thisOptions.routeOrig){
				thisURL = "{{rootPath}}json/get-originating-route-levels-in-model";
			}
			$.ajax({
				url: thisURL,
				data:{modelId:thisOptions.modelId,level:thisOptions.belowLevel}
			})
			.done(function(results){
				if(results.success){
					if(thisOptions.type == 'selectBox'){
						var htmlString = "<select id='" + selectBoxId + "'>";
						for (var i=0; i < results.levels.length; ++i){
								htmlString += "<option value='"+results.levels[i]+"'>"+results.levels[i] + "</option>";
						}
						htmlString += "</select>";
						$("#"+thisContainerId).html(htmlString);
						$("#"+selectBoxId).selectmenu();
					}
					else if(thisOptions.type=='radioSelect'){
						var htmlString = "<div id='" + selectBoxId + "'>";
						for(var i=0; i< results.levels.length; ++i){
							htmlString += "<label  for='" + selectBoxId + "_radio_" + results.levels[i] + "'>"+  results.levels[i] +"</label>";
							htmlString += "<input type='radio' name='" +  selectBoxId + "_radio' id= '" + selectBoxId + "_radio_" + results.levels[i] + "'>";
						}
						if(thisOptions.addOptions.length > 0){
							for(var option in thisOptions.addOptions){
								thisOption = thisOptions.addOptions[option];
								htmlString += "<label  for='" + selectBoxId + "_radio_" + thisOption.value + "'>"+  thisOption.option +"</label>";
								htmlString += "<input type='radio' name='" +  selectBoxId + "_radio' id= '" + selectBoxId + "_radio_" + thisOption.value + "'>";
							}
						}
						
						htmlString += "</div">
						$("#"+thisContainerId).html(htmlString);
						$("#"+selectBoxId + " :input").checkboxradio();
						$("#"+selectBoxId + " :input").change(function(){
							thisOptions.onChangeFunc();
						})
					}
				}
				else{
					alert("{{_('supplyChainLevelSelector: Error getting levels')}}" + results.msg);
				}
			})
			.fail(function(jqxfr, textStatus, error){
 				alert("{{_('supplyChainLevelSelector: Failed getting levels')}}");
			});
		},
		_destroy:function(){
		}
	});
})(jQuery);
