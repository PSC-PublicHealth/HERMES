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
.addvacexpt_slide {
	position:relative;
	display:inline-block;
	margin-right:-4px;
	white-space:normal;
	vertical-align:top;
	*display:inline;
	width:800px;
	height:500px;	
}

#addvacexpt_slides {
	position:relative;
	overflow:hidden;
	margin:0 0 0 0;
	width:800px;
	height:500px;
	white-space:nowrap;
}

#addvacexpt_buttons{
	margin: 10 10 10 10;
}

.addvacexpt_button_disabled{
	color: #999;
}

</style>
-->
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/widget_css/slideshow_widget.css" /> 
<script src="{{rootPath}}widgets/slideshow_widget.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/type_explorer_grid.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/type_editor_dialog_widget.js" type="text/javascript"></script>
<link rel="stylesheet" href="{{rootPath}}static/widget_css/type_explorer_grid_widget.css" />
<script src="{{rootPath}}widgets/vaccine_dose_per_person_grid.js" type="text/javascript"></script>


<h2>{{_("HERMES Experiment Generator: Vaccine Introductions")}}</h2>
<div id="addvacexpt_slides">
	<div id="addvacexpt_slide1" class='addvacexpt_slide'>
		<span class='expt_subtitle'>
			{{_('Description of the Vaccine Introduction Experiments')}}
		</span>
		<p class='expt_text'>
			{{_('Many countries stuggle with having their current supply chains delivering new vaccines that have the potential to prevent illness and save lives.')}}
			{{_("If the supply chain has not been planned with adequate storage and transport capacity to handle the increased amounts and volume that result from adding vaccines to the country's schedule, performance and efficiency may suffer.")}}
			{{_("Modeling can help you plan for a vaccine introduction by helping choose an appropriate presentation, vaccine dose schedule, and determine the increases in storage and transport capacity that are needed.")}}
		</p>
		<p class='expt_text'>
			{{_('This experiment will take you through a series of screens that will allow you define new vaccines that you would like to introduce into the supply chain and the appropriate vaccine dose schedule for the new vaccines.')}}
			{{_('Once specified, HERMES will automatically create a new model that will allow you to run simulations to assess the impact of the additional vaccines.')}}
		</p>	
		<br><hr><br>
		<p class='expt_text'>
		{{_('Below are some example publications where the introduction or one or more vaccines to the supply chain is explored with HERMES modeling: ')}}
		<ul class='proper_ul'>
			<li>
				<a href="https://www.ncbi.nlm.nih.gov/pubmed/21940923" target="blank">
					 Lee BY, Assi TM, Rajgopal J, Norman BA, Chen SI, Brown ST, Slayton RB, Kone S, Kenea H, Welling JS, 
					 Connor DL, Wateska AR, Jana A, Wiringa AE, Van Panhuis WG, Burke DS. 
					 {{_('Impact of introducing the pneumococcal and rotavirus vaccines into the routine immunization program in Niger.')}}
					 <em>Am J Public Health.</em> 2012
					 Feb;102(2):269-76. doi: 10.2105/AJPH.2011.300218. Epub 2011 Nov 28. PubMed PMID: 
					 21940923; PubMed Central PMCID: PMC3386610.
				 </a>
			</li>
			<li>
				<a href = "https://www.ncbi.nlm.nih.gov/pubmed/21931805" target="blank">
					Lee BY, Assi TM, Rookkapan K, Wateska AR, Rajgopal J, Sornsrivichai V, Chen
					SI, Brown ST, Welling J, Norman BA, Connor DL, Bailey RR, Jana A, Van Panhuis WG,
					Burke DS. 
					{{_("Maintaining vaccine delivery following the introduction of the rotavirus and pneumococcal vaccines in Thailand.")}}
					<em>PLoS One.</em> 2011;6(9):e24673. doi:
					10.1371/journal.pone.0024673. Epub 2011 Sep 13. PubMed PMID: 21931805; PubMed
					Central PMCID: PMC3172252.
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
		</ul>
	</p>
	</div>
	<div id="addvacexpt_slide2" class='addvacexpt_slide'>
		<div class="tri_div_top" class='expt_txt'>
			<p class='expt_text'>
				{{_('Please select the vaccines that you would like to introduce into the system by clicking on the checkboxes next to the vaccine name.')}}
				{{_('You can search through the vaccines by clicking the search button at the bottom of the screen.')}}
			</p>
		</div>
		<div id="tri_container" class='tri_div_all'>
			<div id="addvacexpt_explorer_all_div" class="tri_div_left"></div>
			<div id="addvacexpt_add_div" class="tri_div_center">
				<div id="button_div" class="flex-center">
					<button id="addvacexpt_add_vacc_button" class="right_arrow_button">Add Vaccine</button>
				</div>
			</div>
			<div id="addvacexpt_explorer_model_div" class="tri_div_right"></div>
		</div>
	</div>
	<div id="addvacexpt_slide3" class='addvacexpt_slide'>
		<div>
			<p class='expt_text'>
			{{_('Now, for the new vaccines, please specify the dose schedule that you would like to have for each new vaccine that you are introducing.')}}
			{{_('You will need to specify in the table below at least one dose be administered for each vaccine.')}}
		</div>
		<div id="addvacexpt_dose_per_person_grid_div"></div>
	</div>
	<div id="addvacexpt_slide4" class='addvacexpt_slide'>
		<div id='addvacexpt_summary_title'>
			<span class='expt_subtitle'>
				{{_('Vaccine Introduction Experiment Summary')}}
			</span>
		</div>
		<div id="addvacexpt_summary_typegrid"></div>
	</div>
