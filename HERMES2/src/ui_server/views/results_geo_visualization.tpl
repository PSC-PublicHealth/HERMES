%rebase outer_wrapper title_slogan=_("Geographic Visualization"), pageHelpText=pageHelpText, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId,levels=levels,maxpop=maxpop
<!---
-->
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/d3/topojson.v1.min.js"></script>
<script src="{{rootPath}}static/queue.min.js"></script>
<script src="{{rootPath}}static/hermes_info_dialogs.js"></script>
<script src="{{rootPath}}static/rainbowvis.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/rickshaw-master/rickshaw.css"/>
<link rel="stylesheet" href="{{rootPath}}static/linechart-widgets/linechart.css"/>
<script src="{{rootPath}}static/rickshaw-master/rickshaw.js"></script>
<script src="{{rootPath}}static/linechart-widgets/linechart.js"></script>
<script src="{{rootPath}}static/dimple.v2.1.2/dimple.v2.1.2.min.js"></script>
<script src="{{rootPath}}static/barchart-widgets/vaccine_availability_barchart.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/geographic-map-widgets/geographicMap.css"/>
<script src="{{rootPath}}static/geographic-map-widgets/geographicResultsMap.js"></script>

<script>

function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

var selectedStore = [];
var selectedRoute = [];
var openStoreDialogs = {};
var openRouteDialogs = {};
</script>
<div id="geowidgetTest"></div>
<p id="firefox_warning" hidden><b>{{_('There is a known bug showing routes in Firefox when zoomed in.')}}</b></p>
<script>
var LevList = [];
%for i in range(0,len(levels)):
	LevList.push("{{levels[i]}}");
%end

$("#geowidgetTest").geographicResultsMap({
	modelId:{{modelId}},
	resultsId:{{resultsId}},
	rootPath:"{{rootPath}}",
	levelList:LevList,
});

$(function() {
    if (navigator.userAgent.indexOf("Firefox") != -1) {
	$('#firefox_warning').removeAttr('hidden');
    }
});
</script>




</script>
