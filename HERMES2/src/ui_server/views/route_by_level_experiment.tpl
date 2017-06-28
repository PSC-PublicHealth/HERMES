%rebase outer_wrapper title_slogan=_('Modify Transport Route Characteristics Between Supply Chain Levels'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,name=name
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

<link rel="stylesheet" type="text/css" href="{{rootPath}}static/widget_css/slideshow_widget.css" />
<script src="{{rootPath}}widgets/slideshow_widget.js" type="text/javascript"></script>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/type_editor_dialog_widget.css" />
<script src="{{rootPath}}widgets/type_editor_dialog_widget.js" type="text/javascript"></script>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/type_explorer_grid_widget.css" />
<script src="{{rootPath}}widgets/type_explorer_grid.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/supply_chain_level_selector_widget.js" type="text/javascript"></script>
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/widget_css//between_supply_chain_level_selector_widget.css" />
<script src="{{rootPath}}widgets/between_supply_chain_level_selector_widget.js" type="text/javascript"></script>

<style>
.modrouteexpt_level_select_opts_level {
	width: 940px;
	text-align: left;
}
</style>

<h2>{{_("HERMES Experiment Generator: Modify Transport Route Characteristics Between Supply Chain Levels")}}</h2>
<div id="modrouteexpt_slides">
	<div id="modrouteexpt_slide1" class='addstorexpt_slide'>
		<span class='expt_subtitle'>
			{{_('Description of Modify Transport Route Characteristics Between Supply Chain Levels Experiments')}}
		</span>
		<p class='expt_text'>
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
		</p>
		<p class='expt_text'>
			will write something,will write something, will write something,
			will write something,will write something,will write something,will write something,
			will write something,will write something,will write something,will write something,
			will write something,will write something,will write something,will write something,
			will write something,will write something,will write something,will write something,
		</p>	
		<p class='expt_emph'> 
			{{_('Please press the "Next" button to continue.')}}
		</p>
	</div>
	<div id="modrouteexpt_slide2" class='modrouteexpt_slide'>
		<div class='flex_cols'>
			<div class='expt_txt'>
				<p class='expt_text'>
					{{_('Would you like to select supply chain levels by: ')}}
				</p>
			</div>
			<div id='modrouteexpt_level_select_opts_div' class='expt_txt'>
				<p>
					<label for='modrouteexpt_level_orig' class='modrouteexpt_level_select_opts_level'>
						{{_('Specifying the supply chain level where routes originate')}}
					</label>
					<input type='radio' name='modrouteexpt_level_select_opts' id="modrouteexpt_level_orig">
				</p>
				<p>
					<label for='modrouteexpt_level_between' class='modrouteexpt_level_select_opts_level'>
						{{_('Specifying between which two supply chain levels the routes travel')}}
					</label>
					<input type='radio' name='modrouteexpt_level_select_opts' id="modrouteexpt_level_between">
				</p>					
			</div>
			<div id='modrouteexpt_level_originate_level_select_div' class='expt_txt' style='display:none;'>
				<p class='expt_text'>
					{{_('Please select below originating supply chain level for which you would like modify the routes.')}}
				</p>
				<div id='modrouteexpt_level_originating_select'></div>
			</div>
			<div id='modrouteexpt_level_between_level_select_div' class='expt_txt' style='display:none;'>
				<p class='expt_text'>
					{{_('Please select below the between which supply chain levels for which you would like modify the routes.')}}
				</p>
				<div id='modrouteexpt_level_between_select'></div>
			</div>
		</div>
	</div>
	<div id="modrouteexpt_slide3" class='modrouteexpt_slide'>
		<p class='expt_text'>
			<div id="modrouteexpt_youhavechosen" class='expt_text'></div>
		</p>
		<p class='expt_text'>
			<div class='expt_text'>
				{{_('Choose below operations you would like to perform on the routes you have selected...')}}
			</div>
		</p>
		<p>
			<div id="modrouteexpt_operations_div" class='flex_col'>
				<div style='padding:0 0 10px 0;'>
					<label for='modrouteexpt_operations_changefreq' class='modrouteexpt_level_select_opts_level'>
						{{_('Change the frequency at which shippments occur.')}}
					</label>
					<input type='checkbox' name='modrouteexpt_operations' id="modrouteexpt_operations_changefreq">
				</div>
				<div style='padding:0 0 10px 0;'>
					<label for='modrouteexpt_operations_changevehicle' class='modrouteexpt_level_select_opts_level'>
						{{_('Change the transport mode used for the routes.')}}
					</label>
					<input type='checkbox' name='modrouteexpt_operations' id="modrouteexpt_operations_changevehicle">
				</div>
			</div>
		</p>
	</div>
	<div id='moderouteexpt_slide4' class='moderouteexpt_slide'>
		<div class='flex_cols'>
			<p>
				<div class='expt_text'>
					{{_('Please select below how you would like to alter the frequency of the shipments.')}}
				</div>
			</p>
			
			<div id='modrouteexpt_freq_opts_div'>
				<div style='padding:0 0 10px 0;'>
					<label for='modrouteexpt_freq_half' class='modrouteexpt_level_select_opts_level'>
						{{_('Cut the frequency by half.')}}
					</label>
					<input type='radio' name='modrouteexpt_freq_opts' id="modrouteexpt_freq_half">
				</div>
				<div style='padding:0 0 10px 0;'>
					<label for='modrouteexpt_freq_double' class='modrouteexpt_level_select_opts_level'>
						{{_('Increase the frequency by double.')}}
					</label>
					<input type='radio' name='modrouteexpt_freq_opts' id="modrouteexpt_freq_double">
				</div>
				<div style='padding:0 0 10px 0;'>
					<label for='modrouteexpt_freq_quadruple' class='modrouteexpt_level_select_opts_level'>
						{{_('Increase the frequency by quadruple.')}}
					</label>
					<input type='radio' name='modrouteexpt_freq_opts' id="modrouteexpt_freq_quadruple">
				</div>
				<div style='padding:0 0 10px 0;'>
					<label for='modrouteexpt_freq_needed' class='modrouteexpt_level_select_opts_level'>
						{{_('Have the routes make shipments as often as needed.')}}
					</label>
					<input type='radio' name='modrouteexpt_freq_opts' id="modrouteexpt_freq_needed">
				</div>
			</div>
		</div>
	</div>
	<div id='modrouteexpt_slide5' class='modrouteexpt_slide'>
		<div class='flex_cols'>
			<p>
				<div class='expt_text'>
					{{_('Please select below the vehicle that you would like to use for all of the routes.')}}
				</div>
			</p>
			<div id='modrouteexpt_change_vehicle_grid'></div>
		</div>
	</div>
	<div id='modrouteexpt_slide6' class='modrouteexpt_slide'>
		This is the summary page
	</div>
	<div id='modrouteexpt_slide7' class='modrouteexpt_slide'>
		This is the links page
	</div>
</div>
				

<script>

$("#modrouteexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	nextFunctions:[
	               function(){
	            	  // $("#addstorexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   return true;
	               },
	               function(){
	            	  return true;
	               },
	               function(){
	            	   //var idSelector = function(){return this.id; };
	            	   //var selected = $("#modrouteexpt_operations_div :checkbox:checked").map(idSelector).get();
	            	   //console.log(selected);
	            	   //console.log(selected.indexOf("modrouteexpt_operations_changefreq"));
	            	   //console.log(selected);
	            	   return true;
	               },
	               function(){
	            	   create_summary();
	            	   return true;
	               },
	               function(){
	            	   create_summary();
	            	   return true;
	               },
	               function(){
	            	   return true;
	               }
	              ],
	backFunctions:[
	               function(){return true;},
	               function(){
	            	   //$("#addstorexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   return true;
	               },
	               function(){return true;},
	               function(){return true;},
	               function(){return true;},
	               function(){return true;}
	               ],
	doneFunctions:function(){},
	doneUrl: '{{rootPath}}model-open?modelId={{modelId}}'
});

