%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<h3>{{_('Beginning a HERMES Run')}}</h3>

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
<!--
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value="{{_("Previous Screen")}}"></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value="{{_("Next Screen")}}"></td>
      </tr>
    </table>
-->
</form>

<!--
<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_("The name of the run results must not be blank.")}}</p>
</div>
-->

<script>

$(function() {
	$(document).hrmWidget({widget:'stdBackNextButtons',
		getParms:function(){
			var runName = $("#run_results_name").val();
			var modelId = $("#run_model_id_select").val();
			return {runName:runName, modelId:modelId};
		},
		checkParms:function(parmDict) {
			if (parmDict.runName.length == 0)
				return {success:false, msg:'{{_("Please provide a valid run name")}}'}
			else
				return ($.getJSON('{{rootPath}}check-unique',parmDict)
						.then( function(data) {
							if (data['matches'] == 0) return {success:true}
							else {
								var msg = '{{_("The run name ")}}'+parmDict['runName']+'{{_(" has already been used for this model.  Please pick another name.")}}';
								return {success:false, msg:msg}							
							}
						})
						.promise());
		},
		nextURL:'{{! breadcrumbPairs.getNextURL() }}',
		backURL:'{{! breadcrumbPairs.getBackURL() }}'
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
 