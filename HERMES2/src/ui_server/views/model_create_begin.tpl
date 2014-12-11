%rebase outer_wrapper title_slogan=_("Create A Model"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.css"/>
<script>

function makeNetworkJson(i,levelInfo){
	if (i == (Object.getOwnPropertyNames(levelInfo).length - 1)){
		return {'name':levelInfo[i].n,'count':levelInfo[i].c,'focus':levelInfo[i].f};
	}
	else {
		return {'name':levelInfo[i].n,'count':levelInfo[i].c,'focus':levelInfo[i].f,'children':[makeNetworkJson(i+1,levelInfo)]};
	}
}
// This function updates the network diagram
function updateNetworkDiagram(){
	var levelInfo = {};
	for(var i = 0; i < $("#model_create_nlevels_input").val(); ++i){
		if (typeof $("#model_create_levelname_"+(i+1)).val() == "undefined")
			break;
		//levelNames.push($("#model_create_levelname_"+(i+1)).val());
		var focus = false;
		if($("#model_create_levelname_"+(i+1)).is(':focus')){
				focus = true;
				console.log("This has focus.... damnit");
		}
		levelInfo[i] = {'n':$("#model_create_levelname_"+(i+1)).val(),'c':0,'f':focus};
		if (typeof $("#model_create_lcounts_"+(i+1)).val() == "undefined"){
			levelInfo[i].c = 1;
		}
		else{
			var focus = false;
			if($("#model_create_lcounts_"+(i+1)).is(':focus'))
				focus = true;
			levelInfo[i].c = $("#model_create_lcounts_"+(i+1)).val();
			levelInfo[i].f = focus;
			//levelCount.push($("#model_create_lcounts_"+(i+1)).val());
		}
		
	}
	
	console.log("Levels");
	for(var level in levelInfo){
		console.log(levelInfo[level].n);
	}
	if (Object.getOwnPropertyNames(levelInfo).length == 0){
		nlevels = $("#model_create_nlevels_input").val();
		for (var i=0;i<nlevels;i++){
			levelInfo[i] = {'n':'Level '+i,'c':1,'f':false};
		}
	}
	
	jsonNet = makeNetworkJson(0,levelInfo);
	$("#tree-layout-diagram").remove();
	$("#model_create_diagram").append($("<div id='tree-layout-diagram' name='tree-layout-diagram'/>"));
	$("#tree-layout-diagram").diagram({
	        hasChildrenColor: "steelblue",
	        noChildrenColor: "#ccc",
	        jsonData:jsonNet,
	        minWidth: 768,
	        minHeight: 775,
	        resizable: false,
	        scrollable: true,
	        trant: {
	             "title": "{{_('Model')}}",
	        }
	});
}
</script>

<h1>{{_('What is the supply chain structure of the \"{0}\" model?'.format(name))}}</h1>
<p>
<input type="text" name="model_create_model_name" id="model_create_model_name" style="display:none;"
%if defined('name'):
	value="{{name}}"
%end
></input>

<div name="model_create_ui_holder" id="model_create_ui_holder" style="width:1320px;border-style:single;">
<div name="model_create_holder" id="model_create_holder" style="position:relative; left:0; top:0; bottom:0; width:500px;float:left;border-style:double;">
	<div id="model_create_num_levels">
		<h4>
		  	<table>
			  	<tr>
		  			<td>
		  				<label for="model_create_nlevels_input">
		  					{{_('Please select the number of ')}}
		  					<b>
		  						<a href="#" 
		  							title="{{_('The number of storage locations that a vaccine or health product passes through from entering the supply chain to location in which it is used.')}}">
		  							{{_('levels')}}
		  						</a>
		  					</b> 
		  					{{_('in the \"{0}\" supply chain.'.format(name))}}
		  				</label>
		  			</td>
		  			<td>
		  			<div id="sub-div-nlevels">
		  				<select name="model_create_nlevels_input" id="model_create_nlevels_input">
		  					
%if defined('nlevels') and nlevels<=10:
%    for i in xrange(6):
%		 if i == 0: continue
%        if i+1 == nlevels:
			<option value={{i+1}} selected>{{i+1}}</option>
%        else:
  			<option value={{i+1}}>{{i+1}}</option>
%        end
%    end
%else:
%    nlevels = -1
%    for i in xrange(6):
%		 if i==0: continue
%        if i==3:
		  	<option value={{i+1}} selected>{{i+1}}</option>
%        else:
		  	<option value={{i+1}}>{{i+1}}</option>
%        end
%    end
%end
		  				</select>
					<!--<div style="position:absolute; left:0; right:0; top:0; bottom:0; cursor: pointer;display:none;" id="subsub"/>-->		
				</div> <!-- sub-div-nlevels -->
					</td>
		  		</tr>
		    </table>
		    </h4>
	</div> <!-- model_create_num_levels -->

	<div name="model_create_name_levels" id="model_create_name_levels" style="display:none;width:300px;">
		Replaced
	</div>
	<div name="model_create_number_places" id="model_create_number_places" style="display:none;">
		Putting some stuff here to test
	</div>
	<div id="nextbackbuttons">
		<table width=100%>
			<tr>
		    	<!--<td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>-->
		    	<td width 10%></td>
		    	<td></td>
		    	<td></td>
		    	<td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
		    </tr>
		</table>
	</div>
</div>
	<!-- Hierarchical Charts for Cost Summaries -->
<div id="model_create_diagram" name="model_create_diagram_container" style="position:relative; left:0; top:0; bottom:0; border-style:single;float:right;"/>
	<div id="tree-layout-diagram" name="tree-layout-diagram"/>
		<script>
		    updateNetworkDiagram();
		</script>
	</div>
</div>
</div>




<input id="selected-level-hidden" type="text" style="display:none"/>
<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_("The name of the model must not be blank.")}}</p>
</div>

