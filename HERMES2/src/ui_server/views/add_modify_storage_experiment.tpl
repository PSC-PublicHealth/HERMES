%rebase outer_wrapper title_slogan=_('Add / Modify Storage Devices at a Supply Chain Level'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,name=name
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
.addstorexpt_slide {
	position:relative;
	display:inline-block;
	margin-right:-4px;
	white-space:normal;
	vertical-align:top;
	*display:inline;
	width:800px;
	height:500px;	
}

#addstorexpt_slides {
	position:relative;
	overflow:hidden;
	margin:0 0 0 0;
	width:800px;
	height:500px;
	white-space:nowrap;
}

#addstorexpt_buttons{
	margin: 10 10 10 10;
}

.addstorexpt_button_disabled{
	color: #999;
}
</style>
-->
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/widget_css/slideshow_widget.css" />
<script src="{{rootPath}}widgets/slideshow_widget.js" type="text/javascript"></script>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/type_editor_dialog_widget.css" />
<script src="{{rootPath}}widgets/type_editor_dialog_widget.js" type="text/javascript"></script>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/type_explorer_grid_widget.css" />
<script src="{{rootPath}}widgets/type_explorer_grid.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/supply_chain_level_selector_widget.js" type="text/javascript"></script>

<style>
.addstorexpt_opts_label {
	width: 940px;
	text-align: left;
}
</style>

<h2>{{_("HERMES Experiment Generator: Add/Modify Storage by Level")}}</h2>
<div id="addstorexpt_slides">
	<div id="addstorexpt_slide1" class='addstorexpt_slide'>
		<span class='expt_subtitle'>
			{{_('Description of Add/Modify Storage by Level  Experiments')}}
		</span>
		<p class='expt_text'>
			{{_('One of the central components of any supply chain is storage.')}}  
			{{_('The characteristics of storage devices such as net storage capacity, temperature of storage, and costs may have a significant impact of the performance and efficiency of the supply chain.')}}
			{{_('Modeling can help you decide what storage devices are appropriate for your supply chain at which supply chain level.')}}
		</p>
		<p class='expt_text'>
			{{_("This experiment will take you through a series of screens that will allow you to augment or swap out the storage devices for an entire supply chain level.")}}
			{{_("You will be asked which supply chain level you would like to alter, whether you would like to add devices or completely replace devices, or replace a certain device at that level.")}}
			{{_("Then you will be able to specify what compliment of storage devices you would like to use and then HERMES will automatically create a new model based on your input.")}}
		</p>	
		<br><hr><br>
		<p class='expt_text'>
		{{_('Below are some example publications where modify or adding storage to a supply chain is explored with HERMES modeling: ')}}
		<ul class='proper_ul'>
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
			<li>
				<a href = "https://www.ncbi.nlm.nih.gov/pubmed/24582633" target="blank">
					Brown ST, Lee BY. 
					{{_('Unless changes are made in Benin, multiple storage and transport bottlenecks may prevent vaccines from reaching the population.')}}
					<em>Vaccine.</em>
					2014 May 1;32(21):2518-9. doi: 10.1016/j.vaccine.2014.02.060. Epub 2014 Feb 28.
					PubMed PMID: 24582633.

				</a>
			</li>
		</ul>
	</div>
	<div id="addstorexpt_slide2" class='addstorexpt_slide'>
			
		<div class='flex_cols'>
			<div class='expt_txt'>
				<p class='expt_text'>
				{{_('Please select from below the supply chain level of which you would like to modify the storage.')}}
				</p>
			</div>
			<div id='addstorexpt_level_select'></div>
			<div id='addstorexpt_opts' class='expt_txt' style='display:none'>
				<p class='expt_text'>
					{{_('Now you must select from the options below to decide how to apply new storage devices to the level.  Would you like to ...')}}
				</p>
				<p>
				<label for="addstorexpt_replace" class='addstorexpt_opts_label'>
					{{_('Completely replace the existing storage at each location in the supply chain level with a new compliment of storage devices.')}}
				</label>
				<input type='radio' name="addstorexpt_options" id="addstorexpt_replace">
				</p>
				<p>
					<label for="addstorexpt_addition" class='addstorexpt_opts_label'>
						{{_('Add to the current compliment of storage devices at each location in the supply chain level.')}}
					</label>
					<input type='radio' name="addstorexpt_options" id="addstorexpt_addition" checked>
				</p>
				<p>
					<label for="addstorexpt_swap" class='addstorexpt_opts_label'>
						{{_('Replace a specific storage device with one or more other storage devices in a supply chain level.')}}
					</label>
					<input type='radio' name="addstorexpt_options" id="addstorexpt_swap">
				</p>
			</div>
		</div>	
	</div>
	<div id="addstorexpt_slide3" class='addstorexpt_slide'>
		<!-- This is the slide that you define the storage compliment on -->
		<div id="tri_container" class='tri_div_all'>
		<div id="addstorexpt_explorer_all_div" class="tri_div_left"></div>
		<div id="addstorexpt_add_div" class="tri_div_center">
			<div id="button_div" class="flex-center">
				<button id="addstorexpt_add_store_button" class="right_arrow_button">Add Device</button>
			</div>
		</div>
		<div id="addstorexpt_explorer_compliment_div" class="tri_div_right"></div>
	</div>
	</div>
	<div id="addstorexpt_slide4" class='addstorexpt_slide'>
		<!-- This slide is for choosing what storage devices to replace, you can only choose one to replace one device with -->
		<div id="tri_container" class='tri_div_all'>
			<div id="addstorexpt_explorer_from_div"  class="tri_sm_div_left"></div>
			<div id="addstorexpt_place_div"  class="tri_sm_div_center"></div>
			<div id="addstorexpt_explorer_to_div" class="tri_sm_div_right"></div>
		</div>
	</div>
	<div id="addstorexpt_slide5" class='addstorexpt_slide'>
		<div id="addstorexpt_summary_title">
			<span class='expt_subtitle'>
				{{_('Add / Modify Storage By Supply Chain Level Experiment Summary')}}
			</span>
		</div>
		<div id="addstorexpt_summary_text"></div>
		<div id="addstorexpt_click_next" class='expt_text'>
			{{_("Please click the Next button above to complete the experiment")}}
		</div>
	</div>
	<div id='addstorexpt_slide5' class='remlevexpt_slide'>
		<div id='addstorexpt_implementing' style="display:none;">
			<div id='addstorexpt_implementing_text' class='expt_subtitle'>
				{{_("HERMES is implementing your experiment.")}}
			</div>
			<div id='implementing_gif'>
				<img src="{{rootPath}}static/images/kloader.gif">
			</div>
		</div>
	</div>
	<div id="addstoreexpt_slide7" class='addstorept_slide'>
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

