%rebase outer_wrapper title_slogan=_("Create A Model"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,pagehelptag=pagehelptag

<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.js"></script>
<script src="{{rootPath}}static/uisession.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.css"/>
<script>


var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
var modelInfo = ModelInfoFromJson(modJson);
console.log(modJson);
console.log(modelInfo);

// This function updates the network diagram
function updateNetworkDiagram(){
	$("#tree-layout-diagram").remove();
	$("#model_create_diagram").append($("<div id='tree-layout-diagram' name='tree-layout-diagram'/>"));
	$("#tree-layout-diagram").diagram({
	        hasChildrenColor: "steelblue",
	        noChildrenColor: "#ccc",
	        minWidth: 768,
	        jsonData: modelInfo.toJsonNetwork(),
	        minHeight: 775,
	        resizable: false,
	        scrollable: true,
	        trant: {
	             "title": "{{_('Model')}}",
	        }
	});
}

</script>

<p>
	<span class="hermes-top-main">
		{{_('What is the supply chain structure of the \"{0}\" model?'.format(name))}}
	</span>
</p>

<p>
	<span class="hermes-top-sub">
		{{_('Please answer the following questions about the overall supply chain structure.  Click the Next Step button to move onto the next questions.')}}
		{{_('The dynamic diagram will automatically update as you change the characteristics of the supply chain structure (e.g., add/subtract levels, locations, etc.) or shipping policies/frequency/distance.')}}
	</span>
<p>

<style>
#model_create_ui_holder{
	width:100%;
	max-width:875px;
	min-width:875px;
	max-height:800px;
}
#model_create_holder{
	width:450px;
	float:left;
}
#model_create_nlevels_input{
	margin-bottom:10px;
}
#model_create_name_levels{
	margin-bottom:10px;
}

#model_create_diagram{
	float:right;
}
#model_create_next_button{
	height:150px;
	float:left;
}
#scroll_down_div{
	position:fixed;
	bottom:10px;
	right:50px;
	display:none;
}
.levelnames-head{
	font-size:14px;
	margin-bottom
}
.levelnames-note{
	font-size:11px;
	font-style:italic;
}
.levelnames-em{
	font-weight:bold;
}
.levelcount-em{
	font-weight:bold;
}
.levelcount-head{
	font-size:14px;
}
.levelcount-note{
	font-size:11px;
	font-style:italic;
}
.tooltip{
	font-weight: bold;
	fill:#282A57;
}
#
</style>

<div name="scroll_down_div" id="scroll_down_div">
<img src="{{rootPath}}static/images/scrolldownarrow.png">
</div>
<div name="model_create_ui_holder" id="model_create_ui_holder">
	<div name="model_create_holder" id="model_create_holder">
		<div id="model_create_num_levels">
			  	<table>
				  	<tr>
			  			<td>
			  				<label for="model_create_nlevels_input">
			  					<span class="levelnames-head">{{_('Please select the number of ')}}
			  					<span class="tooltip" >
			  						<a href="#" 
			  							title="{{_('The number of storage locations that a vaccine or health product passes through from entering the supply chain to location in which it is used.')}}">
			  							{{_('levels')}}
			  						</a>
			  					</span> 
			  					{{_('in the supply chain.')}}</span>
			  				</label>
			  			</td>
			  			<td style="vertical-align:middle;">
			  			<div id="sub-div-nlevels">
			  				<select name="model_create_nlevels_input" id="model_create_nlevels_input">
			  				</select>
						<!--<div style="position:absolute; left:0; right:0; top:0; bottom:0; cursor: pointer;display:none;" id="subsub"/>-->		
						</div> <!-- sub-div-nlevels -->
						</td>
			  		</tr>
			    </table>
		</div> <!-- model_create_num_levels -->
	
		<div name="model_create_name_levels" id="model_create_name_levels" style="display:none;">
			Replaced
		</div>
		<div name="model_create_number_places" id="model_create_number_places" style="display:none;">
			Putting some stuff here to test
		</div>
	</div>
	<div id="model_create_diagram" name="model_create_diagram_container">
		<div id="tree-layout-diagram" name="tree-layout-diagram"/>
			<script>
			console.log(modelInfo)
			    updateNetworkDiagram();
			</script>
		</div>
	</div>
	<div id="model_create_next_button"> 
		<table width=100%>
			<tr>
				<td width 10%>
					<!--<input type="button" id="back_button" value='{{_("Previous Screen")}}'>-->
				</td>
				<td>
				</td>
				<td width=10%>
					<!--<input type="button" id="expert_button" value='{{_("Skip to Model Editor")}}'>-->
				</td>
				<td width=10%>
					<input type="button" id="next_button" value='{{_("Next Step")}}'>
				</td>
			</tr>
		</table>
	</div>
