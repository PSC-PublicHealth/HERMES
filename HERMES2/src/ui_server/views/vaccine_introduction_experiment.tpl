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
<h2>{{_("HERMES Experiment Generator: Vaccine Introductions")}}</h2>
<h3>
{{_("A series of screens will be given here to walk you through introducting new vaccines to the model.")}}
</h3>

<div id="addvacexpt_slides">
	<div id="addvacexpt_slide1" class='addvacexpt_slide'>
		<span class='expt_subtitle'>
			{{_('Description of the Vaccine Introduction Experiments')}}
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
	<div id="addvacexpt_slide3" class='addvacexpt_slide'>" +
		This will be the last slide.
	</div>
</div>

	
<script>

$("#addvacexpt_slides").slideShowWithFlowControl({
	width: 1200,
	height: 500,
	activateNext:true,
	
});

$("#addvacexpt_explorer_all_div").typeExplorerGrid({
	modelId: 1,
	typeClass:'vaccines',
	checkBoxes: true,
	expandAll: true,
	namesOnly: true,
	width:$("#addvacexpt_explorer_all_div").width(),
	title: "{{_('Choose vaccines that you would like to add to the model.')}}"
});

$("#addvacexpt_explorer_model_div").typeExplorerGrid({
	modelId: {{modelId}},
	typeClass:'vaccines',
	checkBoxes: false,
	selectEnabled: false,
	expandAll: true,
	groupingEnabled:false,
	namesOnly:true,
	searchEnabled: false,
	width:$("#addvacexpt_explorer_model_div").width(),
	deletable: true,
	title: "{{_('Vaccines Currently in the Model')}}"
});

var addVacBut = $("#addvacexpt_add_vacc_button").button({
	icons: {secondary:'ui-icon-arrowthick-1-e'}
});

addVacBut.click(function(e){
	e.preventDefault();
	console.log("Passing = " + $("#addvacexpt_explorer_all_div").typeExplorerGrid("getSelectedElements"));
	$("#addvacexpt_explorer_model_div").typeExplorerGrid("add",$("#addvacexpt_explorer_all_div").typeExplorerGrid("getSelectedElements"),1);
	$("#addvacexpt_slides").slideShowWithFlowControl("activateButton","next");
})

	
</script>