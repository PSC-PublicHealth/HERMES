%rebase outer_wrapper title_slogan=_('Create an Experiment'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,modelName=modelName

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

<script src="{{rootPath}}widgets/model_copy_dialog_widget.js" type="text/javascript"></script>

<style>
.expt_butt{
	width:200px;
	height:200px;
	font-size:large;
	font-style:bold;
    -moz-box-shadow: 3px 3px 4px #ccc;
    -webkit-box-shadow: 3px 3px 4px #ccc;
    box-shadow: 3px 3px 4px #ccc; /* For IE 8 */
    -ms-filter: "progid:DXImageTransform.Microsoft.Shadow(Strength=4, Direction=135, Color='#cccccc')"; /* For IE 5.5 - 7 */
    filter: progid:DXImageTransform.Microsoft.Shadow(Strength = 4, Direction = 135, Color = '#cccccc');
}

.expt_butt_image{
	width:150px;
}

.flex_double_row{
	display: -webkit-flex;
	display: flex;
	margin: 0;
	padding: 10px;
	flex-flow: column;
	width: 1000px;
	-webkit-align-items: center;
	align-items: center;
	-webkit-justify-content: center;
	justify-content: center;
}

.flex_row1{
	margin: 0 auto;
	padding: 15px;
	-webkit-flex: 1 1 50%;
	flex: 1 1 50%;
	order: 1;
}
	
.flex_row2{
	margin: 0 auto;
	padding: 15px;
	-webkit-flex: 1 1 50%;
	flex: 1 1 50%;
	order: 2;
}

.flex_row_container{
	display: -webkit-flex;
	display: flex;
	margin: 0;
	padding: 10px;
	flex-flow: row;
	-webkit-align-items: center;
	align-items: center;
	-webkit-justify-content: center;
	justify-content: center;
}

.flex_col1{
	margin: 0 auto;
	padding: 30px;
	-webkit-flex: 1 1 33%;
	flex: 1 1 33%;
	order: 1;
}
	
.flex_col2{
	margin: 0 auto;
	padding: 30px;
	-webkit-flex: 1 1 33%;
	flex: 1 1 33%;
	order: 2;
}

.flex_col3{
	margin: 0 auto;
	padding: 30px;
	-webkit-flex: 1 1 33%;
	flex: 1 1 33%;
	order: 3;
}

.flex_double_top{
	display:block;
	font-size:large;
}

</style>


<div id="expt_main_container" class="flex_double_row">
	<div id="expt_main_text" class="flex_double_top">
		Please choose an experiment that you would like to perform: 
	</div>
	<div id="expt_main_row1" class="flex_row1">
		<div id="expt_row1_container" class="flex_row_container">
			<div id="expt_row1_col1" class="flex_col1">
				<button class="expt_butt" id="vaccine_introduction_button">
					<img class="expt_butt_image" src="{{rootPath}}static/images/vacintro.png">{{_('Introduce New Vaccines')}}
				</button>
			</div>
		
			<div id="expt_row1_col2" class="flex_col2">
				<button class="expt_butt" id="level_removal_button">
					<img class="expt_butt_image" src="{{rootPath}}static/images/levrem.png">{{_('Remove a Supply Chain Level')}}
				</button>
			</div>
			
			<div id="expt_row1_col3" class="flex_col3">
				<button class="expt_butt" id="add_storage_button">
					<img class="expt_butt_image" src="{{rootPath}}static/images/addstorage.png">{{_('Add Storage Devices By Supply Chain Level')}}
				</button>
			</div>
		</div>				
	</div>
	
	<div id="expt_main_row2" class="flex_row2">
		<div id="expt_row2_container" class="flex_row_container">
			<div id="expt_row2_col1" class="flex_col1">
				<button class="expt_butt" id="route_by_level_button">
					<img class="expt_butt_image" src="{{rootPath}}static/images/addvehicle.png">{{_('Modify Transport Routes Between Supply Chain Levels')}}
				</button>
			</div>
			
			<div id="expt_row2_col2" class="flex_col2">
				<button class="expt_butt" id="change_demand_button">
					<img class="expt_butt_image" src="{{rootPath}}static/images/addpeople.png">{{_('Change Populations and Demand')}}
				</button>
			</div>
			
			<div id="expt_row2_col2" class="flex_col3">
				<button class="expt_butt" id="add_loops_button">
					<img class="expt_butt_image" src="{{rootPath}}static/images/toloops.png">{{_('Introduce Transport Loops')}}
				</button>
			</div>
		</div>
	</div>
</div>

<div id="expt_model_copy_dialog"></div>
<script>

var vacIntroBut = $("#vaccine_introduction_button").button()
var levRemBut = $("#level_removal_button").button();
var addStoreBut = $("#add_storage_button").button();
var addTransBut = $("#route_by_level_button").button();
var addPeopleBut = $("#change_demand_button").button();
var loopsBut = $("#add_loops_button").button();

$(".expt_butt").click(function(){
	experiment_post = $(this).attr('id').replace("_button","");
	$("#expt_model_copy_dialog").copyModelDialog({
		modelId:{{modelId}},
		name: "{{modelName}}",
		title: "{{_('Make a Copy of Model')}} {{modelName}}",
		text: "{{_('In order to proceed, you will need to make a copy of the model. Please provide a name for the newly copied model below.')}}",
		initCopyName:"{{modelName}}" + "_" + experiment_post,
		autoOpen: true,
		resultUrl: '{{rootPath}}'+experiment_post
	});
});


</script>