$("#addstorexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	nextFunctions:[
	               function(){
	            	   $("#addstorexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   return true;
	               },
	               function(){
	            	  return true;
	               },
	               function(){
	            	   createSummary();
	            	   return true;
	               },
	               function(){
	            	   createSummary();
	            	   return true;
	               },
	               function(){	            	   
	            	   $("#addstorexpt_implementing").fadeIn(1000);
	            	   //$("#addstorexpt_slides").slideShowWithFlowControl("hideButton","back");
	            	  //$("#addstorexpt_slides").slideShowWithFlowControl("hideButton","next");
					   $("#addstorexpt_slides").slideShowWithFlowControl("hideButtons");
	            	   implementExperiment()
		            		.done(function(results){
		            			if(results.success){	
		            				var count = 0;
		            				if(results.warnings != ''){
		            					htmlString = "<div class='expt_subtitle'>{{_('Note there were warnings with the experiment.')}}</div>";
		            					htmlString += "<div class='expt_text'>"+results.warnings+"</div>";
		            					$("#addstorexpt_implement_warnings").html(htmlString);
		            					$("#addstorsexpt_implement_warnings").show();
		            				}
		     	            	   	var x = setInterval(function(){
		     	            	   		count++;
		     	            	   		console.log(count);
		     	            	   		if(count == 5){	     	           
		     	            	   			$("#addstorexpt_slides").slideShowWithFlowControl("nextSlide");
		     	            	   			$("#addstorexpt_slides").slideShowWithFlowControl("showButtons");
		     	            	   			clearInterval(x);
		     	            	   		}
		     	            	   	},1000); 
		            				
		            			}
		            			else{
		            				alert("{{_('There was a problem implementing the modifying storage devices experiment: ')}}" + results.msg);
		            			}
		            		})
		            		.fail(function(jqxhr,textStatus,error){
		            			alert("{{_('There was a failure implementing the modifying storage devices experiment: ')}}" + jqxhr.responseText);
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

// Initially hide slide 3 for swap unless chosen
//$("#addstorexpt_slides").slideShowWithFlowControl("hideSlide",3);

$("#addstorexpt_opts :input").checkboxradio();

$("#addstorexpt_level_select").supplyChainLevelSelector({
	modelId: {{modelId}},
	excludeRootAndClients:false,
	type:'radioSelect',
	onChangeFunc:function(){
		$("#addstorexpt_opts").fadeIn(200,function(){
				$("#addstorexpt_slides").slideShowWithFlowControl("activateButton","next");
		});
	}
});

$("#addstorexpt_explorer_all_div").typeExplorerGrid({
	modelId: 1,
	typeClass:'fridges',
	checkBoxes: true,
	expandAll: true,
	namesOnly: false,
	createEnabled: false,
	groupingEnable:true,
	width:$("#addstorexpt_explorer_all_div").width()-2.5,
	title: "{{_('Choose storage devices that you would like to add to the compliment of devices.')}}"
});

var addStoreBut = $("#addstorexpt_add_store_button").button({
	icons: {secondary:'ui-icon-arrowthick-1-e'}
});

addStoreBut.click(function(e){
	e.preventDefault();
	var selected = $("#addstorexpt_explorer_all_div").typeExplorerGrid("getSelectedElements");
	if(selected.length == 0){
		alert("{{_('You have not selected any storage devices to add')}}");
	}
	else{
		$("#addstorexpt_explorer_compliment_div").typeExplorerGrid("add",selected,1);
		$("addstorexpt_slides").slideShowWithFlowControl("activateButton","next");
	}
});

$("#addstorexpt_explorer_compliment_div").typeExplorerGrid({
	modelId: {{modelId}},
	typeClass:'fridges',
	checkBoxes: false,
	selectEnabled: false,
	expandAll: true,
	groupingEnabled:false,
	createEnabled:true,
	searchEnabled: false,
	newOnly:true,
	colorNewRows:false,
	includeCount:true,
	namesOnly: true,
	addFunction: function(typName){
		$("#addstorexpt_explorer_all_div").typeExplorerGrid("removeGrid",typName);
	},
	width:$("#addstorexpt_explorer_compliment_div").width()-2.5,
	deletable: true,
	title: "{{_('Storage Devices Currently in the Model')}}"
});

$("#addstorexpt_explorer_from_div").typeExplorerGrid({
	modelId: {{modelId}},
	typeClass:'fridges',
	checkBoxes: false,
	selectEnabled: true,
	expandAll: true,
	groupingEnabled:false,
	createEnabled:false,
	searchEnabled: false,
	newOnly:false,
	width:$("#addstorexpt_explorer_from_div").width()-2.5,
	deletable: false,
	title: "{{_('Choose one storage device that you would like to replace at this level')}}"
});

$("#addstorexpt_explorer_to_div").typeExplorerGrid({
	modelId:1,
	typeClass:'fridges',
	selectEnabled:true,
	checkBoxes:false,
	expandAll:true,
	groupingEnabled:true,
	createEnabled:false,
	width:$("#addstorexpt_explorer_to_div").width()-2.5,
	title: "{{_('Choose one storage device that you would like to use to replace the old device.')}}"
});

$("#addstorexpt_slides").slideShowWithFlowControl("hideSlide",3);

$("#addstorexpt_opts").change(function(){
	var currentVal = $("#addstorexpt_opts :radio:checked").attr('id');
	if(currentVal == "addstorexpt_swap"){
		$("#addstorexpt_slides").slideShowWithFlowControl("hideSlide",2);
		$("#addstorexpt_slides").slideShowWithFlowControl("showSlide",3);
	}
	else{
		$("#addstorexpt_slides").slideShowWithFlowControl("hideSlide",3);
		$("#addstorexpt_slides").slideShowWithFlowControl("showSlide",2);
	}
});

function createDataObject(){
	return  {
			'level':$("#addstorexpt_level_select :radio:checked").attr("id").replace("addstorexpt_level_select_select_id_radio_",""),
			'option':$("#addstorexpt_opts :radio:checked").attr("id"),
			'addDevices':$("#addstorexpt_explorer_compliment_div").typeExplorerGrid("getNewTypes"),
			'deviceCounts':$("#addstorexpt_explorer_compliment_div").typeExplorerGrid("getDeviceCounts"),
			'fromDevice':$("#addstorexpt_explorer_from_div").typeExplorerGrid("getSelectedElements")[0],
			'toDevice':$("#addstorexpt_explorer_to_div").typeExplorerGrid("getSelectedElements")[0]
			};
}

function createSummary(){
	// prepare data
	
	var dataObject = createDataObject();
	console.log(dataObject);
	
	$.ajax({
		url:{{rootPath}}+"json/add_storage_summary",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	})
	.done(function(results){
		if(results.success){
			$("#addstorexpt_summary_text").html(results.html);
		}
		else{
			alert("{{_('There was a problem getting the summary text for the add storage by level experiment: ')}}" + results.msg);
		}
	})
	.fail(function(jqxhr,textStatus,error){
		alert("{{_('There was a failure in getting the summary text for the add storage by level experiment: ')}}" + jqxhr.responseText);
	});
}

function implementExperiment(){
	var dataObject = createDataObject();
		
	console.log(dataObject);
	
	return $.ajax({
		url:{{rootPath}}+"json/add_storage_experiment_implement",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	}).promise();
//	.done(function(results){
//		if(results.success){
//			
//		}
//		else{
//			alert("{{_('There was a problem implementing the add storage experiment: ')}}" + results.msg);
//		}
//	})
//	.fail(function(jqxhr,textStatus,error){
//		alert("{{_('There was a failure implementing the add storage experiment: ')}}" + jqxhr.responseText);
//	});
		
}
</script>