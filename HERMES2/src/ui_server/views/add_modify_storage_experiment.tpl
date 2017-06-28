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
	<div id="addstoreexpt_slide6" class='addstorept_slide'>
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
							{{_("Further Modify the Storage Device Inventory of  Each Supply Chain Location")}}
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

function createSummary(){
	// prepare data
	var dataObject = {
			'level':$("#addstorexpt_level_select :radio:checked").attr("id").replace("addstorexpt_level_select_select_id_radio_",""),
			'option':$("#addstorexpt_opts :radio:checked").attr("id"),
			'addDevices':$("#addstorexpt_explorer_compliment_div").typeExplorerGrid("getNewTypes"),
			'deviceCounts':$("#addstorexpt_explorer_compliment_div").typeExplorerGrid("getDeviceCounts"),
			'fromDevice':$("#addstorexpt_explorer_from_div").typeExplorerGrid("getSelectedElements"),
			'toDevice':$("#addstorexpt_explorer_to_div").typeExplorerGrid("getSelectedElements")
			};
	
	console.log(dataObject);
	
	$.ajax({
		url:{{rootPath}}+"json/add_storage_summary",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	})
	.done(function(results){
		$("#addstorexpt_summary_text").html(results.html);
	});
}

	
</script>