<div id="reactivate-nlevels-modal" title={{_("Confirm Changing Number of Levels")}}>
  <p>{{_("Would you like to go back and change these values?")}}</p>
</div>

<!--<div id="reactivate-levnames-modal" title={{_("Confirm Changing Level Names")}}>
	<p>{{_("Would you like to go back and change these values?")}}</p>
</div>-->

<div id="level-change-dialog" title={{_("Changing Levels")}}>
	<p>'{{_("You are changing the number of levels in the system, this will result in the names of your levels and counts per level needing to be updated")}}'</p>
</div>
<div id="current-level-counter-div" style="display:none;">
	<input id="current-level-count-input" type="number" value={{nlevels}}>
</div>
<div id="current-level-counter2-div" style="display:none;">
<input id="current-level-count2-input" type="number" value={{nlevels}}>
</div>

<script>
var currentLevelNames = {}
%if defined('levelnames'):
	console.log('levelnames defined');
% 	for i in xrange(len(levelnames)):
		console.log({{i}});
		currentLevelNames[{{i}}] = "{{levelnames[i]}}";
%	end
%end

levelNameLength = 0
for (x in currentLevelNames){
	levelNameLength ++;
}
var levelNameOn = false;

var currentLevelCounts = {}
%if defined('levelcounts'):
	console.log('levelcounts defined');
%	for i in xrange(len(levelcounts)):
		currentLevelCounts[{{i}}] = {{levelcounts[i]}};
%	end
%end

levelCountLength = 0;
for (x in currentLevelCounts){
	levelCountLength++;
}
var levelCountOn = false;
var page_step = 0;

