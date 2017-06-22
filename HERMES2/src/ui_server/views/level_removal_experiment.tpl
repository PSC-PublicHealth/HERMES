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
<script src="{{rootPath}}widgets/slideshow_widget.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/type_explorer_grid.js" type="text/javascript"></script>
<script src="{{rootPath}}widgets/supply_chain_level_selector_widget.js" type="text/javascript"></script>

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
	<div id="remlevexpt_slide2" class='remlevexpt_slide'>
		<div class="flex_cols">
			<div class="expt_txt">
				<p class='expt_text'>
					{{_('Please select from below the supply chain level that you would like to remove from the system.')}}
				</p>
			</div>
			<div id='remlevelexpt_level_select'></div>
			<div id='remlevelexpt_route_opts' class="expt_txt" style="display:none">
				<p class='expt_text'>
					{{_('Now you must select how the new routes between locations at the supply chain levels will be defined.  Please select from below one of the following options')}}
				</p>
				<p>
					<label for="remlevelexpt_fromabove" class='remlevelexpt_opts_label'>
							{{_('Use the charactistics of routes from the supply chain level above the level to be removed')}}
					</label>
					<input type='radio' name="remlevelexpt_route_options" id="remlevelexpt_fromabove">
				</p>
				<p>
					<label for="remlevelexpt_frombelow" class='remlevelexpt_opts_label'>
						{{_('Use the charactistics of routes from the supply chain level below the level to be removed')}}
					</label>
					<input type='radio' name="remlevelexpt_route_options" id="remlevelexpt_frombelow" checked>
				</p>
				<p>
					<label for="remlevelexpt_custom" class='remlevelexpt_opts_label'>
						{{_('Define your own route characteristics the supply chain level below the level to be removed')}}
					</label>
					<input type='radio' name="remlevelexpt_route_options" id="remlevelexpt_custom">
				</p>
			</div>
		</div>
	</div>
	<div id="remlevexpt_slide3" class='remlevexpt_slide'>
		<div>
			<p class='expt_text'>
			{{_('This Page will have further route defining')}}
		</div>
		<div id="remlevexpt_dose_per_person_grid_div"></div>
	</div>
	<div id="remlevexpt_slide4" class='remlevexpt_slide'>
		<div id='remlevexpt_summary_title'>
			<span class='expt_subtitle'>
				{{_('Remove a Supply Chain Level Experiment Summary')}}
			</span>
		</div>
		<div id="remlevexpt_summary_typegrid"></div>
	</div>
</div>

	
<script>
$("#remlevelexpt_route_opts :input").checkboxradio();

$("#remlevexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	nextFunctions:[
	               function(){
	            	   $("#remlevexpt_slides").slideShowWithFlowControl("deactivateButton","next");
	            	   return true;
	               },
	               function(){
	            	  return true;
	               },
	               function(){
	            	  return true;
	               },
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
	               function(){return true;}
	               ],
	doneFunctions:function(){},
	doneUrl: '{{rootPath}}model-open?modelId={{modelId}}'
	
});

$("#remlevelexpt_level_select").supplyChainLevelSelector({
	modelId: {{modelId}},
	excludeRootAndClients:true,
	type:'radioSelect',
	onChangeFunc:function(){
		$("#remlevelexpt_route_opts").fadeIn(200,function(){
				$("#remlevexpt_slides").slideShowWithFlowControl("activateButton","next");
		});
	}
});

function createSummary(){

//	$.ajax({
//		url:{{rootPath}} + "json/vaccine_introduction_summary",
//		data:{
//			modelId:{{modelId}},
//			//newvaccjson:JSON.stringify($("#addvacexpt_explorer_model_div").typeExplorerGrid("getNewTypes")),
//			newvaccdosejson:$("#addvacexpt_dose_per_person_grid_div").vaccineDosePerPersonGrid("resultJson")
//		}
//	})
//	.done(function(results){
//		if(results.success){
//			$("#addvacexpt_summary_typegrid").html(results.html)
//		}
//	});
};
	
//	})
//	var newVaccines = $("#addvacexpt_explorer_model_div").typeExplorerGrid("");
//	

	
</script>