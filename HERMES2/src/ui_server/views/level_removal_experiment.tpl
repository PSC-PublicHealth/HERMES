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
			{{_('Supply chains typically have a series of supply chain levels which are set up as intermediaries for which to ship products until finally the products arrive at locations where they will be given to patients.')}}
			{{_('The levels bring product closer to other locations and generally provide stability and security of stock for the products as they move through the supply chain.')}}
			{{_('However, there is a tradeoff, where it may be that a supply chain level is not necessary and actually makes the supply chain cost more, and a more efficient supply chain may be obtained by bypassing or removing a supply chain level and rerouting shipping routes directly.')}}
			{{_('This experiment will allow you to explore this tradeoff by giving you the ability to automatically remove a supply chain level from the supply chain.')}}
		</p>
		<p class='expt_text'>
			{{_('This experiment will take you through a series of screens that will allow you to specify a supply chain level to remove.')}}
			{{_('Additionally, you will need to specify some characteristics for the new routes that will be created as a result of the supply chain level being removed.')}}
			{{_('Once these options are specified, HERMES will automatically create a new model with the specified supply chain level removed.')}}
		</p>
		<br><hr><br>
		<p class='expt_text'>
		{{_('Below are some example publications where the removing of a supply chain level is explored with HERMES modeling: ')}}
		<ul class='proper_ul'>
			<li>
			<a href="https://www.ncbi.nlm.nih.gov/pubmed/26209835" target="blank">
				Lee BY, Connor DL, Wateska AR, Norman BA, Rajgopal J, Cakouros BE, Chen SI, Claypool EG, Haidari LA, Karir V, 
				Leonard J, Mueller LE, Paul P, Schmitz MM, Welling JS, Weng YT, Brown ST. 
				{{_('Landscaping the structures of GAVI country vaccine supply chains and testing the effects of radical redesign.')}}
				<em>Vaccine</em>. 2015 Aug 26;33(36):4451-8. doi: 10.1016/j.vaccine.2015.07.033. Epub 2015 Jul 23. PubMed PMID: 26209835.
			</a>
			</li>
			<li>
				<a href = "https://www.ncbi.nlm.nih.gov/pubmed/24814550" target="blank">
					Brown ST, Schreiber B, Cakouros BE, Wateska AR, Dicko HM, Connor DL, Jaillard P, Mvundura M, Norman BA, 
					Levin C, Rajgopal J, Avella M, Lebrun C, Claypool E, Paul P, Lee BY. 
					{{_("The benefits of redesigning Benin's vaccine supply chain.")}}
					<em>Vaccine</em>. 2014 Jul 7;32(32):4097-103. doi: 10.1016/j.vaccine.2014.04.090. Epub 2014 May 9. PubMed PMID: 24814550.
				</a>
			</li>
			<li>
			<a href="https://www.ncbi.nlm.nih.gov/pubmed/23602666" target="blank">
				Assi TM, Brown ST, Kone S, Norman BA, Djibo A, Connor DL, Wateska AR, Rajgopal
				J, Slayton RB, Lee BY. 
				
					{{_('Removing the regional level from the Niger vaccine supply chain.')}}
				<em>Vaccine</em>. 2013 Jun 10;31(26):2828-34. doi: 10.1016/j.vaccine.2013.04.011.
				Epub 2013 Apr 17. PubMed PMID: 23602666; PubMed Central PMCID: PMC3763189.
			</a>
			</li>
		</ul>
	</p>
<!--		<p class='expt_emph'> 
			{{_('Please press the "Next" button to continue.')}}
		</p>-->
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
		<div id='remlevexpt_implementing' style="display:none;">
			<div id='remlevexpt_implementing_text' class='expt_subtitle'>
				{{_("HERMES is implementing your experiment.")}}
			</div>
			<div id='implementing_gif'>
				<img src="{{rootPath}}static/images/kloader.gif">
			</div>
		</div>
	</div>
	<div id='remlevexpt_slide5' class='remlevexpt_slide'>
		<div id="remlevexpt_implement_warnings"></div>
		<div id="remlevexpt_final_links_div">
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
	            	   //implementExperiment();
	            	   $("#remlevexpt_implementing").fadeIn(1000);
	            	   $("#remlevexpt_slides").slideShowWithFlowControl("hideButton","back");
	            	   $("#remlevexpt_slides").slideShowWithFlowControl("hideButton","next");
	            	   implementExperiment()
		            		.done(function(results){
		            			if(results.success){	
		            				var count = 0;
		            				if(results.warnings != ''){
		            					htmlString = "<div class='expt_subtitle'>{{_('Note there were warnings with the experiment.')}}</div>";
		            					htmlString += "<div class='expt_text'>"+results.warnings+"</div>";
		            					$("#remlevexpt_implement_warnings").html(htmlString);
		            					$("#remlevexpt_implement_warnings").show();
		            				}
		     	            	   	var x = setInterval(function(){
		     	            	   		count++;
		     	            	   		console.log(count);
		     	            	   		if(count==5){
		     	            	   			$("#remlevexpt_slides").slideShowWithFlowControl("nextSlide");
		     	            	   			clearInterval(x);
		     	            	   		}
		     	            	   	},1000); 
		            				
		            			}
		            			else{
		            				alert("{{_('There was a problem implementing the level removal experiment: ')}}" + results.msg);
		            			}
		            		})
		            		.fail(function(jqxhr,textStatus,error){
		            			alert("{{_('There was a failure implementing the level removal experiment: ')}}" + jqxhr.responseText);
		            		});
	            	    
	            	
	            	   return true;
	               },
	               function(){
	            	   
	               }
	              ],
	backFunctions:[
	               function(){return true;},
	               function(){
	            	  // $("#remlevexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   //$("#remlevexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("destroy"); 
	            	   return true;
	               },
	               function(){return true;},
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

function createDataObject(){
	var dataObject = {
			'level':$("#remlevexpt_level_select").supplyChainLevelSelector("getSelected").replace("remlevexpt_level_select_select_id_radio_",""),
			'option':$("#remlevexpt_route_opts :radio:checked").attr("id"),
			'newRoute':'None'
		};
		
	if($("#remlevexpt_route_opts :radio:checked").attr("id") == "remlevexpt_custom"){
		dataObject['newRoute'] = $("#remlevexpt_route_spec_form").routeSpecifyFormWidget("getData");
	}
	return dataObject;	
	
}

function createSummary(){
	// prepare data
	var dataObject = createDataObject();
	
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

function implementExperiment(){
	var dataObject = createDataObject();
	
	console.log(dataObject);
	
	return $.ajax({
		url:{{rootPath}}+"json/level_removal_experiment_implement",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	}).promise();

		
}
</script>