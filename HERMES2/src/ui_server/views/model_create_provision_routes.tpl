%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs, _=_, inlizer=inlizer

<script src="{{rootPath}}static/uisession.js"></script>
<script>
var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
var modelInfo = ModelInfoFromJson(modJson);
</script>

<h1>{{_('What Are The Details Of Each Transport Route?')}}</h1>
{{_('The shipping network for {0} has been created, but details must be specified for shipping between levels.').format(name)}}
{{_('All routes at a given level will be equipped as you describe below.  You can modify individual routes by editing the model.')}}
<p>
<form>
  	<table id = "provision_route_levels"></table>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
      </tr>
    </table>
</form>
<div id="model_route_add_dialog">
	<div id="model_route_add_div"></div>
</div>

<script>
for (var i = 0; i < modelInfo.nlevels; i++){
	var levelN1 = modelInfo.levelnames[i];
	for (j = 0; j < modelInfo.nlevels; j++){
		var levelN2 = modelInfo.levelnames[j];
		if(modelInfo.canonicalroutesdict[levelN1][levelN2]){
			$("#provision_route_levels").append("<tr><td>{{_('For routes between levels')}}</td>" +
					"<td><div id='model_create_provroute_b_"+i+"_"+j+"'>"+levelN1+ " {{_('and')}} " + levelN2 + "</div></td></tr>");
		}
	}
}

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
		window.location = "{{rootPath}}model-create/next?provisionroutes=true";  // settings already sent via ajax
	});
});

$(function () {
	var btn;
	$('[id^=model_create_provroute_b_]').button();
	
	$('[id^=model_create_provroute_b_]').click(function(e){
		e.preventDefault();
		var thisLstr = $(this).prop('id').replace('model_create_provroute_b_','');
		var thisL1 = parseInt(thisLstr.split('_')[0]);
		var thisL2 = parseInt(thisLstr.split('_')[1]);
		$("#model_route_add_div").remove();
		$("#model_route_add_dialog").dialog({
			autoOpen:false,
			height:"auto",
			width:"auto",
			buttons: {
				'{{_("OK")}}':function(){
					$(this).find('form').submit();
				},
				'{{_("Cancel")}}':function(){
					$(this).dialog("close");
				}
			}
		});
		$("#model_route_add_dialog").append("<div id='model_route_add_div'>New Dialog</div>");
		$("#model_route_add_dialog").hrmWidget({
			widget:'routeEditor',
			modelId:{{modelId}},
			routename:modelInfo.canonicalroutesdict[modelInfo.levelnames[thisL1]][modelInfo.levelnames[thisL2]],
			closeOnSuccess:'model_route_add_dialog',
			afterBuild:function() { 
				$('#model_add_route_dialog').dialog('open'); 
			}
		})
		$("#model_route_add_dialog").dialog("open");
	});
});

</script>
