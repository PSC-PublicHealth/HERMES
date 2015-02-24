%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs, _=_, inlizer=inlizer,pagehelptag=pagehelptag
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
<script src="{{rootPath}}static/uisession.js"></script>
<script>
var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
var modelInfo = ModelInfoFromJson(modJson);
</script>

<p>
	<span class="hermes-top-main">
		{{_('What and how many Transport Vehicles would you like shipping routes?')}}
	</span>
</p>
<p>
	<span class="hermes-top-sub">
		{{_('The shipping network for {0} has been created, and now you must define the vehicle that each route will use').format(name)}}
		{{_('All routes between given levels will use the vehicle specified below.  The supplier location will need to be allocated the vehicles, and you must specify the number of them that will be located at each supplier for the routes.')}}

	</span>
</p>
<form>
  	<table id = "provision_route_levels">
  	</table>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value="{{_("Previous Screen")}}"></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value="{{_("Next Screen")}}"></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title='{{_("Invalid Input Entry")}}'>
	<div id="dialog-modal-text"/>
	</div>
</div>

<script>
for (var i = 0; i < modelInfo.nlevels; i++){
	var levelN1 = modelInfo.levelnames[i];
	for (j = 0; j < modelInfo.nlevels; j++){
		var levelN2 = modelInfo.levelnames[j];
		if(modelInfo.canonicalroutesdict[levelN1][levelN2]){
			$("#provision_route_levels").append(
					"<tr><td>{{_('For Routes betweent the')}} <span style='font-weight:bold;'>"
					+levelN1+"</span> {{_('and the')}} <span style='font-weight:bold;'>"
					+levelN2+"</span> {{_('levels')}}:</td>"
					+"<td><select id='select_route_"+levelN1+"_"+levelN2+"' l1='"+levelN1+"' l2='"+levelN2+"'></select></td>" 
					+"<td>{{_('with the number of vehicles per location in the level being')}}</td>" 
					+"<td><input type=number id='num_route_"+levelN1+"_"+levelN2+"' l1='"
					+levelN1+"' l2='"+levelN2+"' value=1 style='text-align:center;'></input></td></tr>");
		}
	}
}

//Modal Dialog needed for reporting errors
$("#dialog-modal").dialog({
	resizable: false,
  	modal: true,
	autoOpen:false,
 	buttons: {
		OK: function() {
			$( this ).dialog( "close" );
    	}
    },
    open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
		if (e.keyCode == $.ui.keyCode.ENTER) {
		    e.preventDefault();
		    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
		}
	    };
    }
});
//populate transportation select boxes

$(function(){
	$.ajax({
		url:'{{rootPath}}json/get-transport-type-names-in-model',
		datatype:'json',
		data:{'modelId':modelInfo['modelId']}
	})
	.done(function(result){
		if(!result.success){
			alert(result.msg);
		}
		else if(result.values.length == 0){
			alert("{{_('There are no Transportation in thismodel.  Please go back to the Add/Remove Components page and please add some Transportation.')}}");
		}
		else{
			$("[id^='select_route_']").each(function(){
				$this = $(this);
				for(var i=0;i<result.values.length;i++){
					$this.append("<option value='"+result.values[i]+"'>"
							+ result.names[i]+"</option>");
				}
			});
		}
	})
	.fail(function(jqxhr, textStatus, error) {
		alert("Error: " + jqxhr.responseText);
	});	
	
	$('[id^="num_route_"]').each(function(){
		$(this).data('oldVal',$(this).val());
	});
	$('[id^="num_route_"]').change(function(){
		$(this).val(validate_vehiclecount($(this).val(),$(this).data('oldVal')));
		$(this).data('oldVal',$(this).val());
	});
});

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/back"
	});
});
	
$(function() {
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		routeData = []
		$("[id^='select_route_']").each(function(){
			countID = $(this).attr('id').replace('select_','num_');
			routeData.push({'l1':$(this).attr('l1'),'l2':$(this).attr('l2'),'vName':$(this).val(),'vcount':$("[id='"+countID +"']").val()});
		});
		$.ajax({
			url:'{{rootPath}}json/provision-routes',
			datatype:'json',
			data:{
				'modelId':modelInfo['modelId'],
				'routeData':JSON.stringify(routeData)
				},
			method:'post'
		
		})
		.done(function(result){
			if(!result.success){
				alert(result.msg);
			}
			else{
				window.location = "{{rootPath}}model-create/next";
			}
		})
		.fail(function(jqxhr, textStatus, error) {
			alert("Error: " + jqxhr.responseText);
		});
	});
});

function validate_vehiclecount(vehiclecount,origValue){
	if(isNaN(vehiclecount) || vehiclecount == ""){
		$("#dialog-modal-text").text("{{_('The number of vehicles per location per level must be a positive number.')}}");
		$('#dialog-modal').dialog("open");
		return origValue;
	}
	if (vehiclecount < 1) {
		$("#dialog-modal-text").text("{{_('The number of vehicles per locations per level cannot be negative or 0')}}");
		$("#dialog-modal").dialog("open");
		return origValue;
	}
	return vehiclecount;
}

</script>
