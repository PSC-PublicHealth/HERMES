<!---
-->
% attrs = {
%    'trucks' : { 
%        'editForm'      : 'json/truck-edit-form',
%        'commitForm'    : 'json/truck-edit-verify-commit',
%        'slogan'        : _("Modify Transport Type"),
% 	     'editHeader'    : _("Edit Your Transport Type"),
%        'createHeader'  : _("Creating Your Transport Type"),
%        },
%    'fridges' : { 
%        'editForm'      : 'json/fridge-edit-form',
%        'commitForm'    : 'json/fridge-edit-verify-commit',
%        'slogan'        : _("Modify Cold Storage Type"),
% 	     'editHeader'    : _("Edit Your Cold Storage Type"),
%        'createHeader'  : _("Creating Your Cold Storage Type"),
%        },
%    'vaccines' : { 
%        'editForm'      : 'json/vaccine-edit-form',
%        'commitForm'    : 'json/vaccine-edit-verify-commit',
%        'slogan'        : _("Modify Vaccine Type"),
% 	     'editHeader'    : _("Edit Your Vaccine Type"),
%        'createHeader'  : _("Creating Your Vaccine Type"),
%        },
%    'people' : { 
%        'editForm'      : 'json/people-edit-form',
%        'commitForm'    : 'json/people-edit-verify-commit',
%        'slogan'        : _("Modify Population Type"),
% 	     'editHeader'    : _("Edit Your Population Type"),
%        'createHeader'  : _("Creating Your Population Type"),
%        },
%    'staff': {
%        'editForm'      : 'json/staff-edit-form',
%        'commitForm'    : 'json/staff-edit-verify-commit',
%        'slogan'        : _("Modify Staff Type"),
%        'editHeader'    : _("Edit Your Staff Type"),
%        'createHeader'  : _("Creating Your Staff Type")
%        },
%    'perdiems': {
%        'editForm'      : 'json/perdiem-edit-form',
%        'commitForm'    : 'json/perdiem-edit-verify-commit',
%        'slogan'        : _("Modify PerDiem Type"),
%        'editHeader'    : _("Edit Your PerDiem Type"),
%        'createHeader'  : _("Creating Your PerDiem Type")
%        }
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
</form>

<script>
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
	$(document).hrmWidget({widget:'stdCancelSaveButtons',
		getParms:function(){
			var dict = $('#edit_form_div').editFormManager('getEntries');
			% if overwrite:
			dict['overwrite'] = 1;
			% end
			return dict;
		},
		checkParms:function(parmDict) {
			return ($.getJSON("{{rootPath}}{{attr['commitForm']}}",parmDict)
					.promise());
		},
		doneURL:'{{! breadcrumbPairs.getDoneURL() }}'
	});
});


</script>
 
