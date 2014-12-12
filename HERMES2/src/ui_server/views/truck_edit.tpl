%rebase outer_wrapper title_slogan=_("Modify Transport Type"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

% if not overwrite: 
<h1>{{_('Creating Your Transport Type')}}</h1>
{{_("The fields have been filled out with values from the transport type you selected.  When you are finished, select the 'Done' button at the bottom right.")}}
<p>
{{_("Your prototype was named {0}").format(protoname)}}
</p>
% else:
<h1>{{_('Edit Your Transport Type')}}</h1>
{{_("You may create a new transport type by changing the name of this one or leave it the same to modify the current type.")}}
% end
<form id="_edit_form">
    <div id="_edit_form_div"></div>
    <table width=100%>
      <tr>
        <td></td>
        <td width=10%><input type="button" id="cancel_button" value={{_("Cancel")}}></td>
        <td width=10%><input type="button" id="done_button" value={{_("Done")}}></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_("The name of the model must not be blank.")}}</p>
</div>

<script>
$(function() {
	var protoname = "{{get('protoname')}}";
	var modelId = {{get('modelId')}};
	$.getJSON('json/truck-edit-form',{
	    protoname:protoname, 
	    modelId:modelId,
	    % if overwrite:
	    overwrite:1
	    % end
	})
	.done(function(data) {
		if (data.success) {
			$("#_edit_form_div").hrmWidget({
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
	var dict = $('#_edit_form_div').editFormManager('getEntries');
	% if overwrite:
	dict['overwrite'] = 1;
	% end
	
	$.getJSON("{{rootPath}}json/truck-edit-verify-commit",dict)
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
	
    });
});

</script>
 