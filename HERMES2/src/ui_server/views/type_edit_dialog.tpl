<!--
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

% title_slogan=attr['slogan']
% breadcrumbPairs=breadcrumbPairs
% _=_
% inlizer=inlizer


<div id="edit_form_div"></div>


<script>
$(function() {
    var protoname = "{{get('protoname')}}";
    var modelId = {{get('modelId')}};
    //alert("P " + protoname);
    //alert("M " +modelId);
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

//	console.log("setting");
//	alert("shit");
//	$("#edit_form_buttons_div").hrmWidget({widget:'stdCancelSaveButtons',
//		getParms:function(){
//			var dict = $('#edit_form_div').editFormManager('getEntries');
//			% if overwrite:
//			dict['overwrite'] = 1;
//			% end
//			return dict;
//		},
//		checkParms:function(parmDict) {
//			return ($.getJSON("{{rootPath}}{{attr['commitForm']}}",parmDict)
//					.promise());
//		},
//		doneURL:'{{! breadcrumbPairs.getDoneURL() }}'
//	});
});


</script>
 