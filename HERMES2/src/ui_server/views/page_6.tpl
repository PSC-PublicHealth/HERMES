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
<div id='tabs-6'>

<body>	
<h2>{{_('This is for little tests')}}</h2>
<button id="testbutton">{{_('Do it!')}}</button>
<script>
$(function () {
	var btn = $("#testbutton");
	btn.button();
	btn.click( function() {
		$.getJSON("json/test-button")
		.done(function(data) {
			if (data.success) {
				alert('success');
			}
			else {
				alert('Error: '+data.msg)
			}
		})
		.fail(function(jqxhdr, textStatus, error) {
			alert(jqxhdr.responseText);
		});
	});
});
</script>

</body>

</div>