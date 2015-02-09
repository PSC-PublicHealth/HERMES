%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,pagehelptag=pagehelptag
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.css"/>
<script src="{{rootPath}}static/uisession.js"></script>

<script>
var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
console.log(modJson);
var modelInfo = ModelInfoFromJson(modJson);
console.log(modelInfo);
</script>

<style>
input.interleveltable {
	width:200px;
}
select.interleveltable {
	width:200px;
}
span.interleveltableem {
	font-color:blue;
	font-weight:bold;
}
</style>
<script>


// This function updates the network diagram
function updateNetworkDiagram(){
	$("#tree-layout-diagram").remove();
	$("#model_create_diagram").append($("<div id='tree-layout-diagram' name='tree-layout-diagram'/>"));
	$("#tree-layout-diagram").diagram({
	        hasChildrenColor: "steelblue",
	        noChildrenColor: "#ccc",
	        jsonData:modelInfo.toJsonNetwork(),
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

<style>
#model_create_ui_holder{
	width:100%;
	max-width:825px;
}
#model_create_interlev_form_div{
	width:400px;
	float:left;
}
#model_create_diagram{
	float:right;
}
#model_create_interlev_buttons{
	height:150px;
	width:100%;
	float:left;
}
.interleveltablehead{
	font-size:14px;
}
</style>

<p>
	<span class="hermes-top-main">
		{{_('How are goods shipped?')}}
	</span>
</p>
<p>
	<span class="hermes-top-sub">
		{{_("Now please answer this series of questions about the shipping policies between the levels of the network.  The answer below will be used to create a new route between each of the locations at these levels.")}}
	</span>
</p>
<div name="model_create_ui_holder" id="model_create_ui_holder">
	<div id="model_create_interlev_form_div">A form needs to go here</div>
	<div id="model_create_diagram" name="model_create_diagram_container" style="position:relative; left:0; top:0; bottom:0;float:right;">
		<div id="tree-layout-diagram" name="tree-layout-diagram">
			<script>
			    updateNetworkDiagram();
			</script>
		</div>
	</div>
	<div name="model_create_interlev_buttons" id="model_create_interlev_buttons">
    	<table width=100%>
    		<tr>
    			<td width 10%>
    				<input type="button" id="back_button" value='{{_("Previous Screen")}}'>
    			</td>
    			<td>
    			</td>
    			<td width=10%>
    				<input type="button" id="expert_button" value='{{_("Skip to Model Editor")}}'>
    			</td>
    			<td width=10%>
    				<input type="button" id="next_button" value='{{_("Next Screen")}}'>
    			</td>
    		</tr>
    	</table>
    </div>	
</div>

<div id="dialog-modal" title='{{_("Invalid Entry")}}'>
	<div id="dialog-modal-text"/>
</div>
<div id="dialog-save-confirm-modal" title='{{_("Confirm Changes?")}}'>
	<p>{{_('Would you like to save the changes made on this page?')}}</p>
</div>
<div id="expert-modal" title='{{_("Entering Advanced Model Editor")}}'>
	<p>{{_("By entering the advanced model editor, you will be leaving the Model Creation Workflow, and not be able to re-enter.  Would you like to continue?")}}</p>
</div>

<script>
$(function(){
	updateInterLevelShipTable().done(function(result){
		if(!result.success){
			if(result.type == "error")
				alert(result.msg);
		}
		else {
			$("#model_create_interlev_form_div").html(result.htmlString);
			add_interlevelship_listeners();
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
	
	$("#expert-modal").dialog({
		resizable: false,
		modal: true,
		autoOpen:false,
		buttons: {
			'{{_("Yes")}}': function(){
				$(this).dialog("close");
				window.location = "{{rootPath}}model-create/next?expert=true&crmb=clear";
			},
			'{{_("No")}}': function(){
				$(this).dialog("close");
			}
		}
	});
	
	$("#dialog-save-confirm-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			'{{_("Yes")}}': function() {
				$( this ).dialog( "close" );
				modelInfo.updateSession('{{rootPath}}')
					.done(function(result){
						if(!result.success){
							if(result.type == "error")
								alert(result.msg);
					}
				window.location = "{{rootPath}}model-create/back";
				});
        	},
        	'{{_("No")}}': function() {
        		$( this ).dialog( "close" );
        		window.location = "{{rootPath}}model-create/back";
        	}
        }
	});
	
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		$("#dialog-save-confirm-modal").dialog("open");
		//window.location = "{{rootPath}}model-create/back"
	});
	
	var btn = $("#expert_button");
	btn.button();
	btn.click( function() {
		$("#expert-modal").dialog("open");
	});

	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		modelInfo.updateSession('{{rootPath}}')
			.done(function(result){
			if(!result.success){
				if(result.type == "error")
					alert(result.msg);
			}
			window.location = "{{rootPath}}model-create/next";
		});
	});	
});	