</div>

<script>

$("#addvacexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 600,
	activateNext:true,
	nextFunctions:[
	               function(){
	            	   var newTypes = $("#addvacexpt_explorer_model_div").typeExplorerGrid("getNewTypes");
	            	   if(newTypes.length == 0){
	            		   $("#addvacexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   }
	            	   return true;
	               },
	               function(){
	            	  $("#addvacexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	  $("#addvacexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid({
	            		  modelId: {{modelId}},
	            		  filterList: function(){ return JSON.stringify($("#addvacexpt_explorer_model_div").typeExplorerGrid("getNewTypes"))},
	            		  onSaveFunc: function(){$("#addvacexpt_slides").slideShowWithFlowControl("activateButton","next");}
	            	  });
	            	  return true;
	               },
	               function(){
	            	   if($("#addvacexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("validate")){
	            		   createSummary();
	            		   return true;
	            	   }
	            	   else{
	            		   return false;
	            	   }
	               }
	              ],
	backFunctions:[
	               function(){return true;},
	               function(){
	            	   $("#addvacexpt_slides").slideShowWithFlowControl("activateButton","next");
	            	   $("#addvacexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("destroy"); 
	            	   return true;
	               },
	               function(){return true;}
	               ],
	doneFunctions:function(){},
	doneUrl: '{{rootPath}}model-open?modelId={{modelId}}'
	
});

$("#addvacexpt_explorer_all_div").typeExplorerGrid({
	modelId: 1,
	typeClass:'vaccines',
	checkBoxes: true,
	expandAll: true,
	namesOnly: true,
	createEnabled:false,
	excludeTypesFromModel: {{modelId}},
	width:$("#addvacexpt_explorer_all_div").width(),
	title: "{{_('Choose vaccines that you would like to add to the model.')}}"
});

$("#addvacexpt_explorer_model_div").typeExplorerGrid({
	modelId: {{modelId}},
	typeClass:'vaccines',
	checkBoxes: false,
	selectEnabled: false,
	createEnabled: true,
	expandAll: true,
	groupingEnabled:false,
	namesOnly:true,
	searchEnabled: false,
	addFunction: function(typName){
		$("#addvacexpt_explorer_all_div").typeExplorerGrid("removeGrid",typName);
		$("#addvacexpt_slides").slideShowWithFlowControl("activateButton","next");
	},
	createFunction: function(typName){
		$("#addvacexpt_slides").slideShowWithFlowControl("activateButton","next");
	},
	width:$("#addvacexpt_explorer_model_div").width(),
	deletable: true,
	title: "{{_('Vaccines Currently in the Model')}}"
});


var addVacBut = $("#addvacexpt_add_vacc_button").button({
	icons: {secondary:'ui-icon-arrowthick-1-e'}
});

addVacBut.click(function(e){
	e.preventDefault();
	var selected = $("#addvacexpt_explorer_all_div").typeExplorerGrid("getSelectedElements");
	if(selected.length == 0){
		alert("{{_('You have not selected any vaccines to add')}}");
	}
	else{
		$("#addvacexpt_explorer_model_div").typeExplorerGrid("add",$("#addvacexpt_explorer_all_div").typeExplorerGrid("getSelectedElements"),1);
		$("#addvacexpt_slides").slideShowWithFlowControl("activateButton","next");
	}
});


function createSummary(){
	
	$.ajax({
		url:{{rootPath}} + "json/vaccine_introduction_summary",
		data:{
			modelId:{{modelId}},
			//newvaccjson:JSON.stringify($("#addvacexpt_explorer_model_div").typeExplorerGrid("getNewTypes")),
			newvaccdosejson:$("#addvacexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("resultJson")
		}
	})
	.done(function(results){
		if(results.success){
			$("#addvacexpt_summary_typegrid").html(results.html)
		}
	});
};
	
//	})
//	var newVaccines = $("#addvacexpt_explorer_model_div").typeExplorerGrid("");
//	

	
</script>
