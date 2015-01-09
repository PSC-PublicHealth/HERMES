%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs, _=_, inlizer=inlizer

<script src="{{rootPath}}static/uisession.js"></script>
<script>
var modJson = JSON.parse('{{modJson}}'.replace(/&quot;/g,'"'));
var modelInfo = ModelInfoFromJson(modJson);
</script>
<h1>{{_('What Equipment And Population Exist At Each Level?')}}</h1>
{{_('The shipping network for {0} has been created, but equipment and population must be specified at each level.').format(name)}}
{{_('All locations at a given level will be equipped as you describe below.  You can modify individual locations by editing the model.')}}
<p>
<form>
  	<table id = "provision_levels"></table>

    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value="{{_("Previous Screen")}}"></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value="{{_("Next Screen")}}"></td>
      </tr>
    </table>
</form>
<div id="model_store_add_dialog">
 	<div id="model_store_add_div"></div>
</div>


<script>
for(var i = 0; i < modelInfo.nlevels; i++){
	var locString = '{{_("For the locations at level: ")}}';
	if(modelInfo.levelcounts[i] == 1)
		locString = '{{_("For the location at level: ")}}';
	
	$('#provision_levels').append("<tr><td>"+locString+"</td><td><div id = 'model_create_prov_b_"+i+"'>"+modelInfo.levelnames[i]+"</div></td></tr>");
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
		window.location = "{{rootPath}}model-create/next?provision=true";  // settings already sent via ajax
	});
});

$(function () {	
	$('[id^=model_create_prov_b]').button();
	
	$('[id^=model_create_prov_b]').click(function(e){
		e.preventDefault();
		var thisLevNum = parseInt($(this).prop('id').match(/\d+/));
		$("#model_store_add_div").remove();
		$("#model_store_add_dialog").dialog({
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
		$("#model_store_add_dialog").append("<div id='model_store_add_div'>NewDiv</div>");
		//alert("modelInfo.canonicalstoresdict[modelInfo.levelnames[thisLevNum]]");
		$("#model_store_add_div").hrmWidget({
			widget:'storeEditor',
			idcode:modelInfo.canonicalstoresdict[modelInfo.levelnames[thisLevNum]],
			modelId:{{modelId}},
			closeOnSuccess:'model_store_add_dialog',
			afterBuild:function(){
				$('#model_store_add_dialog').dialog('open');
			}
		});
	});
});

</script>
