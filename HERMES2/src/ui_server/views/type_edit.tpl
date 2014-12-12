% attrs = {
%    'trucks' : { 
%        'editForm'      : 'json/truck-edit-form',
%        'commitForm'    : 'json/truck-edit-verify-commit',
%        'slogan'        : _("Modify Transport Type"),
% 	 'editHeader'    : _("Edit Your Transport Type"),
%        'createHeader'  : _("Creating Your Transport Type"),
%        },
%    'fridges' : { 
%        'editForm'      : 'json/fridge-edit-form',
%        'commitForm'    : 'json/fridge-edit-verify-commit',
%        'slogan'        : _("Modify Cold Storage Type"),
% 	 'editHeader'    : _("Edit Your Cold Storage Type"),
%        'createHeader'  : _("Creating Your Cold Storage Type"),
%        },
%    'vaccines' : { 
%        'editForm'      : 'json/vaccine-edit-form',
%        'commitForm'    : 'json/vaccine-edit-verify-commit',
%        'slogan'        : _("Modify Vaccine Type"),
% 	 'editHeader'    : _("Edit Your Vaccine Type"),
%        'createHeader'  : _("Creating Your Vaccine Type"),
%        },
%    'people' : { 
%        'editForm'      : 'json/people-edit-form',
%        'commitForm'    : 'json/people-edit-verify-commit',
%        'slogan'        : _("Modify Population Type"),
% 	 'editHeader'    : _("Edit Your Population Type"),
%        'createHeader'  : _("Creating Your Population Type"),
%        },
% }
% attr = attrs[typeClass]

%rebase outer_wrapper title_slogan=attr['slogan'], breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

% if not overwrite: 
<h1>{{attr['createHeader']}}</h1>
{{_("The fields have been filled out with values from the type you selected.  When you are finished, select the 'Done' button at the bottom right.")}}
<p>
{{_("Your prototype was named {0}").format(protoname)}}
</p>
% else:
<h1>{{attr['editHeader']}}</h1>
{{_("You may create a new type by changing the name of this one or leave it the same to modify the current type.")}}
% end
<form id="edit_form">
    <div id="edit_form_div"></div>
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
var backURL = "{{backURL}}";
%print backURL
$(function() {
    var protoname = "{{get('protoname')}}";
    var modelId = {{get('modelId')}};
    $.getJSON('{{rootPath}}{{attr["editForm"]}}',{
	protoname:protoname, 
	modelId:modelId,
	% if overwrite:
	overwrite:1
	% end
    })
	.done(function(data) {
	    if (data.success) {
		$("#edit_form_div").hrmWidget({
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
		if (backURL != 'query') {
		    window.location = backURL;
		    return;
		    alert("why am I here?");
		}
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
	var dict = $('#edit_form_div').editFormManager('getEntries');
	% if overwrite:
	dict['overwrite'] = 1;
	% end
	
	$.getJSON("{{rootPath}}{{attr['commitForm']}}",dict)
	    .done(function(data) {
		if (data.success) {
		    if (backURL != 'query') {
			window.location = backURL;
			return;
			alert("why am I here2?");
		    }
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
 