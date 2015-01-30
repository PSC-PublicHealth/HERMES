%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<form id="run_parms_edit_form">
	<div id="run_parms_edit_form_div"></div>
</form>

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
    var btn = $("#wrappage_cs_misc_button");
    btn.show();
    btn.button();
    btn.attr('value',"{{_('Switch To Advanced')}}");
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
	$(document).hrmWidget({widget:'stdCancelSaveButtons',
		getParms:function(){
			var dict = {modelId:{{get('modelId')}}}
			$("#run_parms_edit_form input,select").each(function(index) {
			    var tj = $(this);
			    if (tj.is(":checkbox")) {
				dict[tj.attr('id')] = tj.is(":checked");
			    } else {
				dict[tj.attr('id')] = tj.val();
			    }
			});
			return dict;
		},
		checkParms:function(parmDict) {
			return ($.ajax({
				type:"POST",
				dataType:"json",
				url:"{{rootPath}}json/run-parms-edit", 
				data:parmDict
			}).promise());
		},
		doneURL:'{{! breadcrumbPairs.getDoneURL() }}'
	});
});


</script>
