%rebase outer_wrapper title_slogan=_("Create A Model"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer


<h1>{{_('How many levels in the {0} supply chain?'.format(name))}}</h1>
<p>
<div id="model_create_num_levels">
<form>
  	<table>
<!--	  	<tr>
  			<td><label for="model_create_model_name">{{_('Name Your Model')}}</label></td>
  			<td>-->
  			<input type="text" name="model_create_model_name" id="model_create_model_name" style='display:none;'
%if defined('name'):
value={{name}}
%end
  			>
  			<!--</td>
  		</tr>-->
	  	<tr>
  			<td><label for="model_create_nlevels_input">{{_('Please select the number of levels in the {0} supply chain.'.format(name))}}</label></td>
  			<td><select name="model_create_nlevels_input" id="model_create_nlevels_input">
%if defined('nlevels') and nlevels<=6:
%    for i in xrange(6):
%        if i+1 == nlevels:
  			<option value={{i+1}} selected>{{i+1}}</option>
%        else:
  			<option value={{i+1}}>{{i+1}}</option>
%        end
%    end
%else:
%    nlevels = -1
%    for i in xrange(6):
%        if i==3:
  			<option value={{i+1}} selected>{{i+1}}</option>
%        else:
  			<option value={{i+1}}>{{i+1}}</option>
%        end
%    end
%end
  			</select></td>
  		</tr>
    </table>
</div>
<div name="model_create_holder" id="model_create_holder" style="width:800px;">
<div name="model_create_name_levels" id="model_create_name_levels" style="display:none;width:300px;float:left"></div>
<div name="model_create_number_places" id="model_create_number_places" style="display:none;">Putting some stuff here to test</div>
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
</form>
</div>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_("The name of the model must not be blank.")}}</p>
</div>

<div id="level-change-dialog" title={{_("Changing Levels")}}>
	<p>This is a dialog for confirming changing levels</p>
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
//$(function() {
//	var btn = $("#back_button");
//	btn.button();
//	btn.click( function() {
//		$.ajax({
//			url:'{{rootPath}}json/model-create-name-levels-form?nLevels='+$("#model_create_nlevels_input").val(),
//			async: false,
//			dataType: 'json',
//			success: function(json) {
//				$("#model_create_name_levels").html(json.htmlString);
//				$("#model_create_nlevels_input").attr('disabled',true);
//				$("#model_create_nlevels_input").css("background-color","grey");
//				$("#model_create_nlevels_input").css("color","white");
//				$("#model_create_num_levels").fadeTo("slow",.50);
//				$("#model_create_name_levels").fadeIn("slow");
//				
//			}
//		});
//		
//	});
//});


$(function() {
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
					console.log(parseInt(levelNum)+1);
					console.log(currentLevelNames[levelNum])
					console.log($("#model_create_levelname_"+(parseInt(levelNum)+1)).val());
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
						//console.log(parseInt(levelNum)+1);
						//console.log(currentLevelNames[levelNum])
						//console.log($("#model_create_levelname_"+(parseInt(levelNum)+1)).val());
						$("#model_create_lcounts_" + (parseInt(levelNum)+1)).val(currentLevelCounts[levelNum]);
						levelCountOn = true;
					}
				}
			}
		});
		$("#next_button").prop('value','{{_("Next Stage")}}');
		page_step = 2;
	}
	
	/// OK one last thing, if we change the number of levels we have to work that out.
	
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
					$("#model_create_name_levels").html(json.htmlString);
					$("#model_create_nlevels_input").prop('disabled',true);
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
					$("#model_create_name_levels").fadeTo(400,0.5);
					$("#model_create_name_levels :input").prop("disabled",true)
					$("#model_create_number_places").fadeIn("slow");
					$('#next_button').prop('value','{{_("Next Stage")}}')
					
				}
			});
			page_step = 2;
		}
		else if(page_step == 2){
			var modelName = $("#model_create_model_name").val();
			var modelNLevels = $("#model_create_nlevels_input").val();
			var modelLevelNames = validate_inputs(modelNLevels);
			if (modelName) {
				window.location = "{{rootPath}}model-create/next?name="+modelName+"&nlevels="+modelNLevels+modelLevelNames;
			}
		}
		
		//var modelName = $("#model_create_model_name").val();
		//var modelNLevels = $("#model_create_nlevels").val();
		//if (modelName) {
		//	window.location = "{{rootPath}}model-create/next?name="+modelName+"&nlevels="+modelNLevels;
		//}
		//else {
		//	$("#dialog-modal").dialog("open");
		//}
	});
	
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
});

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
</script>
 