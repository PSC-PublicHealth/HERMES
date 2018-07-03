%rebase outer_wrapper title_slogan=_('Add Transport Loops to Supply Chain'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,name=name
<!---

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
<script src="{{rootPath}}widgets/model_copy_dialog_widget.js" type="text/javascript"></script>

<style>
.addloopsexpt_level_select_opts_level {
	width: 940px;
	text-align: left;
}
</style>
<div id='addloopsexpt_copyModelDialog'></div>
<div id='addloopsexpt_testDialog'></div>

<h2>{{_("HERMES Experiment Generator: Add Transport Loops To Supply Chain")}}</h2>
<div id="addloopsexpt_slides">
	<div id="addloopsexpt_slide1" class='addloopsexpt_slide'>
		<span class='expt_subtitle'>
			{{_('Description of Adding Transport Loops Experiments')}}
		</span>
		<p class='expt_text'>
			{{_('Many supply chains utilize transport routes that start at one location and visit multiple locations before returning to their origin. This type of shipping route is known as a "loop."')}}
			{{_('Loops can be more efficient and provide more reliable shipping of products because they require maintaining a smaller fleet vehicles that can potentially travel less distance and provide a more regular shipping pattern.')}}
			{{_('However, transport loops may also require larger vehicles which may be more costly to operate and maintain and may incur per diem costs as the routes can become quite long.')}}
			{{_('Modeling can help you to understand these tradeoffs and where and when transport loops may make sense for your supply chain.')}}
		</p>
		<p class='expt_text'>
			{{_('This experiment will take you through a series of screens that will ask you between which supply chain levels you would like to create transport loops,')}}
			{{_(' the number of locations per transport loop, and the vehicle that you would like to use for each transport loop. After you give it your paramaters, HERMES will automatically create transport loops for the model based on the shortest distance. HERMES will estimate road distances by applying a modification factor to the straight-line distance for each route.')}}
		</p>
		<br><hr><br>
		<p class='expt_text'>
		{{_('Below are some example publications where the addition of transport loops in supply chains is explored with HERMES modeling: ')}}
		<ul class='proper_ul'>
			<li>
				<a href = "https://www.ncbi.nlm.nih.gov/pubmed/24814550" target="blank">
					Brown ST, Schreiber B, Cakouros BE, Wateska AR, Dicko HM, Connor DL, Jaillard P, Mvundura M, Norman BA, 
					Levin C, Rajgopal J, Avella M, Lebrun C, Claypool E, Paul P, Lee BY. 
					{{_("The benefits of redesigning Benin's vaccine supply chain.")}}
					<em>Vaccine</em>. 2014 Jul 7;32(32):4097-103. doi: 10.1016/j.vaccine.2014.04.090. Epub 2014 May 9. PubMed PMID: 24814550.
				</a>
			</li>
			<li>
				<a href = "https://www.ncbi.nlm.nih.gov/pubmed/26209835">
					Lee BY, Connor DL, Wateska AR, Norman BA, Rajgopal J, Cakouros BE, Chen SI,
					Claypool EG, Haidari LA, Karir V, Leonard J, Mueller LE, Paul P, Schmitz MM,
					Welling JS, Weng YT, Brown ST. 
					{{_('Landscaping the structures of GAVI country vaccine supply chains and testing the effects of radical redesign.')}}
					<em>Vaccine</em>. 2015 Aug
					26;33(36):4451-8. doi: 10.1016/j.vaccine.2015.07.033. Epub 2015 Jul 23. PubMed
					PMID: 26209835.
				</a>
			</li>
			<li>
				<a href = "https://www.ncbi.nlm.nih.gov/pubmed/27576077" target="blank">
				Lee BY, Haidari LA, Prosser W, Connor DL, Bechtel R, Dipuve A, Kassim H,
				Khanlawia B, Brown ST. 
				{{_('Re-designing the Mozambique vaccine supply chain to improve access to vaccines.')}}
				<em>Vaccine</em>. 2016 Sep 22;34(41):4998-5004. doi:
				10.1016/j.vaccine.2016.08.036. Epub 2016 Aug 26. PubMed PMID: 27576077.
				</a>
			</li>
		</ul>
	</div>
	<div id='addloopsexpt_slide2' class='addloopsexpt_slide'>
		<div class="flex_cols">
			<div id='addloopsexpt_level_start_div'>
				<div class="expt_text">
					<p class='expt_text'>
						{{_('Please select below the level you at which you would like to start the transport loops.')}}
					</p>
				</div>
				<div id='addloopsexpt_level_start'></div>
			</div>
			<div id='addloopsexpt_level_end_div' style='display:none;'>
				<div class="expt_text">
					<p class='expt_text'>
						{{_('Please select below the level(s) to include in the transport loops.')}}
					</p>
				</div>
				<div id='addloopsexpt_level_end'></div>
			</div>			
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
						<td>
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
		<div class='expt_text' id='addloopsexpt_summary_div'></div>
	</div>
	<div id='addloopsexpt_slide5' class='remlevexpt_slide'>
		<div id='addloopsexpt_implementing' style="display:none;">
			<div id='addloopsexpt_implementing_text' class='expt_subtitle'>
				{{_("HERMES is implementing your experiment.")}}
			</div>
			<div id='implementing_gif'>
				<img src="{{rootPath}}static/images/kloader.gif">
			</div>
		</div>
	</div>
	<div id='addloopsexpt_slide6' class='modrouteexpt_slide'>
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
					   $("#addloopsexpt_implementing").fadeIn(1000);
	            	   //$("#addloopsexpt_slides").slideShowWithFlowControl("hideButton","back");
	            	  //$("#addloopsexpt_slides").slideShowWithFlowControl("hideButton","next");
					   $("#addloopsexpt_slides").slideShowWithFlowControl("hideButtons");
	            	   implementExperiment()
		            		.done(function(results){
		            			if(results.success){	
		            				var count = 0;
		            				if(results.warnings != ''){
		            					htmlString = "<div class='expt_subtitle'>{{_('Note there were warnings with the experiment.')}}</div>";
		            					htmlString += "<div class='expt_text'>"+results.warnings+"</div>";
		            					$("#addloopsexpt_implement_warnings").html(htmlString);
		            					$("#addloopsexpt_implement_warnings").show();
		            				}
		     	            	   	var x = setInterval(function(){
		     	            	   		count++;
		     	            	   		console.log(count);	
		     	            	   		if(count == 1){
		     	            	   			$("#addloopsexpt_slides").slideShowWithFlowControl("nextSlide");
		     	            	   			$("#addloopsexpt_slides").slideShowWithFlowControl("showButtons");
		     	            	   			clearInterval(x);
		     	            	   		}
		     	            	   	},1000); 
		            				
		            			}
		            			else{
		            				alert("{{_('There was a problem implementing the adding transport loops experiment: ')}}" + results.msg);
		            			}
		            		})
		            		.fail(function(jqxhr,textStatus,error){
		            			alert("{{_('There was a failure implementing the adding transport loops experiment: ')}}" + jqxhr.responseText);
		            		});
	            	    
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
					},
					function(){
						   return true;
					}
	               ],            
	doneFunctions:function(){},
	doneUrl: '{{rootPath}}model-open?modelId={{modelId}}'
});

