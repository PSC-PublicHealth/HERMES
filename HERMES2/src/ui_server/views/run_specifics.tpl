%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,developer=developer
<h3>{{_('Provide Some Details')}}</h3>
<table>
<col align='right'>
<col align='left'>
<col align='center'>

<tr>
<td><label for="n_instances">{{_("Run how many instances?")}}</label></td>
<td><input type="number" min="1" 
%if defined('nInstances'):
	value={{nInstances}}
%else:
	value=1
%end
	id="n_instances"></td>
</tr>

%if developer:
<tr>
<td><label for="set_seeds_checkbox">{{_("Set random seeds?")}}</label></td>
<td><input type="checkbox" id="set_seeds_checkbox"
%if defined('setseeds') and setseeds:
    checked
%end
    ></td>
<td>
	<div id='subtable' 
%if not defined('setseeds') or not setseeds:
	style='display:none'
%end
	></div>
</td>
</tr>
%end
%if developer:
<tr>
<td><label for="deterministic_checkbox">{{_("Try to be deterministic?")}}</label></td>
<td><input type="checkbox" id="deterministic_checkbox"
%if defined('deterministic') and deterministic:
    checked
%end
    ></td>
</tr>
%end
%if developer:
<tr>
<td><label for="perfect_checkbox">{{_("Run with Perfect Storage and Transport?")}}</label></td>
<td><input type="checkbox" id="perfect_checkbox"
	%if defined('perfect') and perfect:
		checked
	%end
	></td>
</tr>
%end
<tr>
<td colspan=2><input type="button" id="edit_parms_button" value="{{_('Edit Parameters?')}}"></td>
</tr>
</table>

<form>
    <table width=100%>
      <tr>
        <td width=10%><input type="button" id="back_button" value="{{_("Previous Screen")}}"></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value="{{_("Next Screen")}}"></td>
      </tr>
    </table>
</form>

<script>

function generateSeedTable(nSlots) {
	var s = '<table>	<tr><th>{{_("Run")}}</th><th>{{_("Seed")}}</th></tr>';
	for (var i = 0; i < nSlots; i++) {
		s += '<tr><td>';
		s += (i+1).toString();
		var idStr = 'seed_'+i.toString();
		s += '</td><td><input type="number" id="'+idStr+'"></td></tr>';
	};
	s += '</table>';
	return s;
};

$(function() {
	$('#set_seeds_checkbox').click(function () {
		var nSeeds = $("#n_instances").val();
		$("#subtable").html(generateSeedTable(nSeeds));
	    $("#subtable").toggle(this.checked);
	});	
	
	$('#n_instances').change( function() {
		$("#subtable").html(generateSeedTable($(this).val()));
	});

%if defined('nInstances') and defined('seeds'):
	$("#subtable").html('{{!generateInitialSeedTable(nInstances,seeds)}}');	
%else:
	$("#subtable").html(generateSeedTable($("#n_instances").val()));
%end
});

function getParmString() {
	var nSeeds = $("#n_instances").val();
	var deterministicChecked = $("#deterministic_checkbox").is(":checked")
	var s = '?nInstances='+nSeeds.toString();
	var deterministicChecked = $("#deterministic_checkbox").is(":checked")
	s += '&deterministic='+deterministicChecked.toString();
	var perfectChecked = $('#perfect_checkbox').is(':checked')
	s += '&perfect='+perfectChecked.toString();
	var seedsChecked = $("#set_seeds_checkbox").is(":checked")
	s += '&setseeds='+seedsChecked.toString();
	for (var i = 0; i<nSeeds; i++) {
		var idStr = 'seed_'+i.toString();
		var seedVal = $('#'+idStr).val();
		if (seedVal == undefined) {
			s += '&'+idStr+'=';			
		}
		else {
			s += '&'+idStr+'='+seedVal.toString();			
		}
	};
	return s;
};

$(function() {
	var btn = $("#edit_parms_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-run/edit-parms"+getParmString();
	});
});

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-run/back";
	});
});

var btn = $("#next_button");
btn.button();
btn.click( function() {
	window.location = "{{rootPath}}model-run/next"+getParmString();
});


</script>
 