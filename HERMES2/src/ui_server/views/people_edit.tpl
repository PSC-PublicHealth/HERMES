%rebase outer_wrapper title_slogan=_("Modify Population Type"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
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
<h1>{{_('Creating Your Population Type')}}</h1>
{{_("The fields have been filled out with values from the population type you selected.  When you are finished, select the 'Done' button at the bottom right.")}}
<p>
{{_("Your prototype was named {0}").format(protoname)}}
<form id="people_edit_form">
    <div id="people_edit_form_div"></div>
</form>

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
	$(document).hrmWidget({widget:'stdCancelSaveButtons',
		getParms:function(){
			var dict = $('#people_edit_form_div').editFormManager('getEntries');
			% if overwrite:
			dict['overwrite'] = 1;
			% end
			return dict;
		},
		checkParms:function(parmDict) {
			return ($.getJSON("{{rootPath}}json/people-edit-verify-commit",parmDict)
					.promise());
		},
		doneURL:'{{! breadcrumbPairs.getDoneURL() }}'
	});
});

</script>
 