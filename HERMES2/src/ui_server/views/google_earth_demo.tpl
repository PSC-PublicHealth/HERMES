%rebase outer_wrapper title_slogan=_("Results Heirarchy Demo"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,runId=runId
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

