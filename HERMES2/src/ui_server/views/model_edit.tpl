%rebase outer_wrapper title_slogan=slogan, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<script src="{{rootPath}}static/model_edit.js"></script>

<div id="model_edit_info_dialog" title="This should get replaced"></div>

<h2>'Edit model'</h2>
    <button type="button" class="storeName_Button", onclick="toggle_attr('storeName')">toggle store names</button>
    <button type="button" class="storeCategory_Button", onclick="toggle_attr('storeCategory')">toggle category</button>
    <button type="button" class="storeLatLon_Button", onclick="toggle_attr('storeLatLon')">toggle lat / lon</button>
    <button type="button" class="storeUseVials_Button", onclick="toggle_attr('storeUseVials')">toggle use vials</button>
    <button type="button" class="storeUtilizationRate_Button", onclick="toggle_attr('storeUtilizationRate')">toggle utilization rate</button>
    <button type="button" class="storeDemand_Button", onclick="toggle_attr('storeDemand')">toggle demand</button>
    <button type="button" class="storefridges_Button", onclick="toggle_attr('storefridges')">toggle storage</button>
    <button type="button" class="storetrucks_Button", onclick="toggle_attr('storetrucks')">toggle transport</button>
    <button type="button" class="storeNotes_Button", onclick="toggle_attr('storeNotes')">toggle notes</button>

<div id="modelTree"></div>

<script>
var Attrs = {
    "storeCategory" : { 'type' : 'store', 'title' : 'categories' },
    "storeLatLon" :   { 'type' : 'store', 'title' : 'lat / lon' },
    "storeName" :     { 'type' : 'store', 'title' : 'store names' },
    "storeDemand" :   { 'type' : 'store', 'title' : 'demand' },
    "storefridges" :  { 'type' : 'store', 'title' : 'storage' },
    "storetrucks" :   { 'type' : 'store', 'title' : 'transport' },
    "storeUseVials" : { 'type' : 'store', 'title' : 'use vials' },
    "storeUtilizationRate" : { 'type' : 'store', 'title' : 'utilization rate' },
    "storeNotes" :    { 'type' : 'store', 'title' : 'notes' }
};

var TreeLabels = {
    'A' : '#modelTree'
};

</script>
<script>
$(function() {
    $('#modelTree')
	.bind("load_node.jstree", function (event, data) {
            fixNewNodes();
	})
	.jstree({
	    "plugins" : ["core", "themes", "json_data", "ui", "crrm"],
	    //"plugins" : ["core", "themes", "html_data", "ui", "crrm"],
	    "themes" : { "theme" : "classic", "icons" : false },
	    "core" : {"html_titles" : true , "animation" : 50 },
	    "json_data" : {
		"ajax" : {
		    "url" : "json/modelTree{{nr}}/{{modelId}}",
		    "data" : function(n) { return { id : n.attr ? n.attr("id") : "A-1" }; },
                    "dataFilter" : function(data, type) {
                        //alert (type);
                        data = jQuery.parseJSON(data);
                        //alert (data);
                        //alert (data.successString);
                        //alert (data.data[0].state);
                        return JSON.stringify(data.data);
                        data = jQuery.parseJSON(data);
                        return data.dataString;
                    },
                    "success" : function(result) {
                        //alert('success');
                    },
                    "error" : function(jqxhr, textStatus, error) {
                        alert('error');
                    } /*

		    if (jsonResult.success) {
			alert('here');
			return jsonResult.childList;
		    } else {
			alert('{{_("Failed (my msg): ")}}' + jsonResult.msg);
			return ['{{_("Fetch failed")}}'];
		    }
		},
		"error" : function(jqxhr, textStatus, error) {
		    alert('{{_("Error: ")}}' + jqxhr.responseText);
		}*/
		}
	    }
	});
});
</script>