$("#modrouteexpt_level_select_opts_div :input").checkboxradio();
$("#modrouteexpt_operations_div :input").checkboxradio();
$("#modrouteexpt_freq_opts_div :input").checkboxradio();
$("#modrouteexpt_ids_opts_div :input").checkboxradio();

$("#modrouteexpt_level_between_select").betweenSupplyChainLevelSelector({
	modelId:{{modelId}},
	labelClass:'modrouteexpt_level_select_opts_level',
	onChangeFunc: function(){
		var routeParsed = $("#modrouteexpt_level_between_select").betweenSupplyChainLevelSelector("getSelectedParsed");
		$("#modrouteexpt_youhavechosen").html("{{_('You have chosen to modify routes ')}}" + routeParsed + ".");
	}
});

$("#modrouteexpt_operations_changefreq").change(function(){
	if($(this).is(":checked")){
		$("#modrouteexpt_slides").slideShowWithFlowControl("showSlide",3);
	}
	else{
		$("#modrouteexpt_slides").slideShowWithFlowControl("hideSlide",3);
	}
});

$("#modrouteexpt_operations_changevehicle").change(function(){
	if($(this).is(":checked")){
		$("#modrouteexpt_slides").slideShowWithFlowControl("showSlide",4);
	}
	else{
		$("#modrouteexpt_slides").slideShowWithFlowControl("hideSlide",4);
	}
});

