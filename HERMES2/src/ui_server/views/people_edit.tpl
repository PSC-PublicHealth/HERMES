%rebase outer_wrapper title_slogan=_("Modify Population Type"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<h1>{{_('Creating Your Population Type')}}</h1>
{{_("The fields have been filled out with values from the population type you selected.  When you are finished, select the 'Done' button at the bottom right.")}}
<p>
{{_("Your prototype was named {0}").format(protoname)}}
<form id="people_edit_form">
    <div id="people_edit_form_div"></div>
    <table width=100%>
      <tr>
        <td></td>
        <td width=10%><input type="button" id="cancel_button" value={{_("Cancel")}}></td>
        <td width=10%><input type="button" id="done_button" value={{_("Done")}}></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_("This will be replaced.")}}</p>
</div>

<script>
$(function() {
	var protoname = "{{get('protoname')}}";
	var modelId = {{get('modelId')}};
	$.getJSON('json/people-edit-form',{
		protoname:protoname, 
		modelId:modelId
		})
	.done(function(data) {
		if (data.success) {
			$("#people_edit_form_div").hrmWidget({
				widget:'editFormManager',
				html:data['htmlstring'],
				modelId:modelId
			});			
		}
		else {
	    	alert('{{_("Failed: ")}}'+data.msg);
		}
	})
	.fail(function(jqxhr, textStatus, error) {
		alert("Error: "+jqxhr.responseText);
	});
});

$(function() {
	var btn = $("#cancel_button");
	btn.button();
	btn.click( function() {
		var dict = {modelId:{{get('modelId')}}}
		$.getJSON("{{rootPath}}json/generic-edit-cancel",dict)
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					window.location = data.goto;
				}
				else {
					$("#dialog-modal").text(data['msg']);
					$("#dialog-modal").dialog("open");
				}
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
	})
})

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

	var btn = $("#done_button");
	btn.button();
	btn.click( function() {
		var dict = $('#people_edit_form_div').editFormManager('getEntries');
		$.getJSON("{{rootPath}}json/people-edit-verify-commit",dict)
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					window.location = data.goto;
				}
				else {
					$("#dialog-modal").text(data['msg']);
					$("#dialog-modal").dialog("open");
				}
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
		
		/*
		var modelName = $("#model_create_model_name").val();
		var modelNLevels = $("#model_create_nlevels").val();
		if (modelName) {
		*/
		/*
		if (true) { 
		}
		else {
			$("#dialog-modal").dialog("open");
		}
		*/
	});
});

</script>
 