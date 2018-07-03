%rebase outer_wrapper title_slogan=_("Modify Vaccine Type"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<!---
-->
<h1>{{_('Creating Your Vaccine Type')}}</h1>
{{_("The fields have been filled out with values from the vaccine type you selected.  When you are finished, select the 'Done' button at the bottom right.")}}
<p>
{{_("Your prototype was named {0}").format(protoname)}}
<form id="vaccine_edit_form">
    <div id="vaccine_edit_form_div"></div>
</form>

<script>
$(function() {
	var protoname = "{{get('protoname')}}";
	var modelId = {{get('modelId')}};
	$.getJSON('json/vaccine-edit-form',{
		protoname:protoname, 
		modelId:modelId
		})
	.done(function(data) {
		if (data.success) {
			$("#vaccine_edit_form_div").hrmWidget({
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
			var dict = $('#vaccine_edit_form_div').editFormManager('getEntries');
			% if overwrite:
			dict['overwrite'] = 1;
			% end
			return dict;
		},
		checkParms:function(parmDict) {
			return ($.getJSON("{{rootPath}}json/vaccine-edit-verify-commit",parmDict)
					.promise());
		},
		doneURL:'{{! breadcrumbPairs.getDoneURL() }}'
	});
});

</script>
 
