%rebase outer_wrapper title_slogan=_("Modify Transport Type"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<!---
###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################
-->
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
</form>

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
	$(document).hrmWidget({widget:'stdCancelSaveButtons',
		getParms:function(){
			var dict = $('#_edit_form_div').editFormManager('getEntries');
			% if overwrite:
			dict['overwrite'] = 1;
			% end
			return dict;
		},
		checkParms:function(parmDict) {
			return ($.getJSON("{{rootPath}}json/truck-edit-verify-commit",parmDict)
					.promise());
		},
		doneURL:'{{! breadcrumbPairs.getDoneURL() }}'
	});
});

</script>
 