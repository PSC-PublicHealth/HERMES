<!---
-->
<h1>{{heading}}</h1>
{{_("The fields have been filled out with values from the per diem rule you selected.  When you are finished, select the 'Done' button at the bottom right.")}}
<p>
{{_("Your prototype was named {0}").format(protoname)}}
<form id="type_edit_form">
    <div id="type_edit_form_div"></div>
</form>

<script>
$(function() {
	var protoname = "{{get('protoname')}}";
	var modelId = {{get('modelId')}};
	$.getJSON('{{rootPath}}{{formURL}}',{
		protoname:protoname, 
		modelId:modelId
		})
	.done(function(data) {
		if (data.success) {
			$("#type_edit_form_div").hrmWidget({
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
			var dict = $('#type_edit_form_div').editFormManager('getEntries');
			return dict;
		},
		checkParms:function(parmDict) {
			return ($.getJSON("{{rootPath}}{{editURL}}",parmDict)
					.promise());
		},
		doneURL:'{{! breadcrumbPairs.getDoneURL() }}'
	});
});


</script>
 
