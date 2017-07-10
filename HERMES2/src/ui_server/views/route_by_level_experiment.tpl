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
			{{_('A supply chain is mostly about moving products between locations till finally the products arrives where it will be given to people.')}}
			{{_('Therefore, transport is a critical component to the supply chain.')}}
			{{_('The type of vehicle or mode of transport one uses, the policy that dictates ordering and moving of product, and geographic characteristics can all have a signficant impact on the performance and efficiency of the supply chain.')}}
			{{_('Modeling can help one understand and quantify this impact.')}}
		</p>
		<p class='expt_text'>
			{{_('This experiment will allow you to choose a collection of routes based on what supply chain level the routes originate at or which supply chain levels the routes run between.')}}
			{{_('You can then specify operations to perform on the routes such as increasing the frequency and changing the mode of transport that will be used on the routes.')}}
			{{_('Based on the specifications, HERMES will create a new model that alters all of the selected routes.')}}
		</p>	
		<br><hr><br>
		<p class='expt_text'>
			{{_('Below are some example publications where modifying transport route characteristics in a supply chain is explored with HERMES modeling: ')}}
			<ul class='proper_ul'>
				<li>
					<a href="https://www.ncbi.nlm.nih.gov/pubmed/27340098" target="blank">
						Haidari LA, Brown ST, Ferguson M, Bancroft E, Spiker M, Wilcox A, Ambikapathi 
						R, Sampath V, Connor DL, Lee BY. 
						{{_('The economic and operational value of using drones to transport vaccines.')}}
						<em>Vaccine</em>. 2016 Jul 25;34(34):4062-7. doi:
						10.1016/j.vaccine.2016.06.022. Epub 2016 Jun 20. PubMed PMID: 27340098.
					 </a>
				</li>
				<li>
					<a href="https://www.ncbi.nlm.nih.gov/pubmed/23717590" target="blank">
						Haidari LA, Connor DL, Wateska AR, Brown ST, Mueller LE, Norman BA, Schmitz
						MM, Paul P, Rajgopal J, Welling JS, Leonard J, Chen SI, Lee BY. 
						{{_("Augmenting transport versus increasing cold storage to improve vaccine supply chains.")}}
						<em>PLos One.</em> 2013 May 22;8(5):e64303. doi: 10.1371/journal.pone.0064303. Print 2013.
						Erratum in: PLoS One. 2013;8(12).
						doi:10.1371/annotation/b428dad2-e829-4289-acae-c44369d55a80. PubMed PMID:
						23717590; PubMed Central PMCID: PMC3661440.
					 </a>
				</li>
				<li>
					<a href = "https://www.ncbi.nlm.nih.gov/pubmed/23903398" target="blank">
						Haidari LA, Connor DL, Wateska AR, Brown ST, Mueller LE, Norman BA, Schmitz
						MM, Paul P, Rajgopal J, Welling JS, Leonard J, Claypool EG, Weng YT, Chen SI, Lee
						BY. 
						{{_('Only adding stationary storage to vaccine supply chains may create and worsen transport bottlenecks.')}}
						<em>J Public Health Manag Pract.</em> 2013 Sep-Oct;19 Suppl
						2:S65-7. doi: 10.1097/PHH.0b013e31828a83fe. PubMed PMID: 23903398; PubMed Central
						PMCID: PMC4540066.
					</a>
				</li>			
			</ul>
		</p>
	</div> <!-- slide -->
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
				<div id='asneeded' style='padding:0 0 10px 0;'>
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
		<div id='modrouteexpt_summary_title'>
			<span class='expt_subtitle'>
				{{_('Remove a Supply Chain Level Experiment Summary')}}
			</span>
		</div>
		<div id='modrouteexpt_summary_div'></div>
		<div id='remlevexpt_click_next" class='expt_text'>
			{{_("Please click the Next button above to complete the experiment")}}
		</div>
	</div>
	<div id='modrouteexpt_slide7' class='remlevexpt_slide'>
		<div id='modrouteexpt_implementing' style="display:none;">
			<div id='modrouteexpt_implementing_text' class='expt_subtitle'>
				{{_("HERMES is implementing your experiment.")}}
			</div>
			<div id='implementing_gif'>
				<img src="{{rootPath}}static/images/kloader.gif">
			</div>
		</div>
	</div>
	<div id='modrouteexpt_slide8' class='modrouteexpt_slide'>
		<div id="modrouteexpt_final_links_div">	
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

