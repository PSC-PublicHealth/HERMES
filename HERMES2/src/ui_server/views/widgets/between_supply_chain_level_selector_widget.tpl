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
	$.widget("typeWidgets.betweenSupplyChainLevelSelector",{
		options:{
			modelId:'',
			//type:'selectBox',
			title: "",
			width:500,
			labelClass:'',
			excludeRootAndClients:false,
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
			
			var selected = $("#"+selectBoxId + " :radio:checked").attr('id');
			
			if(selected.length == 0){
				return "None";
			}
			else{
				if(selected.indexOf("loop") != -1){
					var selectedSub = selected.substring(selected.indexOf("loop"),selected.length);
					console.log(selectedSub);
					var selectedSplit = selectedSub.split("_");
					var returnString =  "{{_('for loops starting at the ')}}" + selectedSplit[1] + "{{_(' involving the levels: ')}}";
					for(var i=2;i<selectedSplit.length;++i){
						if(i == selectedSplit.length-1) {
							if(selectedSplit.length == 3){
								returnString += selectedSplit[i];
							}
							else{
								returnString += "{{_(' and ')}}" + selectedSplit[i];
							}
						}
						else{
							returnString += selectedSplit[i] + ",";
						}
					}
					return returnString;
				}
				else{
					selectedSplit = selected.split("_");
					console.log(selectedSplit);
					return "{{_('between the ')}}" + selectedSplit[selectedSplit.length-2] + "{{_(' level  to the ')}}" + selectedSplit[selectedSplit.length-1] + "{{_(' level')}}";
				}
			}
		},
		_create: function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			
			var thisContainerId = this.containerId;
			var selectBoxId = thisContainerId + "_select_id";
			var thisOptions = this.options;
			
			var class_pre = "hermes_supply_chain_level_selector_";
			$("#"+thisContainerId).addClass(class_pre + "main_div");
			var thisURL = "{{rootPath}}json/get-levels-between-routes-in-model";
			
			$.ajax({
				url: thisURL,
				data:{modelId:thisOptions.modelId}
			})
			.done(function(results){
				if(results.success){
					var htmlString = "<div id='" + selectBoxId + "' class='flex_cols'>";
						for(var i=0; i< results.levelsBetween.length; ++i){
							levelToParse = results.levelsBetween[i];
							
							if(levelToParse[0] == 'loop'){
								//This is a loop
								labelString = '{{_("Loops Beginning at ")}}' + levelToParse[1][0] + '{{_(" to Locations in the Levels: ")}}';
								valueString = "loop_"+levelToParse[1][0];
								for(var j = 1; j<levelToParse[1].length;++j){
									labelString += levelToParse[1][j];
									if(j != levelToParse[1].length - 1) labelString += ",";
									valueString += "_"+levelToParse[1][j];
								}
							}
							else{
								labelString = levelToParse[0] + '{{_(" to ")}}' + levelToParse[1];
								valueString = levelToParse[0] + '_' + levelToParse[1];
							}
							htmlString += "<div class='hermes_supply_chain_level_selector_item'><label class='"+thisOptions.labelClass +"' for='" + selectBoxId + "_radio_" + valueString + "'>"+  labelString +"</label>";
							htmlString += "<input type='radio' name='" +  selectBoxId + "_radio' id= '" + selectBoxId + "_radio_" + valueString + "'></div>";
						}
						
						htmlString += "</div">
						$("#"+thisContainerId).html(htmlString);
						$("#"+selectBoxId + " :input").checkboxradio();
						$("#"+selectBoxId + " :input").change(function(){
							thisOptions.onChangeFunc();
						})
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