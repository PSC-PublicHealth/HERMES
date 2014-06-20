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