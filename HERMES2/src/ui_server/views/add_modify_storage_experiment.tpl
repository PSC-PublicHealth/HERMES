%rebase outer_wrapper title_slogan=_('Vaccine Introduction'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,name=name
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
		We are on Slide 3..
	</div>
	<div id="addstorexpt_slide4" class='addstorexpt_slide'>
		We are on Slide 4..
	</div>
</div>

	
<script>

$("#addstorexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	nextFunctions:[
	               function(){
	            	   //$("#addstorexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   return true;
	               },
	               function(){
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
	               function(){return true;}
	               ],
	doneFunctions:function(){},
	doneUrl: '{{rootPath}}model-open?modelId={{modelId}}'
});

$("#addstorexpt_slides").slideShowWithFlowControl("hideSlide",1);
$("#addstorexpt_slides").slideShowWithFlowControl("hideSlide",2);
$("#addstorexpt_slides").slideShowWithFlowControl("showSlide",1);


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

//$("#addstorexpt_explorer_all_div").typeExplorerGrid({
//	modelId: 1,
//	typeClass:'vaccines',
//	checkBoxes: true,
//	expandAll: true,
//	namesOnly: true,
//	excludeTypesFromModel: {{modelId}},
//	width:$("#addstorexpt_explorer_all_div").width(),
//	title: "{{_('Choose vaccines that you would like to add to the model.')}}"
//});
//
//$("#addstorexpt_explorer_model_div").typeExplorerGrid({
//	modelId: {{modelId}},
//	typeClass:'vaccines',
//	checkBoxes: false,
//	selectEnabled: false,
//	expandAll: true,
//	groupingEnabled:false,
//	namesOnly:true,
//	searchEnabled: false,
//	addFunction: function(typName){
//		console.log("HERE " + typName);
//		$("#addstorexpt_explorer_all_div").typeExplorerGrid("removeGrid",typName);
//	},
//	width:$("#addstorexpt_explorer_model_div").width(),
//	deletable: true,
//	title: "{{_('Vaccines Currently in the Model')}}"
//});
//
//
//var addVacBut = $("#addstorexpt_add_vacc_button").button({
//	icons: {secondary:'ui-icon-arrowthick-1-e'}
//});
//
//addVacBut.click(function(e){
//	e.preventDefault();
//	var selected = $("#addstorexpt_explorer_all_div").typeExplorerGrid("getSelectedElements");
//	if(selected.length == 0){
//		alert("{{_('You have not selected any vaccines to add')}}");
//	}
//	else{
//		$("#addstorexpt_explorer_model_div").typeExplorerGrid("add",$("#addstorexpt_explorer_all_div").typeExplorerGrid("getSelectedElements"),1);
//		$("#addstorexpt_slides").slideShowWithFlowControl("activateButton","next");
//	}
//});
//
//
//function createSummary(){
//	
//	$.ajax({
//		url:{{rootPath}} + "json/vaccine_introduction_summary",
//		data:{
//			modelId:{{modelId}},
//			//newvaccjson:JSON.stringify($("#addstorexpt_explorer_model_div").typeExplorerGrid("getNewTypes")),
//			newvaccdosejson:$("#addstorexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("resultJson")
//		}
//	})
//	.done(function(results){
//		if(results.success){
//			$("#addstorexpt_summary_typegrid").html(results.html)
//		}
//	});
//};
//	
////	})
////	var newVaccines = $("#addstorexpt_explorer_model_div").typeExplorerGrid("");
////	

	
</script>