%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<form id="run_parms_edit_form">
	<div id="run_parms_edit_form_div"></div>
</form>

<form>
	<table width=100%>
		<tr>
			<td width=70%></td>
			<td width=10%>
			    <input type="button" id="bas_adv_button" value="{{_('Switch To Advanced')}}">
			</td>
			<td width=10%>
			<input type="button" id="cancel_button" value={{_("Cancel")}}>
			</td>
			<td width=10%>
			<input type="button" id="save_button" value={{_("Save")}}>
			</td>
		</tr>
	</table>
</form>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
	<p>
		{{_("This will be replaced")}}
	</p>
</div>

<script>
function setParamVisibilityByLevel(level,table){
    $.getJSON('json/run-parms-levels-to-show', {
	level:level
    }).done(function(data) {
	if (data.success){
	    keyList = data['keyList']
	    $("#"+table+" input").each( function(index) {
	       	var key = $(this).attr('id');
		if($.inArray(key,keyList) > -1){
		    $("#"+key).parent().parent().show();
		    $("#"+key).css("visibility","visible");
		}
		else{
		    $("#"+key).parent().parent().hide();
		}		
	    });
	}
	else {
	    alert('{{_("Failed: ")}}' + data.msg);
	}
    }).fail(function(jqxhr, textStatus, error) {
	alert("Error: " + jqxhr.responseText);
    });			
}

$(function() {
    var modelId = {{get('modelId')}};
    $.getJSON('{{rootPath}}model-run/json/run-parms-edit-form', {
	modelId : modelId, level: 1, maxlevel: 2
    }).done(function(data) {
	if (data.success) {
	    $("#run_parms_edit_form_div").html('<h3>' + data['title'] + '</h3>' + data['htmlstring']);
	} 
	else {
	    alert('{{_("Failed: ")}}' + data.msg);
	}
    }).fail(function(jqxhr, textStatus, error) {
	alert("Error: " + jqxhr.responseText);
    });
    setParamVisibilityByLevel(1,"run_parms_edit_form_table");
});

$(function() {
    var btn = $("#cancel_button");
    btn.button();
    btn.click(function() {
		window.location = "{{rootPath}}model-run/next"; // but without applying changes
    });
});

$(function() {
    var btn = $("#bas_adv_button");
    btn.button();
    var level = 1;
    btn.click(function(){
	var modelId = {{get('modelId')}};
	if(btn.val() == "{{_('Switch To Basic')}}"){
	    level = 1;
	    btn.attr('value',"{{_('Switch To Advanced')}}");
	}
	else{
	    level = 2;
	    btn.attr('value',"{{_('Switch To Basic')}}");
	}
	setParamVisibilityByLevel(level,"run_parms_edit_form_table");			
    });		
});	

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
    
    var btn = $("#save_button");
    btn.button();
    btn.click( function() {
	var dict = {modelId:{{get('modelId')}}}
	
	$("#run_parms_edit_form input,select").each(function(index) {
	    var tj = $(this);
	    if (tj.is(":checkbox")) {
		dict[tj.attr('id')] = tj.is(":checked");
	    } else {
		dict[tj.attr('id')] = tj.val();
	    }
	});
	$.getJSON("{{rootPath}}json/run-parms-edit", dict).done(function(data) {
	    if (data.success) {
		if (data.value) {
			window.location = "{{rootPath}}model-run/next";
		} else {
		    $("#dialog-modal").text(data['msg']);
		    $("#dialog-modal").dialog("open");
		}
	    } else {
		alert('{{_("Failed: ")}}' + data.msg);
	    }
	}).fail(function(jqxhr, textStatus, error) {
	    alert("Error: " + jqxhr.responseText);
	});
    });    
});
</script>