function updateInterLevelShipTable(){
	return $.ajax({
		url:'{{rootPath}}json/model-create-interl-info-form-from-json',
		type:'post',
		dataType:'json',
		data:JSON.stringify(modelInfo)		
	}).promise();
};

// listeners
function add_interlevelship_listeners(){
	
	// Listeners for bolding the route info on focus
	$("[id^=model_create_interl]").focusin(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		$('#tree-layout-diagram').diagram("bold_link_arrow",thisLevNum);
	});	
	
	// Listeners for unbolding the route info on focus
	$("[id^=model_create_interl]").focusout(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		$('#tree-layout-diagram').diagram("unbold_link_arrow",thisLevNum);
	});
	
	// Listeners for flipping arrow direction
	$("[id^=model_create_interl_isfetch]").change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		modelInfo.shippatterns[thisLevNum][1] = $(this).val();
		modelInfo.changed = true;
		$('#tree-layout-diagram').diagram("flip_link_arrow",thisLevNum,$(this).val());
	});
	
	// Listeners that changes the label of frequency based on value
	$("[id^=model_create_interl_issched]").change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		if($(this).val() == "false"){
			$("#Iter_Level_Info_Form_table_row_"+((thisLevNum)*7 + 4)+"_col_0").addClass('animated pulse');
			setTimeout(function(){
				$("#Iter_Level_Info_Form_table_row_"+((thisLevNum)*7 + 4)+"_col_0").removeClass('animated pulse');
			},1000);
			setTimeout(function(){
				$("#Iter_Level_Info_Form_table_row_"+((thisLevNum)*7 + 4)+"_col_0").text("up to a frequency of");
			},300);
		}
		else{
			console.log("This is true");
			$("#Iter_Level_Info_Form_table_row_"+((thisLevNum)*7 + 4)+"_col_0")
				.addClass('animated pulse');
			setTimeout(function(){
				$("#Iter_Level_Info_Form_table_row_"+((thisLevNum)*7 + 4)+"_col_0").removeClass('animated pulse');
			},1000);
			setTimeout(function(){
				$("#Iter_Level_Info_Form_table_row_"+((thisLevNum)*7 + 4)+"_col_0").text("at a frequency of");
			},300);
		}
		modelInfo.shippatterns[thisLevNum][2] = $(this).val();
		modelInfo.changed = true;
		$("#tree-layout-diagram").diagram('change_route_freq',thisLevNum,$(this).val());
	});
	
	// Listeners for changing fixed tag on diagram
	$("[id^=model_create_interl_isfixedam]").change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		modelInfo.shippatterns[thisLevNum][0] = $(this).val();
		modelInfo.changed = true;
		$("#tree-layout-diagram").diagram('change_route_amt',thisLevNum,$(this).val());
	});
	
	$("[id^=model_create_interl_howoften]").each(function(){
		$(this).data('oldVal',$(this).val());
	});
	
	// Listener for changing the interval on diagram
	$("[id^=model_create_interl_howoften]").change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		$(this).val(validate_interval($(this).val(),$("#model_create_interl_ymw_"+(thisLevNum+1)).val(),$(this).data('oldVal')));
		modelInfo.shippatterns[thisLevNum][3] = parseFloat($(this).val());
		$(this).data('oldVal',$(this).val());
		console.log($("#model_create_interl_ymw_"+(thisLevNum+1)).val());
		modelInfo.changed = true;
		$("#tree-layout-diagram").diagram('change_route_interv',thisLevNum,$(this).val(),$("#model_create_interl_ymw_"+(thisLevNum+1)).val());
	});
	
	//Listener for changing time unit on diagram
	$("[id^=model_create_interl_ymw]").change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		modelInfo.shippatterns[thisLevNum][4] = $(this).val();
		console.log(thisLevNum  + " " + $('#model_create_interl_howoften_'+(thisLevNum+1)).val());
		modelInfo.changed = true;
		$("#tree-layout-diagram").diagram('change_route_interv',thisLevNum,$('#model_create_interl_howoften_'+(thisLevNum+1)).val(),$(this).val());
	});
};

// Validation functions
function validate_interval(value,unit,origValue){
	var limits = {'year':336,'month':28,'week':7};
	if(isNaN(value) || value == ""){
		$("#dialog-modal-text").text("{{_('The frequency of shipments must be a positive number.')}}");
		$('#dialog-modal').dialog("open");
		return origValue;
	}
	if(value <= 0){
		$("dialog-modal-text").text("{{_('The frequency of shipments cannot be less than or equal to 0. Please select a positive number.')}}");
		$('#dialog-modal').dialog("open");
		return origValue;
	}
	
//	if(value > limits[unit]){
//		$("dialog-modal-text").text("{{_('The frequency of shipments be specifed at more than one trip per day. Please select a positive number.')}}");
//		$('#dialog-modal').dialog("open");
//		return origValue;
//	}
	return value;
}

</script>
 