%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<h3>{{_('Verify and Start the Run')}}</h3>
<br>
{{_('Do you want to start the run?')}}

<form>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
		<!--
        <td></td>
        <td><input type="button" id="download_button" value={{_("Download")}}></td>
        <td></td>
        -->
        <td></td>
        <td width=10%><input type="button" id="cancel_button" value={{_("Cancel")}}></td>
        <td width=10%><input type="button" id="next_button" value={{_("Start Execution")}}></td>
      </tr>
    </table>
</form>

<script>

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-run/back"
	});

	var btn = $("#cancel_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-run/next"; // but without calling to start the run
	});

	/*
	var btn = $("#download_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}download-model?model="+{{modelId}}
	});
	*/

	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		modelId = {{modelId}};
		$.getJSON("{{rootPath}}json/run-start",{ modelId:modelId, runName:'{{runName}}' })
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					alert('{{_("Warning! Do not turn off your machine!")}}');
					window.location = "{{rootPath}}model-run/next";									
				}
				else {
					alert('{{_("Sorry; the run failed to start")}}');
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
 