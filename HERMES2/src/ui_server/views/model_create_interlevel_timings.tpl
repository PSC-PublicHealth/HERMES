%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.css"/>
<script src="{{rootPath}}static/uisession.js"></script>

<style>
#model_create_ui_holder{
	width:100%;
	max-width:825px;
}
#model_create_interltime_form_div{
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
input.interleveltable {
	width:50px;
}
select.interleveltable {
	width:100px;
}
span.interleveltableem {
	font-color:blue;
	font-weight:bold;
}
.interleveltablehead{
	font-size:14px;
}
</style>

<script>
var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
console.log(modJson);
var modelInfo = ModelInfoFromJson(modJson);
console.log(modelInfo);

//This function updates the network diagram
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

<h1>{{_('What are the typical travel times between levels?')}}</h1>

<div name="model_create_ui_holder" id="model_create_ui_holder">
<div id="model_create_interltime_form_div">A form needs to go here</div>
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

<div id="dialog-modal" title={{_("Invalid Entry")}}>
	<div id="dialog-modal-text"/>
</div>
<div id="dialog-save-confirm-modal" title='{{_("Confirm Changes?")}}'>
	<p>{{_('Would you like to save the changes made on this page?')}}</p>
</div>

<script>
$(function(){
	updateInterLevelTimingTable().done(function(result){
		if(!result.success){
			if(result.type == "error")
				alert(result.msg);
		}
		else {
			$("#model_create_interltime_form_div").html(result.htmlString);
			add_event_handlers();
			$("#model_create_timing_time_1").focus().select();
			//add_interlevelship_listeners();
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
	
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		$("#dialog-save-confirm-modal").dialog("open");
	});
	
	//EXPERT BUTTON
	var btn = $("#expert_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/next?expert=true";
	});
});

function updateInterLevelTimingTable(){
	return $.ajax({
		url:'{{rootPath}}json/model-create-interl-timing-form-from-json',
		type:'post',
		dataType:'json',
		data:JSON.stringify(modelInfo)
	}).promise();
};

//Event Handlers
function add_event_handlers(){
	// Set old value so that we can revert on validation
	$('[id^=model_create_timing]').each(function(){
		$(this).data('oldval',$(this).val());
	});
	
	//Bold on focus
	$('[id^=model_create_timing]').focusin(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		$('#tree-layout-diagram').diagram("bold_link_arrow",thisLevNum);
	});	
	
	//Unbold on focus loss
	$('[id^=model_create_timing]').focusout(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		$('#tree-layout-diagram').diagram("unbold_link_arrow",thisLevNum);
	});	
	
	$('[id^=model_create_timing_time]').change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		$(this).val(validate_timing($(this).val(),$(this).data('oldval')));
		modelInfo.shiptransittimes[thisLevNum] = parseFloat($(this).val());
		$(this).data('oldval',$(this).val());
		modelInfo.changed = true;
		//Change network diagram
		$("#tree-layout-diagram").diagram('change_route_time',thisLevNum,$(this).val(),$('#model_create_timing_units_'+(thisLevNum+1)).val());
	});
	
	$('[id^=model_create_timing_units]').change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		modelInfo.shiptransitunits[thisLevNum] = $(this).val();
		modelInfo.changed = true;
		//Change network diagram
		$("#tree-layout-diagram").diagram('change_route_time',thisLevNum,$('#model_create_timing_time_'+(thisLevNum+1)).val(),$(this).val());
	});
	
	$('[id^=model_create_timing_dist]').change(function(){
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/))-1;
		$(this).val(validate_distance($(this).val(),$(this).data('oldval')));
		modelInfo.shiptransitdist[thisLevNum] = parseFloat($(this).val());
		$(this).data('oldval',$(this).val());
		modelInfo.changed = true;
		$("#tree-layout-diagram").diagram('change_route_distance',thisLevNum,$(this).val())
	})
	
};

//Validation Functions
function validate_timing(value,origValue){
	if(isNaN(value) || value == ""){
		$("#dialog-modal-text").text("{{_('The trip time to be a positive number.')}}");
		$('#dialog-modal').dialog("open");
		return origValue;
	}
	if(value <= 0){
		$("#dialog-modal-text").text("{{_('The trip time cannot be less than or equal to 0. Please select a positive number.')}}");
		$('#dialog-modal').dialog("open");
		return origValue;
	}
	return value;
};

function validate_distance(value,origValue){
	if(value < 0){
		$("#dialog-modal-text").text("{{_('The trip can not have a distance less than 0. Please select a positive number.')}}");
		$('#dialog-modal').dialog("open");
		return origValue;
	}
	if(isNaN(value) || value == ""){
		$("#dialog-modal-text").text("{{_('The trip distance has to be a positive number.')}}");
		$('#dialog-modal').dialog("open");
		return origValue;
	}
	return value;
};

</script>
 