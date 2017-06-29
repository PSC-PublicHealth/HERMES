%rebase outer_wrapper title_slogan=_('Remove a Supply Chain Level'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,name=name
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

<style>
.remlevexpt_slide {
	position:relative;
	display:inline-block;
	margin-right:-4px;
	white-space:normal;
	vertical-align:top;
	*display:inline;
	width:800px;
	height:500px;	
}

#remlevexpt_slides {
	position:relative;
	overflow:hidden;
	margin:0 0 0 0;
	width:800px;
	height:500px;
	white-space:nowrap;
}

#remlevexpt_buttons{
	margin: 10 10 10 10;
}

.remlevexpt_button_disabled{
	color: #999;
}

</style>
-->
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/widget_css/slideshow_widget.css" /> 
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/widget_css/route_specifier_form_widget.css" />
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/widget_css/type_editor_dialog_widget.css" />
<script src="{{rootPath}}widgets/slideshow_widget.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/type_explorer_grid.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/type_editor_dialog_widget.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/supply_chain_level_selector_widget.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/route_specifier_form_widget.js" type="text/javascript"></script>


<h2>{{_("HERMES Experiment Generator: Removal of A Supply Chain Level")}}</h2>
<div id="remlevexpt_slides">
	<div id="remlevexpt_slide1" class='remlevexpt_slide'>
		<span class='expt_subtitle'>
			{{_('Description of Removing a Suply Chain Level Experiments')}}
		</span>
		<p class='expt_text'>
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
		</p>
		<p class='expt_text'>
			{{_('This experiment will take you through a series of screens that will allow you to specify a supply chain level to remove.')}}
			{{_('Additionally, you will need to specify some characteristics for the new routes that will be created as a result of the supply chain level being removed.')}}
			{{_('Once these options are specified, HERMES will automatically create a new model with the specified supply chain level removed.')}}
		</p>	
		<p class='expt_emph'> 
			{{_('Please press the "Next" button to continue.')}}
		</p>
	</div>
	<div id="remlevexpt_slide2" class='remlevexpt_slide'>
		<div class="flex_cols">
			<div class="expt_txt">
				<p class='expt_text'>
					{{_('Please select from below the supply chain level that you would like to remove from the system.')}}
				</p>
			</div>
			<div id='remlevexpt_level_select'></div>
			<div id='remlevexpt_route_opts' class="expt_txt" style="display:none">
				<p class='expt_text'>
					{{_('Now you must select how the new routes between locations at the supply chain levels will be defined.  Please select from below one of the following options')}}
				</p>
				<p>
					<label for="remlevexpt_fromabove" class='remlevexpt_opts_label'>
							{{_('Use the charactistics of routes from the supply chain level above the level to be removed')}}
					</label>
					<input type='radio' name="remlevexpt_route_options" id="remlevexpt_fromabove">
				</p>
				<p>
					<label for="remlevexpt_frombelow" class='remlevexpt_opts_label'>
						{{_('Use the charactistics of routes from the supply chain level below the level to be removed')}}
					</label>
					<input type='radio' name="remlevexpt_route_options" id="remlevexpt_frombelow" checked>
				</p>
				<p>
					<label for="remlevexpt_custom" class='remlevexpt_opts_label'>
						{{_('Define your own route characteristics the supply chain level below the level to be removed')}}
					</label>
					<input type='radio' name="remlevexpt_route_options" id="remlevexpt_custom">
				</p>
			</div>
		</div>
	</div>
	
	<div id="remlevexpt_slide3" class='remlevexpt_slide'>
		<div id="remlevexpt_route_spec_form"></div>
	</div>
	
	<div id="remlevexpt_slide4" class='remlevexpt_slide'>
		<div id='remlevexpt_summary_title'>
			<span class='expt_subtitle'>
				{{_('Remove a Supply Chain Level Experiment Summary')}}
			</span>
		</div>
		<div id="remlevexpt_summary_text"></div>
		<div id='remlevexpt_click_next" class='expt_text'>
			{{_("Please click the Next button above to complete the experiment")}}
		</div>
	</div>
	
	<div id='remlevexpt_slide5' class='remlevexpt_slide'>
		<div id="addstorexpt_final_links_div">
			<span class='expt_subtitle'>
				{{_('Below are some additional actions that you may want to perform on your newly modified model:')}}
			</span>
			<span class="expt_text">
				<ul class="proper_ul">
					<li>
						<a href="{{rootPath}}model-edit-population-tabular?modelId={{modelId}}">
							{{_('Update the Number of People Served by Each Supply Chain Location')}}
						</a>
					</li>
					<li>
						<a href="{{rootPath}}model-edit-store-inventory-tabular?modelId={{modelId}}">
							{{_("Further Modify the Storage Device Inventory of Each Supply Chain Location")}}
						</a>
					</li>
					<li>
						<a href="{{rootPath}}model-edit-structure?id={{modelId}}">
							{{_("Open the New Model in the HERMES Advanced Editor to Make Further Changes")}}
						</a>
					</li>
					<li>
						{{_("Or If you are finished creating this experiment:")}}
						<a href="{{rootPath}}model-run?modelId={{modelId}}">
							{{_("Run Simulations of this Model")}}
						</a>
					</li>
				</ul>
			</span>
		</div>
	</div>
