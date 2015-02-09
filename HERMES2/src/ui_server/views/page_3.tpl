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
<div id='tabs-3'>
<h2>{{_('This is a jsTree example')}}</h2>

<div id="treedemo"></div>

<script>
$(function() {
  $('#treedemo').jstree({
    "plugins": ["core","themes","json_data","ui"],
	"themes" : {
		"theme" : "classic",
	},
	"json_data" : {
		"ajax" : {
                "url" : "json/show-tree",
				"data" : function (n) {
					return { id : n.attr ? n.attr("id") : -1 };
				},
				"success" : function(jsonResult) {
					if (jsonResult.success) {
						return jsonResult.kidList;
					}
					else {
						alert('{{_("Failed: ")}}'+jsonResult.msg);
						return ['{{_("Fetch failed")}}']
					}
				},
				"error" : function(jqxhr, textStatus, error) {
					alert('{{_("Error: ")}}'+jqxhr.responseText);
				}
            }
	/*
		"data" : [
			{
				"data" : {{_("A node")}},
				"metadata" : { id : 23 },
				"children" : [ {{_("Child 1")}}, {{_("A Child 2")}} ]
			},
			{
				"attr" : { "id" : "li.node.id1" },
				"data" : {
					"title" : {{_("Long format demo"))},
					"attr" : { "href" : "#" }
				}
			}
		]
		*/
	}
  });
});
</script>

</div>