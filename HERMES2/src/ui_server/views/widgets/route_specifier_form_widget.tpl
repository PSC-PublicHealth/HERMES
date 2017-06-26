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
	
	var routeTypeMap = {"push":["fixed","fixedAmount","supplier"],
					"varpush":["fixed","basedOnDemand","supplier"],
					"schedfetch":["fixed","fixedAmount","client"],
					"schedvarfetch":["fixed","basedOnDemand","client"],
					"pull":["variable","basedOnDemand","supplier"],
					"demandfetch":["variable","basedOnDemand","client"]
	};
	$.widget("typeWidgets.routeSpecifyFormWidget",{
		options:{
			modelId:'',
			routeId:"generic9999",
			includeStops:true,
			colFormat:true,
			unique:"",
			trant:{
				title: "{{_('Route Specification Form')}}"
			}
		},
		getJson: function(){
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			
			var thisOptions = this.options;
			
			var thisFormId = thisContainerId + thisOptions.unique + "_route_form";
			var thisFormIdMainTab = thisFormId + "_tab1";
			var thisFormIdStopsTab = thisFormId + "_tab2";
			
			// Form ids
			var typeSelectId = thisFormId + "_routeType_select";
			var fixedScheduleId = thisFormId + "_fixedSchedule_select";
			var demandSelectId = thisFormId + "_demand_select";
			var createTruckButtonId = thisFormId + "_createTruck_button";
			var createDialogId = thisFormId + "_createDialog_div";
			var truckSelectId = thisFormId + "_truckType_select";
			var shipIntervalId = thisFormId + "_shipInterval_input";
			var pullIntervalId = thisFormId + "_pullInterval_input";
			var vehicleWhereSelectId = thisFormId + "_vehicleWhere_select";
			
		
			var typeDesc=[$("#"+fixedScheduleId).val(),$("#"+demandSelectId).val(),$("#"+vehicleWhereSelectId).val()];
			
			var routeType = "none";
			for(var rT in routeTypeMap){
				if(JSON.stringify(routeTypeMap[rT]) == JSON.stringify(typeDesc)){
					routeType = rT;
					break;
				}
			}
			
			return JSON.stringify({'routeType':routeType,
								   'truckType':$("#"+truckSelectId).val(),
								   'shipInterval':$("#"+shipIntervalId).timeFormInput("value"),
								   'pullInterval':$("#"+pullIntervalId).timeFormInput("value")});
		},
		_create:function(){
			trant = this.options.trant;
			this.containerId = $(this.element).attr('id');
			var thisContainerId = this.containerId;
			
			var thisOptions = this.options;
			
			var thisFormId = thisContainerId + thisOptions.unique + "_route_form";
			var thisFormIdMainTab = thisFormId + "_tab1";
			var thisFormIdStopsTab = thisFormId + "_tab2";
			
			// Form ids
			var typeSelectId = thisFormId + "_routeType_select";
			var fixedScheduleId = thisFormId + "_fixedSchedule_select";
			var demandSelectId = thisFormId + "_demand_select";
			var createTruckButtonId = thisFormId + "_createTruck_button";
			var createDialogId = thisFormId + "_createDialog_div";
			var truckSelectId = thisFormId + "_truckType_select";
			var shipIntervalId = thisFormId + "_shipInterval_input";
			var pullIntervalId = thisFormId + "_pullInterval_input";
			var vehicleWhereSelectId = thisFormId + "_vehicleWhere_select";
		
			var flexClass= 'flex_cols';
			
			// devise the form
			
			htmlString = "<div id='" + createDialogId + "'></div>";
			htmlString += "<form id='"+thisFormId+"' action='json/throw-error'>";
			if(thisOptions.includeStops){
				htmlString += "<ul>";
				htmlString += "<li><a href='#"+thisFormIdMainTab +"'>{{_('Main')}}</a></li>";
				htmlString += "<li><a href='#"+thisFormIdStopsTab + "'>{{_('Stops')}}</a></li>";
				htmlString += "</ul>";
			}
			htmlString += "<div id='" + thisFormIdMainTab + "' class = '"+ flexClass + "' style='max-width:1000px;' >";
			htmlString += "<table class='route_spec_table' style='border:2'>";
			htmlString += "  <tr class='route_spec_table_row'>";
			htmlString += "    <td class='route_spec_table_label_col'>";
			htmlString += "      <label>{{_('Products Are')}}</label>";
			htmlString += "    </td>";
			htmlString += "    <td class='route_spec_table_input_col'>";
			htmlString += "      <select id='" + vehicleWhereSelectId + "' class='rts_selectBox'>";
			htmlString += "         <option value = 'supplier'>{{_('delivered by the supplier')}}</option>";
			htmlString += "         <option value = 'client'>{{_('picked up by the client')}}</option>";
			htmlString += "      </select>";
			htmlString += "    </td>";
			htmlString += "  </tr>";
			
			htmlString += "  <tr class='route_spec_table_row'>";
			htmlString += "    <td class='route_spec_table_label_col'>";
			htmlString += "      <label>{{_('for an amount that is')}}</label>";
			htmlString += "    </td>";
			htmlString += "    <td class='route_spec_table_input_col'>";
			htmlString += "      <select id='" + demandSelectId + "' class='rts_selectBox'>";
			htmlString += "         <option value = 'basedOnDemand'>{{_('based on demand')}}</option>";
			htmlString += "         <option value = 'fixedAmount'>{{_('a fixed amount each trip')}}</option>";
			htmlString += "      </select>";
			htmlString += "    </td>";
			htmlString += "  </tr>";
			
			htmlString += "  <tr class='route_spec_table_row'>";
			htmlString += "    <td class='route_spec_table_label_col'>";
			htmlString += "      <label>{{_('on a schedule that occurs')}}</label>";
			htmlString += "    </td>";
			htmlString += "    <td class='route_spec_table_input_col'>";
			htmlString += "      <select id='" + fixedScheduleId + "' class='rts_selectBox'>";
			htmlString += "         <option value = 'fixed'>{{_('on a fixed frequency')}}</option>";
			htmlString += "         <option value = 'variable'>{{_('as product is needed')}}</option>";
			htmlString += "      </select>";
			htmlString += "    </td>";
			htmlString += "  </tr>";
			
			htmlString += "  <tr class='route_spec_table_row'>";
			htmlString += "    <td class='route_spec_table_label_col'>";
			htmlString += "      <label>{{_('shipped with the mode of transportation ')}}</label>";
			htmlString += "    </td>";
			htmlString += "    <td class='route_spec_table_input_col'>";
			htmlString += "       <div id='" + truckSelectId + "' class='rts_selectBox'></div>";
			htmlString += "    </td>";
			htmlString += "  </tr>";
			
			htmlString += "  <tr class='route_spec_table_row'>";
			htmlString += "    <td class='route_spec_table_label_col'>";
			htmlString += "      <label>{{_('or')}}</label>";
			htmlString += "    </td>";
			htmlString += "    <td class='route_spec_table_input_col'>";
			htmlString += "       <button id='" + createTruckButtonId + "'>{{_('Create a New Mode of Transport')}}</button>";
			htmlString += "    </td>";
			htmlString += "  </tr>";

			htmlString += "  <tr class='route_spec_table_row' id='fixed_table_row'>";
			htmlString += "    <td class='route_spec_table_label_col'>";
			htmlString += "      <label>{{_('at an shipping interval of ')}}</label>";
			htmlString += "    </td>";
			htmlString += "    <td class='route_spec_table_input_col'>";
			htmlString += "       <div id='" + shipIntervalId + "' class='rts_selectBox'></div>";
			htmlString += "    </td>";
			htmlString += "  </tr>";
			
			htmlString += "  <tr class='route_spec_table_row' id='variable_table_row' style='display:none;'>";
			htmlString += "    <td class='route_spec_table_label_col'>";
			htmlString += "      <label>{{_('with an amount for which to order ')}}</label>";
			htmlString += "    </td>";
			htmlString += "    <td class='route_spec_table_input_col'>";
			htmlString += "       <div id='" + pullIntervalId + "' class='rts_selectBox'></div>";
			htmlString += "    </td>";
			htmlString += "  </tr>";
			
			htmlString += "</table>";
			
			$("#"+thisContainerId).html(htmlString);
			
			
			$("#"+truckSelectId).hrmWidget({
				widget:'simpleTypeSelectField',
				invType:'trucks',
				modelId:thisOptions.modelId,
				selected:'',
				width:200,
				persistent:true
			});
			
			$("#"+createTruckButtonId).button();
			$("#"+createTruckButtonId).click(function(e){
				e.preventDefault();
				$("#"+createDialogId).typeEditorDialog({
					modelId:thisOptions.modelId,
					typeClass: 'trucks',
					saveFunc:function(){
						
					}
				});
			});
			
			$("#"+shipIntervalId).hrmWidget({
				widget:'timeFormInput',
				value: "1:M",
				label:"",
				fieldMap:JSON.stringify({'required':true,'canzero':false})
			});
			
			$("#"+pullIntervalId).hrmWidget({
				widget:'timeFormInput',
				value: "1:M",
				label:"",
				fieldMap:JSON.stringify({'required':true,'canzero':false})
			});
			
			$("#"+fixedScheduleId).change(function(){
				if($("#"+fixedScheduleId).val() == "fixed"){
					$("#variable_table_row").hide();
					$("#fixed_table_row").show();
					
				}
				else{
					$("#fixed_table_row").hide();
					$("#variable_table_row").show();
				}
				console.log($("#"+thisContainerId).routeSpecifyFormWidget('getJson'));
			});
			
		}
	});
})(jQuery);