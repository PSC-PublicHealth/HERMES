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
<h4>
{{_("Put descripion text here")}}
</h4>

<div id="addvacexpt_slides">
	<div id="addvacexpt_slide1" class='addvacexpt_slide'>
		Slide 1	
		<div id="addvacexpt_explorer_div"></div>
	</div>
	<div id="addvacexpt_slide2" class='addvacexpt_slide'>
		Slide 2
	</div>
	<div id="addvacexpt_slide3" class='addvacexpt_slide'>
		Slide 3
	</div>
</div>

	
<script>

$("#addvacexpt_slides").slideShowWithFlowControl({
	width: 800,
	height: 500,
	activateNext:true
});

$("#addvacexpt_explorer_div").typeExplorerGrid({
	modelId: 1,
	typeClass:'vaccines',
	checkBoxes: true
})
//var activeSlide = 0;
//var numSlides = $(".addvacexpt_slide").length;
////console.log("Active = "+ activeSlide + " num = "+numSlides);
//var slideWidth = $("#addvacexpt_slides").width();
//
//nextBut.click(function(e){
//	e.preventDefault();
//	activeSlide++;
//	$("#addvacexpt_slides").animate({scrollLeft:slideWidth*activeSlide},600);
//	//console.log("ActiveSlide = " + activeSlide);
//	if(activeSlide == numSlides - 1){
//		nextBut.prop('disabled',true)
//			.addClass('addvacexpt_button_disabled');
//	}
//	backBut.prop('disabled',false).removeClass('addvacexpt_button_disabled');
//});
//
//backBut.click(function(e){
//	e.preventDefault();
//	activeSlide--;
//	$("#addvacexpt_slides").animate({scrollLeft:slideWidth*activeSlide},600);
//	//console.log("ActiveSlide = " + activeSlide);
//	if(activeSlide == 0){
//		backBut.prop('disabled',true)
//		.addClass('addvacexpt_button_disabled');
//	}
//	nextBut.prop('disabled',false).removeClass('addvacexpt_button_disabled');
//});
//

	
</script>