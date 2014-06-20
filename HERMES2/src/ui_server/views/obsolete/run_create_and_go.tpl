%rebase outer_wrapper title_slogan="Run A Model Simulation", pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<h3>This page begins a track that leads to actually submitting a job.</h3>
The steps are (based on discussion 6/27/2013):
<ol>
<li>(Specify model to run?)</li>
<li>Reality Check</li>
<li>Name the model output</li>
<li>Set some run specifics.  (Long discussion about how much could/should be hidden from naive users).
<ul>
<li>duration</li>
<li>burn-in</li>
<li>seed</li>
<li>how many instances</li>
</ul>
</li>
<li>Summary of inputs (as per skeleton)</li>
<li>Are you sure you want to run? (happy face/worried face)
<ul><li>yes</li><li>no</li><li>download zip</li></ul>
</li>
<li>Can we give them a run time estimate (or percent done?)</li>
<li>Warning: don't turn off your machine!</li>
</ol>
<h3>Of course none of this is implemented yet</h3>
<input type="button" id="run_start_button" value="Run">
<script>
$(function() {
	var btn = $("#run_start_button");
	btn.button();
	btn.click( function() {
		$.getJSON("json/run_start",{modelId:24})
		.done(function(data) {
			alert("Started model running");
			window.location = "/bottle_hermes/run_top";			
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
	});
});
</script>
 