$("#addloopsexpt_level_start").supplyChainLevelSelector({
	modelId:{{modelId}},
	labelClass:'addloopsexpt_level_select_opts_level',
	excludeClients:true,
	type:'radioSelect',
	onChangeFunc: function(){
		
		//console.log("LEVLE = "+ $("#addloopsexpt_level_start").supplyChainLevelSelector("getSelectedParsed"));
		var divBackup = $("#addloopsexpt_level_end");
		var parentDiv = $("#addloopsexpt_level_end").parent();
		parentDiv.fadeOut(400,
				function(){
				$("#addloopsexpt_level_end").remove();
				parentDiv.append(divBackup);
				$("#addloopsexpt_level_end").supplyChainLevelSelector({
					modelId:{{modelId}},
					labelClass:'addloopsexpt_level_select_opts_level',
					belowLevel:$("#addloopsexpt_level_start").supplyChainLevelSelector("getSelectedParsed"),
					type:'radioSelect',
					addOptions:[{'option':'{{_("All Locations Below")}}','value':'all'}],
					onChangeFunc: function(){
						$("#addloopsexpt_slides").slideShowWithFlowControl("activateButton","next");
					}
				});
				parentDiv.fadeIn(400);
			});
		//$("#addloopsexpt_slides").slideShowWithFlowControl("activateButton","next");
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

function createDataObject(){
	return {
			'levelStart':$("#addloopsexpt_level_start").supplyChainLevelSelector("getSelectedParsed"),
			'levelEnd':$("#addloopsexpt_level_end").supplyChainLevelSelector("getSelectedParsed"),
			'maximumLocations':$('#number_per_loop_input').val(),
			'vehicleToUse': $('#vehicle_select_box').simpleTypeSelectField("value")
		};
}

function create_summary(){
	var dataObject = createDataObject();
	
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

function implementExperiment(){
	var dataObject = createDataObject();
	
	console.log(dataObject);
	
	return $.ajax({
		url:{{rootPath}}+"json/add_loops_experiment_implement",
		data:{
			modelId:{{modelId}},
			data:JSON.stringify(dataObject)
		}
	}).promise();

		
}
</script>
