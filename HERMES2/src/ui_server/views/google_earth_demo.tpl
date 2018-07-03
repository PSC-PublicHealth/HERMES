%rebase outer_wrapper title_slogan=_("Results Heirarchy Demo"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,runId=runId
<!---
-->
<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript" src='{{rootPath}}static/google_earth.js'></script>

<script>

function getKMLString(ge){
	$.getJSON("{{rootPath}}json/google-earth-kmlstring?modelId={{modelId}}&resultsId={{runId}}")
		.done(function(data){
			if(data['success'] == false){
				alert("Error in creating a KML representation:\n" + data['msg']);
			}
			else{
				var kmlString = data.kmlString;
				parseKmlWrapper(ge,kmlString);
			}
	})
	.fail(function(jqxhr, textStatus, error){
		alert("Error: "+jqxhr.responseText);
	 });	
}
</script>
 
<link rel="stylesheet" type="text/css" href="/bottle_hermes/static/google_earth.css"/>

<div id="ge_map3d"></div>
<div id="ge_buttons">
<div id="ge_layers">
<table>
<tr><td colspan=3>
<p style="font-size:large;">Layers:</p>
</td></tr>
<tr>
<p style="font-size:medium;">
<td width="50px"></td><td>Population:</td><td width:"100px"> <input type="checkbox" id="ge_show_population" checked /></td></tr>
<td width="50px"></td><td>Utilization:</td><td width:"100px"> <input type="checkbox" id="ge_show_utilization" value="On"/></td></tr>
<td width="50px"></td><td>Vaccines:</td><td width:"100px"> <input type="checkbox" id="ge_show_vaccine" value="On"/></td></tr>
<td width="50px"></td><td>Routes:</td><td width:"100px"> <input type="checkbox" id="ge_show_routes" value="On"/></td></tr>
</table>
</p>

<div id="ge_content-for-iframe">
	<div id="ge_content"></div>	
</div>	
</div>