$("#modrouteexpt_level_originating_select").supplyChainLevelSelector({
	modelId:{{modelId}},
	routeOrig:true,
	type:'radioSelect'
});

$("#modrouteexpt_level_select_opts_div").change(function(){
	var selected = $("#modrouteexpt_level_select_opts_div :radio:checked").attr("id");
	
	if(selected == "modrouteexpt_level_orig"){
		$("#modrouteexpt_level_between_level_select_div").fadeOut(200,function(){
			$("#modrouteexpt_level_originate_level_select_div").fadeIn(200);
		});	
		
	}
	else{
		$("#modrouteexpt_level_originate_level_select_div").fadeOut(200,function(){
			$("#modrouteexpt_level_between_level_select_div").fadeIn(200);
		});
	}
	
});

//$("#modrouteexpt_ids_opts_div").change(function(){
//	var selected = $("#modrouteexpt_ids_opts_div :radio:checked").attr("id");
//	if(selected == "modrouteexpt_is_opt"){
//		$("#modrouteexpt_ds").fadeOut(200,function(){
//			$("#modrouteexpt_is").fadeIn(200)
//		});
//	}
//	else{
//		$("#modrouteexpt_is").fadeOut(200,function(){
//			$("#modrouteexpt_ds").fadeIn(200)
//		});
//	}
//});

$("#modrouteexpt_change_vehicle_grid").typeExplorerGrid({
	modelId:{{modelId}},
	typeClass:'trucks',
	checkBoxes:false,
	groupingEnabled:false,
	namesOnly: false,
	createEnabled:true,
	width:$("#modrouteexpt_change_vehicle_grid").width()-2.5
});

$("#modrouteexpt_slides").slideShowWithFlowControl("hideSlide",3);
$("#modrouteexpt_slides").slideShowWithFlowControl("hideSlide",4);

//$("#modrouteexpt_level_between_level_select_div").change(function(){
//	var routeParsed = $("#modrouteexpt_level_between_level_select_div").betweenSupplyChainLevelSelector("getSelectedParsed");
//	$("#moderouteexpt_youhavechosen").html("{{_('You have chosen to modify routes ')}}" + routeParsed + ".");
//});

function create_summary(){
	// create data structure
	var freqOpt = '';
	if($("#modrouteexpt_operations_changefreq").is(":checked")){
		freqOpt = $("#modrouteexpt_freq_opts_div :radio:checked").attr("id");
	}
	var vehicleChange = '';
	if($("#modrouteexpt_operations_changevehicle").is(":checked")){
		vehicleChange = $("#modrouteexpt_change_vehicle_grid").typeExplorerGrid("getSelectedElements");
	}
	var dataObject = {
		'levelopt': $("#modrouteexpt_level_select_opts_div :radio:checked").attr("id"),
		'levelbetween': $("#modrouteexpt_level_between_select").betweenSupplyChainLevelSelector("getSelected"),
		'levelorig': $("#modrouteexpt_level_originating_select").supplyChainLevelSelector("getSelected"),
		'changefreg': $("#modrouteexpt_operations_changefreq").is(":checked"), 
		'changevehicle': $("#modrouteexpt_operations_changevehicle").is(":checked"), 
		'freqOpt':freqOpt,
		'vehicleChange':vehicleChange
	};

	console.log(dataObject);
}

</script>