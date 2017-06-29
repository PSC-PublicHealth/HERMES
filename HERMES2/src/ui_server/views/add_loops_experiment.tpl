%rebase outer_wrapper title_slogan=_('Add Transport Loops to Supply Chain'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,name=name
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

<h2>{{_("HERMES Experiment Generator: Add Transport Loops To Supply Chain")}}</h2>
<div id="addloopsexpt_slides">
	<div id="addloopsexpt_slide1" class='addloopsexpt_slide'>
		<span class='expt_subtitle'>
			{{_('Description of Adding Transport Loops Experiments')}}
		</span>
		<p class='expt_text'>
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
			Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,Leila and jenn,
		</p>
		<p class='expt_text'>
			{{_('This experiment will take you through a series of screens that will ask you between which supply chain levels you would like to create transport loops between,')}}
			{{_(' the number of locations per transport loop, and the vehicle that you would like to use for each transport loop and then HERMES will automatically create transport loops for the model based on the shortest distance.')}}
		</p>	
		<p class='expt_emph'> 
			{{_('Please press the "Next" button to continue.')}}
		</p>
	</div>
	<div id='addloopsexpt_slide2' class='addloopsexpt_slide'>
		<div class="flex_cols">
			<div class="expt_txt">
				<p class='expt_text'>
					{{_('Please select below the two levels between which you would like to produce transport loops between.')}}
				</p>
			</div>
			<div id='addloopsexpt_between_level_select'></div>
		</div>
	</div>
	<div id='addloopsexpt_slide3' class='addloopsexpt_slide'>
		<div class='flex_cols'>
			<div class='expt_txt'>
				<p class='expt_text'>
					{{_('Please specify the parameters for the transport loops below:')}}
				</p>
			</div>
			<div>
				<table>
					<tr class="loop_table_item">
						<td class='expt_text'>
							{{_("Maximum Number of Locations Per Transport Loop")}}
						</td>
						<td class='expt_text'>
							<input type="number" id="number_per_loop_input" value=3></input>
						</td>
					</tr>
					<tr class="loop_table_item">
						<td class='expt_text'>
							{{_("Tranport Component to be Used for Loops")}}
						</td>
						<td class='expt_text'>
							<div id="vehicle_select_box"></div>
						</td>
					</tr>
				</table>
			</div>
		</div>
	</div>
	<div id='addloopsexpt_slide4' class='addloopsexpt_slide'>
		<div id='addloopsexpt_summary_title'>
			<span class='expt_subtitle'>
				{{_('Add Transport Loops Experiment Summary')}}
			</span>
		</div>
		<div id='addloopsexpt_summary_div'></div>
		<div id='addloopsexpt_click_next" class='expt_text'>
			{{_("Please click the Next button above to complete the experiment")}}
		</div>
	</div>
	<div id='addloopsexpt_slide5' class='modrouteexpt_slide'>
		<div id="addloopsexpt_final_links_div">	
			<span class='expt_subtitle'>
				{{_('Below are some additional actions that you may want to perform on your newly modified model:')}}
			</span>
			<span class="expt_text">
				<ul class="proper_ul">
					<li>
						<a href="{{rootPath}}model-edit-population-tabular?modelId={{modelId}}">
							{{_('Update the Number of People Served by Each Supply Chain Location')}}<br>
						</a>
					</li>
					<li>
						<a href="{{rootPath}}model-edit-store-inventory-tabular?modelId={{modelId}}">
							{{_("Further Modify the Storage Device Inventory of Each Supply Chain Location")}}<br>
						</a>
					</li>
					<li>
						<a href="{{rootPath}}model-edit-structure?id={{modelId}}">
							{{_("Open the New Model in the HERMES Advanced Editor to Make Further Changes")}}<br>
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
$("#addloopsexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	nextFunctions:[
				   function(){  
					   $("#addloopsexpt_slides").slideShowWithFlowControl("deactivateButton","next");
					   return true;
				   },
				   function(){
					   //$("#addloopsexpt_slides").slideShowWithFlowControl("deactivateButton","next");
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
					function(){
						   return true;
					},
					function(){
						   return true;
					},
					function(){
						   return true;
					},
					function(){
						   return true;
					}
	               ],            
	doneFunctions:function(){},
	doneUrl: '{{rootPath}}model-open?modelId={{modelId}}'
});

$("#addloopsexpt_between_level_select").betweenSupplyChainLevelSelector({
	modelId:{{modelId}},
	labelClass:'addloopsexpt_level_select_opts_level',
	includeLoops:false,
	onChangeFunc: function(){
		$("#addloopsexpt_slides").slideShowWithFlowControl("activateButton","next");
	}
});

$("#vehicle_select_box").hrmWidget({
	widget:'simpleTypeSelectField',
	invType:'trucks',
	modelId:{{modelId}},
	selected:'',
	width:200,
	persistent:true
});

function create_summary(){
	var dataObject = {'levelsBetween':$("#addloopsexpt_between_level_select").betweenSupplyChainLevelSelector("getSelected"),
					  'levelsBetweenParsed':$("#addloopsexpt_between_level_select").betweenSupplyChainLevelSelector("getSelectedParsed"),
					  'maximumLocations':$('#number_per_loop_input').val(),
					  'vehicleToUse': $('#vehicle_select_box').simpleTypeSelectField("value")
					};
	
	console.log(dataObject);
	
	$.ajax({
		url:{{rootPath}}+"json/add_loops_summary",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	})
	.done(function(results){
		if(results.success){
			$("#addloopsexpt_summary_div").html(results.html);
		}
		else{
			alert("{{_('There was a problem getting the summary text for the add loops experiment: ')}}" + results.msg);
		}
	})
	.fail(function(jqxhr,textStatus,error){
		alert("{{_('There was a failure in getting the summary text for the add loops experiment: ')}}" + jqxhr.responseText);
	});
	
}
</script>