</div>

	
<script>
$("#remlevexpt_route_opts :input").checkboxradio();

$("#remlevexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	nextFunctions:[
	               function(){
	            	   if($("#remlevexpt_level_select").supplyChainLevelSelector("getSelected") == "None"){
	            		   $("#remlevexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   }
	            	   return true;
	               },
	               function(){
	            	   if(!$("#remlevexpt_slide3").is(":visible")){
	            		   createSummary();
	            	   }
	            	 //$("#remlevexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   return true;
	               },
	               function(){
	            	  createSummary();
	            	  return true;
	               },
	               function(){
	            	   return true;
	               }
	             //  function(){
	            	//   if($("#remlevexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("validate")){
	            	//	   createSummary();
	            	//	   return true;
	            	//   }
	            	//   else{
	            	//	   return false;
	            	 //  }
	             //  }
	              ],
	backFunctions:[
	               function(){return true;},
	               function(){
	            	  // $("#remlevexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   //$("#remlevexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("destroy"); 
	            	   return true;
	               },
	               function(){return true;},
	               function(){return true;}
	               ],
	doneFunctions:function(){},
	doneUrl: '{{rootPath}}model-open?modelId={{modelId}}'
	
});

$("#remlevexpt_level_select").supplyChainLevelSelector({
	modelId: {{modelId}},
	excludeRootAndClients:true,
	type:'radioSelect',
	onChangeFunc:function(){
		$("#remlevexpt_route_opts").fadeIn(200,function(){
				$("#remlevexpt_slides").slideShowWithFlowControl("activateButton","next");
		});
	}
});

$("#remlevexpt_route_spec_form").routeSpecifyFormWidget({
	modelId:{{modelId}},
	includeStops:false
});

$("#remlevexpt_slides").slideShowWithFlowControl("hideSlide",2);

$("#remlevexpt_route_opts").change(function(){
	var currentVal = $("#remlevexpt_route_opts :radio:checked").attr("id");
	console.log("Current Val = "+currentVal);
	if(currentVal == "remlevexpt_custom"){
		$("#remlevexpt_slides").slideShowWithFlowControl("showSlide",2);
	}
	else{
		$("#remlevexpt_slides").slideShowWithFlowControl("hideSlide",2);
	}
});

function createSummary(){
	// prepare data
	var dataObject = {
		'level':$("#remlevexpt_level_select").supplyChainLevelSelector("getSelected").replace("remlevexpt_level_select_select_id_radio_",""),
		'option':$("#remlevexpt_route_opts :radio:checked").attr("id"),
		'newRoute':'None'
	};
	
	if($("#remlevexpt_route_opts :radio:checked").attr("id") == "remlevexpt_custom"){
		dataObject['newRoute'] = $("#remlevexpt_route_spec_form").routeSpecifyFormWidget("getData");
	}
	
	$.ajax({
		url:{{rootPath}}+"json/level_removal_summary",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	})
	.done(function(results){
		if(results.success){
			$("#remlevexpt_summary_text").html(results.html);
		}
		else{
			alert("{{_('There was a problem getting the summary text for the remove level experiment: ')}}" + results.msg);
		}
	})
	.fail(function(jqxhr,textStatus,error){
		alert("{{_('There was a failure in getting the summary text for the remove level experiment: ')}}" + jqxhr.responseText);
	});
}
	
</script>