$(function() {
	$("#subsub").click(function(e){
		//e.preventDefault();
		console.log("Checking");
		if ($("#model_create_nlevels_input").is(':disabled')){
		//if( $("#model_create_nlevels_input").is(':disabled')){
			console.log("Disabled");
			//$("#reactivate-nlevels-modal").dialog("open");
		}
	});
	$("#dialog-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				$( this ).dialog( "close" );
        	}
        }
	});
	
	$("#reactivate-nlevels-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
		buttons: {
			{{_("Yes")}}: function(){
				$(this).dialog("close");
				$("#model_create_nlevels_input").prop('disabled',false);
				$("#subsub").hide();
				$("#model_create_nlevels_input").css("background-color","white");
				$("#model_create_nlevels_input").css("color","black");
				$("#model_create_num_levels").fadeTo("fast",1.0);
				levelNameOn = true;
				levelCountOn = true;
			},
			{{_("No")}}: function(){
				$(this).dialog(close);
			}
		}
	});

	$("#model_create_nlevels_input").change(function(){
		updateNetworkDiagram();
	});
	
	// The Next Button moving through the first time
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		if(page_step == 0){
			$("#current-level-count-input").val($("#model_create_nlevels_input").val());
			$("#current-level-count2-input").val($("#model_create_nlevels_input").val());
			$.ajax({
				url:'{{rootPath}}json/model-create-name-levels-form?nLevels='+$("#model_create_nlevels_input").val(),
				async: false,
				dataType: 'json',
				success: function(json) {
					var levelNames = [];
					var levelCount = [];
					$("#model_create_name_levels").html(json.htmlString);
					add_level_name_handlers();
					$("#model_create_nlevels_input").prop('disabled',true);
					$("#subsub").show();
					$("#model_create_nlevels_input").css("background-color","grey");
					$("#model_create_nlevels_input").css("color","white");
					$("#model_create_num_levels").fadeTo("slow",.50);
					$("#model_create_name_levels").fadeIn("slow");
					
				}
			});
			page_step = 1;
		}
		else if(page_step == 1){
			var levelNames = {};
			for (i=0;i<$("#model_create_nlevels_input").val();i++){
				levelNames[i] = $("#model_create_levelname_"+(i+1)).val();
			}
			$.ajax({
				url:'{{rootPath}}json/model-create-number-places-per-level-form',
				type:'post',
				data:levelNames,
				datatype:'json',
				success:function(data){
					$("#model_create_number_places").html(data.htmlString);
					updateNetworkDiagram();
					add_level_count_handlers();
					$("#model_create_name_levels").fadeTo(400,0.5);
					$("#model_create_name_levels :input").prop("disabled",true)
					$("#model_create_number_places").fadeIn("slow");
					$('#next_button').prop('value','{{_("Next Stage")}}')
					
				}
			});
			page_step = 2;
		}
		else if(page_step == 2){
			//updateNetworkDiagram();
			var modelName = $("#model_create_model_name").val();
			var modelNLevels = $("#model_create_nlevels_input").val();
			var modelLevelNames = validate_inputs(modelNLevels);
			if (modelName) {
				window.location = "{{rootPath}}model-create/next?name="+modelName+"&nlevels="+modelNLevels+modelLevelNames;
			}
		}
	});
	// IF there is data, this page needs to be populated and fully shown
	if (levelNameLength > 0){
		$.ajax({
			url:'{{rootPath}}json/model-create-name-levels-form?nLevels={{nlevels}}',
			async:false,
			dataType:'json',
			success: function(json){
				$("#model_create_name_levels").html(json.htmlString);
				$("#model_create_name_levels").show();
				for(levelNum in currentLevelNames){
					$("#model_create_levelname_" + (parseInt(levelNum)+1)).val(currentLevelNames[levelNum]);
					levelNameOn = true;
				}
			}
		});
		$.ajax({
			url:'{{rootPath}}json/model-create-number-places-per-level-form',
			type:'post',
			async:false,
			dataType:'json',
			data:currentLevelNames,
			success: function(json){
				$("#model_create_number_places").html(json.htmlString);
				$("#model_create_number_places").show();
				if(levelCountLength){
					for(levelNum in currentLevelCounts){
						$("#model_create_lcounts_" + (parseInt(levelNum)+1)).val(currentLevelCounts[levelNum]);	
					}			
				levelCountOn = true;
				}
				updateNetworkDiagram();
				add_level_name_handlers();
				add_level_count_handlers();
			}
		});
		$("#next_button").prop('value','{{_("Next Stage")}}');
		page_step = 2;
	}
	
	/// OK one last thing, if we change the number of levels we have to work that out.

	$("#level-change-dialog").dialog({
		resizable: false,
		modal: true,
		autoOpen:false,
		buttons:{
			Yes: function(){
				$.ajax({
					url:'{{rootPath}}json/model-create-name-levels-form?nLevels='+$("#model_create_nlevels_input").val(),
					async:false,
					dataType:'json',
					success: function(json){
						$("#model_create_name_levels").html(json.htmlString);
						$("#model_create_name_levels").show();
						for(var i=0; i < $("#model_create_nlevels_input").val();++i){
							levelNum = i;
							// if the new level value is less, cut out of here
							console.log("Level Num = " + levelNum);
							
							// take care if the new level value is higher
							if(levelNum < $("#current-level-count-input").val()){
								$("#model_create_levelname_" + (levelNum+1)).val(currentLevelNames[levelNum]);
							}
							else{
								$("#model_create_levelname_" + (levelNum+1)).val("NewLevel_"+(levelNum+1));
								currentLevelNames[levelNum] = "NewLevel_"+(levelNum+1);							
							}
							
						}
					
						levelNameOn = true;
						
						console.log($("#model_create_nlevels_input").val());
						console.log($("#current-level-count-input").val());
						for(var j=$("#model_create_nlevels_input").val();j<$("#current-level-count-input").val();j++){
							console.log("Deleting " + j);
							delete currentLevelNames[j];
						}
						
						for(levelName in currentLevelNames){
							console.log("New Levels " + levelName + " " + currentLevelNames[levelName]);
						}
						$("#current-level-count-input").val($("#model_create_nlevels_input").val());
						$.ajax({
							url:'{{rootPath}}json/model-create-number-places-per-level-form',
							type:'post',
							async:false,
							dataType:'json',
							data:currentLevelNames,
							success: function(json){
								$("#model_create_number_places").html(json.htmlString);
								$("#model_create_number_places").show();
								for (var i=0; i< $("#model_create_nlevels_input").val();++i){
									levelNum = i;
									if(levelNum < $("#current-level-count2-input").val()){
										$("#model_create_lcounts_" + (levelNum+1)).val(currentLevelCounts[levelNum]);
									}
									else{
										$("#model_create_lcounts_" + (levelNum+1)).val(1);
									}
								}
								
								levelCountOn=true;
								
								for(var j=$("#model_create_nlevels_input").val();j<$("#current-level-count2-input").val();j++){
									delete currentLevelCounts[j];
								}
								$("#current-level-count2-input").val($("#model_create_nlevels_input").val());

								for(levelName in currentLevelCounts){
									console.log("New Levels " + levelName + " " + currentLevelCounts[levelName]);
								}
							}
						});
						updateNetworkDiagram();
					}
				});
				
				$("#next_button").prop('value','{{_("Next Stage")}}');
				page_step = 2;
				$(this).dialog("close");
			},
			No: function(){
%if defined('nlevels'):
				$("#model_create_nlevels_input").val({{nlevels}});
%end
				$(this).dialog("close");
			}
		}
	});
	
	$("#model_create_nlevels_input").change(function(){
		if((levelNameOn) && (levelCountOn)){ 
			$("#level-change-dialog").dialog("open");
			//alert('{{_("You are changing the number of levels in the system, this will result in the names of your levels and counts per level needing to be updated")}}');
		}
	});
	
	function add_level_name_handlers(){
		$("#model_create_name_levels :input").change(function(){
			console.log(this);
			thisLevNum = parseInt($(this).prop('id').replace("model_create_levelname_",""));
			$("#tree-layout-diagram").diagram("change_level_name",thisLevNum-1,$(this).val());
		});
		$("#model_create_name_levels :input").focusin(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_levelname_",""));
			$("#tree-layout-diagram").diagram("bold_level",thisLevNum-1);
		});
		$("#model_create_name_levels :input").focusout(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_levelname_",""));
			$("#tree-layout-diagram").diagram("unbold_level",thisLevNum-1);
		});
	};
	
	function add_level_count_handlers(){
		$("#model_create_number_places :input").change(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_lcounts_",""));
			var locString = "Location";
			if($(this).val() > 1) locString = "Locations";
			$("#tree-layout-diagram").diagram("change_location_text",thisLevNum-1,$(this).val() + " " +locString);
		});
		$("#model_create_number_places :input").focusin(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_lcounts_",""));
			$("#tree-layout-diagram").diagram("bold_level",thisLevNum-1);
		});
		$("#model_create_number_places :input").focusout(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_lcounts_",""));
			$("#tree-layout-diagram").diagram("unbold_level",thisLevNum-1);
		});
	};
	
	function validate_inputs(nlevels) {
		var parms = "";
		var valsOK = true;
		var first = false;
		for (var i=0; i<nlevels; i++) {
		   var s = "model_create_levelname_"+(i+1);
		   var n = "model_create_lcounts_"+(i+1);
		   //have to convert the names that are used here, probably should make them smaller
		   // to prevent restful overrun
		   var sval = $("#"+s).val();
		   var nval = $("#"+n).val();
		   if (sval) {
		       if (first) {
		           parms = parms + s + "=" + sval + "&" + n + "=" + nval;
		           first = false;
		       }
		       else {
		           parms = parms + "&" + s + "=" + sval + "&" + n + "=" + nval;
		       }
		   }
		   else {
		       valsOK = false;
		   }
		}
		if (!valsOK) { parms = null; }
		return parms;
	}
});
</script>