$("#modrouteexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	nextFunctions:[
	               function(){
	            	   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   if($("#modrouteexpt_level_select_opts_div :radio:checked").attr("id")=="modrouteexpt_level_orig"){
	            		   if($("#modrouteexpt_level_originating_select").supplyChainLevelSelector("getSelectedParsed") == "None"){
	            			   $("#moderouteexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            		   }
	            	   }
	            	   else if($("#modrouteexpt_level_select_opts_div :radio:checked").attr("id")=="modrouteexpt_level_between"){
	            		   if($("#modrouteexpt_level_between_select").betweenSupplyChainLevelSelector("getSelectedParsed") == "None"){
	            			   $("#modrouteexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            		   }
	            	   }
	            	   else if($("#moderouteexpt_level_select_opts_div :radio:checked").length == 0){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   }
	            	   
	            	   $("#modrouteexpt_operations_div").change(function(){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   });
	            	   
	            	   
	            	   return true;
	               },
	               function(){
	            	   $("#modrouteexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   //$("#modrouteexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   if ($("#modrouteexpt_operations_changefreq").is(":checked")){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   }
	            	   
	            	   if ($("#modrouteexpt_operations_changevehicle").is(":checked")){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   }
	            	   //$("#addstorexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	  return true;
	               },
	               function(){
	            	   $("#modrouteexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   
	            	   if ($("#modrouteexpt_freq_opts_div :radio:checked").length > 0){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   }
	            	   
	            	   if($("#modrouteexpt_change_vehicle_grid").typeExplorerGrid("getSelectedElements")[0] != null){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   }
	            	   
	            	   $("#modrouteexpt_freq_opts_div").change(function(){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   });
	            	   
	            	   $("#modrouteexpt_change_vehicle_grid").change(function(){alert("here");})	  	      
	            	   return true;
	               },
	               function(){
	            	   
	            	   $("#modrouteexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   
	            	   if (!$("#modrouteexpt_operations_changevehicle").is(":checked")){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   }
	            	   
	            	   if($("#modrouteexpt_change_vehicle_grid").typeExplorerGrid("getSelectedElements")[0] != null){
	            		   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   }
	            	   createSummary();
	            	   return true;
	               },
	               function(){
	            	   createSummary();
	            	   return true;
	               },
	               function(){
	            	   //$("#modrouteexpt_slides").slideShowWithFlowControl("deactivateButton","back");
	            	   $("#modrouteexpt_implementing").fadeIn(1000);
	            	   //$("#modrouteexpt_slides").slideShowWithFlowControl("hideButton","back");
	            	   //$("#modrouteexpt_slides").slideShowWithFlowControl("hideButton","next");
					   $("#modrouteexpt_slides").slideShowWithFlowControl("hideButtons");
	            	   implementExperiment()
		            		.done(function(results){
		            			if(results.success){	
		            				var count = 0;
		            				if(results.warnings != ''){
		            					htmlString = "<div class='expt_subtitle'>{{_('Note there were warnings with the experiment.')}}</div>";
		            					htmlString += "<div class='expt_text'>"+results.warnings+"</div>";
		            					$("#modrouteexpt_implement_warnings").html(htmlString);
		            					$("#modrouteexpt_implement_warnings").show();
		            				}
		     	            	   	var x = setInterval(function(){
		     	            	   		count++;
		     	            	   		console.log(count);	
		     	            	   		if(count == 5){
		     	            	   			$("#modrouteexpt_slides").slideShowWithFlowControl("nextSlide");
		     	            	   			$("#modrouteexpt_slides").slideShowWithFlowControl("showButtons");
		     	            	   			clearInterval(x);
		     	            	   		}
		     	            	   	},1000); 
		            				
		            			}
		            			else{
		            				alert("{{_('There was a problem implementing the modify routes by level experiment: ')}}" + results.msg);
		            			}
		            		})
		            		.fail(function(jqxhr,textStatus,error){
		            			alert("{{_('There was a failure implementing the modify routes by level experiment: ')}}" + jqxhr.responseText);
		            		});
	            	   return true;  
	               },
	               function(){
	            	   return true;
	               }
	              ],
	backFunctions:[
	               function(){return true;},
	               function(){
	            	   $("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   return true;
	               },
	               function(){return true;},
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
		$("#modrouteexpt_youhavechosen").html("{{_('You have chosen to modify routes that are ')}}" + routeParsed + ".");
		$("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
		var routeSel = $("#modrouteexpt_level_between_select").betweenSupplyChainLevelSelector("getSelected");
		$("#asneeded").show();
		if (routeSel.startsWith("loop_")){
			$("#asneeded").hide();
		}
		
	}
});

$("#modrouteexpt_level_originating_select").supplyChainLevelSelector({
	modelId:{{modelId}},
	routeOrig:true,
	type:'radioSelect',
	onChangeFunc: function(){
		var origLevel = $("#modrouteexpt_level_originating_select").supplyChainLevelSelector("getSelectedParsed");
		$("#modrouteexpt_youhavechosen").html("{{_('You have chosen to modify routes that originate at the ')}}" + origLevel + " suppply chain level");
		$("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");
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
//		});def 
//	}
//});

$("#modrouteexpt_change_vehicle_grid").typeExplorerGrid({
	modelId:{{modelId}},
	typeClass:'trucks',
	checkBoxes:false,
	groupingEnabled:false,
	namesOnly: false,
	createEnabled:true,
	createDialogTitle:"{{_('Create a New Mode of Transport for the Modified Routes')}}",
	width:$("#modrouteexpt_change_vehicle_grid").width()-2.5,
	onSelectFunction:function(){$("#modrouteexpt_slides").slideShowWithFlowControl("activateButton","next");}
});

$("#modrouteexpt_slides").slideShowWithFlowControl("hideSlide",3);
$("#modrouteexpt_slides").slideShowWithFlowControl("hideSlide",4);

//$("#modrouteexpt_level_between_level_select_div").change(function(){
//	var routeParsed = $("#modrouteexpt_level_between_level_select_div").betweenSupplyChainLevelSelector("getSelectedParsed");
//	$("#moderouteexpt_youhavechosen").html("{{_('You have chosen to modify routes ')}}" + routeParsed + ".");
//});

function createDataObject(){
	var freqOpt = '';
	if($("#modrouteexpt_operations_changefreq").is(":checked")){
		freqOpt = $("#modrouteexpt_freq_opts_div :radio:checked").attr("id");
	}
	var vehicleChange = '';
	if($("#modrouteexpt_operations_changevehicle").is(":checked")){
		vehicleChange = $("#modrouteexpt_change_vehicle_grid").typeExplorerGrid("getSelectedElements");
	}
	return {
		'levelOpt': $("#modrouteexpt_level_select_opts_div :radio:checked").attr("id"),
		'levelBetween': $("#modrouteexpt_level_between_select").betweenSupplyChainLevelSelector("getSelected"),
		'levelBetweenParsed': $("#modrouteexpt_level_between_select").betweenSupplyChainLevelSelector("getSelectedParsed"),
		'levelOrig': $("#modrouteexpt_level_originating_select").supplyChainLevelSelector("getSelectedParsed"),
		'changeFreq': $("#modrouteexpt_operations_changefreq").is(":checked"), 
		'changeVehicle': $("#modrouteexpt_operations_changevehicle").is(":checked"), 
		'freqOpt':freqOpt,
		'vehicleChange':vehicleChange[0] //there should only be one
	};

}
function createSummary(){
	// create data structure

	var dataObject = createDataObject();
	
	console.log(dataObject);
	$.ajax({
		url:{{rootPath}}+"json/route_by_level_summary",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	})
	.done(function(results){
		if(results.success){
			$("#modrouteexpt_summary_div").html(results.html);
		}
		else{
			alert("{{_('There was a problem getting the summary text for the modify routes by level experiment: ')}}" + results.msg);
		}
	})
	.fail(function(jqxhr,textStatus,error){
		alert("{{_('There was a failure in getting the summary text for the modify routes by level experiment: ')}}" + jqxhr.responseText);
	});
}

function implementExperiment(){
	var dataObject = createDataObject();
		
	console.log(dataObject);
	
	return $.ajax({
		url:{{rootPath}}+"json/route_by_level_experiment_implement",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	}).promise();
	
		
}
</script>