</div>




<input id="selected-level-hidden" type="text" style="display:none"/>
<div id="dialog-modal" title='{{_("Invalid Input Entry")}}'>
 	<div id="dialog-modal-text"/>
 	</div>
</div>

<div id="reactivate-nlevels-modal" title='{{_("Confirm Changing Number of Levels")}}'>
  <p>{{_("Would you like to go back and change these values?")}}</p>
</div>

<!--<div id="reactivate-levnames-modal" title='{{_("Confirm Changing Level Names")}}'>
	<p>{{_("Would you like to go back and change these values?")}}</p>
</div>-->

<div id="level-change-dialog" title='{{_("Changing Levels")}}'>
	<p>'{{_("You are changing the number of levels in the system, this will result in the names of your levels and counts per level needing to be updated")}}'</p>
</div>

<div id="big-modal" title='{{_("Warning: Large number of locations")}}'>
	<p>{{_("You are creating a model with a large number of locations.  Please note that this will require much time to create the model for simulation and if you would like to proceed, you will need patience when waiting between screens.")}}</p>
</div>
<script>

var page_step = 0;
$(function() {
	createNLevelSelect();

//	if( $(window).scrollTop()!= $(document).height())
//		$("#scroll_down_div").show();
//	
//	$('body,html').scroll(function(){
//		if( $(window).scrollTop()== $(document).height())
//			$("#scroll_down_div").hide();
//		else
//			$("#scroll_down_div").show();
//	});
//	$(window).resize(function(){
//		if (($(window).height() < ($("#model_create_next_button").position().top + $("#model_create_next_button").outerHeight(true)))
//				&& ($(window).scrollTop() + $(window).height() != $(document).height()))
//			$("#scroll_down_div").show();
//		else
//			$("#scroll_down_div").hide();
//	});
//	
//	$(window).ready(function(){
//		if (($(window).height() < ($("#model_create_next_button").position().top + $("#model_create_next_button").outerHeight(true)))
//				&& ($(window).scrollTop() + $(window).height() != $(document).height()))
//			$("#scroll_down_div").show();
//		else
//			$("#scroll_down_div").hide();
//	});

	$("#subsub").click(function(e){
		//e.preventDefault();
		console.log("Checking");
		if ($("#model_create_nlevels_input").is(':disabled')){
		//if( $("#model_create_nlevels_input").is(':disabled')){
			console.log("Disabled");
			//$("#reactivate-nlevels-modal").dialog("open");
		}
	});
	
	//Modal Dialog needed for reporting errors
	$("#dialog-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				$( this ).dialog( "close" );
        	}
        },
        open: function(e,ui) {
    	    $(this)[0].onkeypress = function(e) {
    		if (e.keyCode == $.ui.keyCode.ENTER) {
    		    e.preventDefault();
    		    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
    		}
    	    };
        }
	});
	
	$("#big-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			'{{_("OK")}}': function() {
				$( this ).dialog( "close" );
        	}
        },
        open: function(e,ui) {
    	    $(this)[0].onkeypress = function(e) {
    		if (e.keyCode == $.ui.keyCode.ENTER) {
    		    e.preventDefault();
    		    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
    		}
    	    };
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

	add_nlevel_handlers();
	
	
	// The Next Button moving through the first time
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		if(page_step == 0){
			$("#current-level-count-input").val($("#model_create_nlevels_input").val());
			$("#current-level-count2-input").val($("#model_create_nlevels_input").val());
			console.log(modelInfo);
			updateLevelNamesTable().done(function(result){
				if(!result.success){
					if(result.type == "error")
						alert(result.msg);
				}
				else{
					$("#model_create_name_levels").html(result.htmlString);
					add_level_name_handlers();
					$("#model_create_nlevels_input").prop('disabled',true);
					$("#subsub").show();
					$("#model_create_nlevels_input").css("background-color","grey");
					$("#model_create_nlevels_input").css("color","white");
					$("#model_create_num_levels").fadeTo("slow",.50);
					$("#model_create_name_levels").fadeIn("slow");
					$("#model_create_levelname_1").focus();
					$("#model_create_levelname_1").select();
				}
			});
			page_step = 1;
		}
		else if(page_step == 1){
			updateLevelCountsTable().done(function(result){
				if(!result.success){
					if(result.type == "error")
						alert(result.msg);
				}
				else{
					$("#model_create_number_places").html(result.htmlString);
					//updateNetworkDiagram();
					add_level_count_handlers();
					$("#model_create_name_levels").fadeTo(400,0.5);
					$("#model_create_name_levels :input").prop("disabled",true)
					$("#model_create_number_places").fadeIn("slow");
					$("#model_create_lcounts_2").focus();
					$("#model_create_lcounts_2").select();
					$('#next_button').prop('value','{{_("Next Screen")}}')
				}
			});
			page_step = 2;
		}
		else if(page_step == 2){
			modelInfo.updateSession('{{rootPath}}')
				.done(function(result){
					if(!result.success){
						if(result.type == "error")
							alert(result.msg);
					}
					window.location = "{{rootPath}}model-create/next";
				});
		}
	});
	
	
	// If there is data, this page needs to be populated and fully shown
	if(!modelInfo.firstTime){
		console.log("Not our first rodeo");
		updateLevelNamesTable().done(function(result){
			if(!result.success){
				if(result.type == "error")
					alert(result.msg);
			}
			else {
				$("#model_create_name_levels").html(result.htmlString);
				add_level_name_handlers();
				$("#model_create_name_levels").show();
			}
		});
		updateLevelCountsTable().done(function(result){
			if(!result.success){
				if(result.type == "error")
					alert(result.msg);
			}
			else {
				$("#model_create_number_places").html(result.htmlString);
				add_level_count_handlers();
				$("#model_create_number_places").show();
			}
		});
		updateNetworkDiagram();
		$("#next_button").prop('value','{{_("Next Stage")}}');
		page_step = 2;

	}
	
	// Level Change Dialog for altering an existing model

	$("#level-change-dialog").dialog({
		resizable: false,
		modal: true,
		autoOpen:false,
		buttons:{
			Yes: function(){
				$(this).dialog("close");
				modelInfo.changeNumberOfLevels($("#model_create_nlevels_input").val());
				updateLevelNamesTable().done(function(result){
					if(!result.success){
						if(result.type == "error")
							alert(result.msg);
					}
					else {
						$("#model_create_name_levels").html(result.htmlString);
						add_level_name_handlers();
						$("#model_create_name_levels").show();
					}
				});
				updateLevelCountsTable().done(function(result){
					if(!result.success){
						if(result.type == "error")
							alert(result.msg);
					}
					else {
						$("#model_create_number_places").html(result.htmlString);
						add_level_count_handlers();
						$("#model_create_number_places").show();
					}
				});
				updateNetworkDiagram();
				
			},
			No: function(){
				$('#model_create_nlevels_input').val(modelInfo.nlevels);
				$(this).dialog("close");
			}
		}
	});
});
	// Event handler functions for the inputs
	
	function add_nlevel_handlers(){
		$("#model_create_nlevels_input").change(function(){
			if (modelInfo.firstTime){
				modelInfo.changeNumberOfLevels($(this).val());
				updateNetworkDiagram();
				modelInfo.changed = true;
			}
			else{
				$("#level-change-dialog").dialog("open");
			}
		});
	};
	
	function add_level_name_handlers(){
		$("#model_create_name_levels :input").each(function(){
			$(this).data('oldVal',$(this).val());
		});
		
		$("#model_create_name_levels :input").change(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_levelname_","")) - 1;
			// Error handling
			$(this).val(validate_levelName($(this).val(), thisLevNum,$(this).data('oldVal')));
			$(this).data('oldVal',$(this).val());
			//update session
			modelInfo.levelnames[thisLevNum] = $(this).val();
			modelInfo.changed = true;
			//update diagram widget
			$("#tree-layout-diagram").diagram("change_level_name",thisLevNum,$(this).val());
		});
		$("#model_create_name_levels :input").focusin(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_levelname_","")) - 1 ;
			$("#tree-layout-diagram").diagram("bold_level",thisLevNum);
		});
		$("#model_create_name_levels :input").focusout(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_levelname_","")) - 1;
			$("#tree-layout-diagram").diagram("unbold_level",thisLevNum);
		});
	};
	
	function add_level_count_handlers(){
		$("#model_create_number_places :input").each(function(){
			$(this).data('oldVal',$(this).val());
		});
		
		$("#model_create_number_places :input").change(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_lcounts_","")) - 1;
			var locString = "Location";
			if($(this).val() > 1) locString = "Locations";
			//Error handling
			$(this).val(validate_levelcount($(this).val(),thisLevNum,$(this).data('oldVal')));
			$(this).data('oldVal',$(this).val());
			// Check to see if this is large
			if($(this).val() > 5000){
				$("#big-modal").dialog("open");
				$(this).focus().select();
			}
			//Update session
			modelInfo.levelcounts[thisLevNum] = parseInt($(this).val());
			modelInfo.changed = true;
			//Update diagram widget
			$("#tree-layout-diagram").diagram("change_location_text",thisLevNum,$(this).val() + " " +locString);
		});
		$("#model_create_number_places :input").focusin(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_lcounts_","")) - 1;
			$("#tree-layout-diagram").diagram("bold_level",thisLevNum);
		});
		$("#model_create_number_places :input").focusout(function(){
			thisLevNum = parseInt($(this).prop('id').replace("model_create_lcounts_","")) - 1;
			$("#tree-layout-diagram").diagram("unbold_level",thisLevNum);
		});
	};
	
	/// Validatation functions
	function validate_levelName(levelname,levelnum,origValue){
		if(levelname.length == 0){
			$("#dialog-modal-text").text("{{_('The name of a level cannot be blank')}}");
			$("#dialog-modal").dialog("open");
			return origValue;
		}
		return levelname;
	}
	
	function validate_levelcount(levelcount,levelnum,origValue){
		if(isNaN(levelcount) || levelcount == ""){
			$("#dialog-modal-text").text("{{_('The number of location per level must be a positive number.')}}");
			$('#dialog-modal').dialog("open");
			return origValue;
		}
		if(levelnum == 0){
			if (levelcount > 1) {
				$("#dialog-modal-text").text("{{_('The first level of the supply chain can only have one location')}}");
				$("#dialog-modal").dialog("open");
				return origValue;
			}
		}
		if (levelcount < 1) {
			$("#dialog-modal-text").text("{{_('The number of locations cannot be negative or 0')}}");
			$("#dialog-modal").dialog("open");
			return origValue;
		}
		return levelcount;
	}

	// Create or Update tables
	function createNLevelSelect(){
		for(var i=1;i<6;i++){
			$("#model_create_nlevels_input")
				.append($("<option></option>")
				.text(i+1)
				.val(i+1));
		}
		$("#model_create_nlevels_input").val(modelInfo.nlevels);
	}
	
	function updateLevelNamesTable(){
		return $.ajax({
			url:'{{rootPath}}json/model-create-name-levels-form-from-json',
			dataType:'json',
			type:'post',
			data:JSON.stringify(modelInfo)}).promise();
	};
	
	function updateLevelCountsTable(){
		return $.ajax({
			url:'{{rootPath}}json/model-create-number-places-per-level-form-from-json',
			type:'post',
			data:JSON.stringify(modelInfo),
			datatype:'json'
		}).promise();
	};
</script>
