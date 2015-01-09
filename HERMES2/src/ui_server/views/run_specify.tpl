%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<h3>{{_('Beginning a Hermes Run')}}</h3>

{{_("As you finish each page, select the 'Next' button at the bottom right.  Once you have finished this short set of pages, the execution of your model will begin.  You can continue to modify or other models while this model is running.  If you leave this sequence of screens too early, your model will not begin running but you will be able to return to the sequence where you left off by selecting 'Run HERMES' again.")}}
<p>
<form>
  	<table>
  		<tr>
  			<td><label for="run_model_id_select">{{_('Which model do you wish to run?')}}</label></td>
  			<td><select name="run_model_id_select" id="run_model_id_select"></select></td>
  		</tr>
	  	<tr>
  			<td><label for="run_results_name">{{_('What name should be given to this set of results?')}}</label></td>
  			<td><input type="text" name="run_results_name" id="run_results_name" \\
%if defined('runName'):
value={{runName}} \\
%end
></td>
  		</tr>
    </table>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value="{{_("Previous Screen")}}"></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value="{{_("Next Screen")}}"></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_("The name of the run results must not be blank.")}}</p>
</div>

<script>

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-run/back"
	});

	$("#dialog-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				$( this ).dialog( "close" );
        	}
        }
	});

	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		var runName = $("#run_results_name").val();
		var modelId = $("#run_model_id_select").val();
		if (runName) {
			$.getJSON('{{rootPath}}check-unique',{runName:runName, modelId:modelId})
			.done(function(data) {
				if (data['matches'] == 0) {
					window.location = "{{rootPath}}model-run/next?runName="+runName+"&modelId="+modelId;
				}
				else {
					alert('{{_("The run name ")}}'+runName+'{{_(" has already been used for this model.  Please pick another name.")}}');
				}
			})
	  		.fail(function(jqxhr, textStatus, error) {
	  			alert("Error: "+jqxhr.responseText);
			});
		}
		else {
			$("#dialog-modal").dialog("open");
		}
	});
	
  	$.getJSON('{{rootPath}}list/select-model')
	.done(function(data) {
		var sel = $("#run_model_id_select");
    	sel.append(data['menustr']);
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert("Error: "+jqxhr.responseText);
	});
});


</script>
 