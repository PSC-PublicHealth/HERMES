%rebase outer_wrapper title_slogan=slogan, breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
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
<script type="text/javascript" src="{{rootPath}}static/jstree-v.pre1.0/jquery.jstree.js"></script>
<script src="{{rootPath}}static/base64v1_0.js"></script>
<script src="{{rootPath}}static/model_edit.js"></script>


% Attrs = [
%    { 'field' : "Name",         'type' : 'store', 'title' : _('names') },
%    { 'field' : "Category",     'type' : 'store', 'title' : _('categories') },
%    { 'field' : "LatLon",       'type' : 'store', 'title' : _('lat / lon') },
%    { 'field' : "UseVials",     'type' : 'store', 'title' : _('use vials') },
%    { 'field' : "UtilizationRate", 'type' : 'store', 'title' : _('utilization rate') },
%    { 'field' : "Demand",       'type' : 'store', 'title' : _('population') },
%    { 'field' : "fridges",      'type' : 'store', 'title' : _('storage') },
%    { 'field' : "trucks",       'type' : 'store', 'title' : _('transport') },
%    { 'field' : "SiteCost",     'type' : 'store', 'title' : _('site cost')},
%    { 'field' : "Notes",        'type' : 'store', 'title' : _('notes') },
%    { 'field' : "Name",         'type' : 'route', 'title' : _('route names') },
%    { 'field' : "Type",         'type' : 'route', 'title' : _('route types') },
%    { 'field' : "TransitHours", 'type' : 'route', 'title' : _('transit hours') },
%    { 'field' : "Distances",    'type' : 'route', 'title' : _('distances') },
%    { 'field' : "OrderAmount",  'type' : 'route', 'title' : _('order amounts') },
%    { 'field' : "TruckType",    'type' : 'route', 'title' : _('truck type') },
%    { 'field' : "Timings",      'type' : 'route', 'title' : _('route timings') },
%    { 'field' : "PerDiemType",  'type' : 'route', 'title' : _('per diem policy')},
%    { 'field' : "Conditions",   'type' : 'route', 'title' : _('route conditions') }
% ]

<style>
#em_content { width: 100%; height: 100%; top: 0; bottom: 0; }
#em_leftSide { 
    //overflow-y: scroll; 
    top: 0;
    bottom: 0;
    height: 100%;
    width: 70%;
    float: left;
}
#em_rightSide { 
    //overflow-y: scroll; 
    top: 0;
    bottom: 0;
    height: 100%;
    width: 30%;
    float: right;
}
</style>

<div id="model_edit_info_dialog" title="This should get replaced"></div>

<h2>{{_('Edit model')}}</h2>
<table>
  <tr>
    <td>
<ul class='em_disp_menu'>
  <li class='no_ul'><a href="#">{{_('store viewing options')}}</a>
    <ul>
      % for a in Attrs:
      %     if not a['type'] == 'store': 
      %         continue 
      %     end
      %     f = a['field']
      %     t = a['title']
       <li class='no_ul'>
	 <a href="#">{{_('store {0}').format(t)}}</a>
	 <ul>
	   <li class='no_ul' onclick="show_attr('store{{f}}')"><a href="#">{{_('edit store {0}').format(t)}}</a></li>
	   <li class='no_ul' onclick="ro_attr('store{{f}}')"><a href="#">{{_('view store {0}').format(t)}}</a></li>
	   <li class='no_ul' onclick="hide_attr('store{{f}}')"><a href="#">{{_('hide store {0}').format(t)}}</a></li>
	 </ul>
       </li>
      %end
<!--
      <li class="storeName_Button", onclick="toggle_attr('storeName')"><a class='no_ul' href="#">toggle store names</a></li>
-->
    </ul>
  </li>
</ul>
</td>
<td>
<ul class='em_disp_menu'>
  <li class='no_ul'><a href="#">{{_('route viewing options')}}</a>
    <ul>
      % for a in Attrs:
      %     if not a['type'] == 'route': 
      %         continue 
      %     end
      %     f = a['field']
      %     t = a['title']
       <li class='no_ul'>
	 <a class="no_ul" href="#">{{_('route {0}').format(t)}}</a>
	 <ul>
	   <li class='no_ul' onclick="show_attr('route{{f}}')"><a href="#">{{_('edit route {0}').format(t)}}</a></li>
	   <li class='no_ul' onclick="ro_attr('route{{f}}')"><a href="#">{{_('view route {0}').format(t)}}</a></li>
	   <li class='no_ul' onclick="hide_attr('route{{f}}')"><a href="#">{{_('hide route {0}').format(t)}}</a></li>
	 </ul>
       </li>
      % #       <li class="route{{c}}_Button", onclick="toggle_attr('route{{c}}')"><a class="no_ul" href="#">toggle route {{c}}</a></li>
      %end

    </ul>
  </li>
</ul>
</td>
<td>
  <ul class='em_disp_menu'>
    <li class='no_ul'>
      <a href="#">{{_('Model Validation')}}</a>
      <ul>
	<li class='no_ul' onclick="validateModel()">
	  <a href="#">{{_('Validate Model')}}</a>
	</li>
	<li class='no_ul' onclick="clearMessages()">
	  <a href="#">{{_('Clear Messages')}}</a>
	</li>
      </ul>
    </li>
  </ul>
</td>
  </tr>
</table>

<div id="em_context">
    <p>{{_('Route to use as template for newly created routes:')}} 
        <span id='routeTemplateText'>None</span>
        <button type="button" onclick="clearRouteTemplate()">{{_('Clear')}}</button>
    </p>
</div>
<div id="em_content">
    <div id="em_leftSide">
        <div id="modelTree"></div>
    </div>
    <div id="em_rightSide">
        <div id="orphanTree"></div>
    </div>
</div>
<script>
  $(function() {
    $( ".em_disp_menu" ).menu();
  });
</script>
<!-- script>
  $(function() {    
    $( ".em_disp_menu_2" ).menu({ position: { my: "left top", at: "right top" } });

    $( ".em_disp_menu_1" ).menu({ position: { my: "left top", at: "left bottom" } });
  });
    
</script -->
<style>
  .ui-menu { width: 200px; }
</style>
<script>
var modelId = {{modelId}};
var extraContext = {'routeTemplate' : null};

var Attrs = {
% for a in Attrs:
    "{{a['type']}}{{a['field']}}" : { 'type': '{{a['type']}}', 'title': '{{a['title']}}' },
%end
};

var TreeLabels = {
    'A' : '#modelTree',
    'B' : '#orphanTree'
};

</script>
<script>
//$(window).bind('beforeunload',function(){
//	$.ajax({
//		url:'{{rootPath}}json/removeD3Model?modelId={{modelId}}',
//		async:false
//	});
//	//return "";
//});

$(function() {
	$.ajax({
		url:'{{rootPath}}json/removeD3Model?modelId={{modelId}}',
		async:false
	});
	
    $('#modelTree')
	.bind("load_node.jstree", function (event, data) {
	    loadNode(event, data);
	})
        .bind("open_node.jstree", function (event, data) {
	    openNode(event, data);
	})
	.bind("close_node.jstree", function(event, data) {
	    closeNode(event, data);
	})
	.jstree({
	    "plugins" : ["core", "themes", "json_data", "ui", "crrm"],
	    //"plugins" : ["core", "themes", "html_data", "ui", "crrm"],
	    "themes" : { "theme" : "classic", "icons" : false },
	    "core" : {"html_titles" : true , "animation" : 50 },
	    "json_data" : {
		"ajax" : {
		    "url" : "json/modelRoutes/{{modelId}}",
		    "data" : function(n) { return { id : n.attr ? n.attr("id") : 'A-1' }; },
                    "dataFilter" : function(data, type) {
                        data = jQuery.parseJSON(data);
			success = data.success;
			if (!success) {
			    if('errorString' in data) {
				alert("{{_('error fetching node: ')}}"+data.errorString);
			    } else {
				alert("{{_('error fetching node')}}");
			    }
			    return NULL;
			}
			$.merge(updatesSavedForLoadNode, data.updates);
                        return JSON.stringify(data.data);
                    },
                    "success" : function(result) {
                        //alert('success');
                    },
                    "error" : function(jqxhr, textStatus, error) {
                        alert("{{_('error fetching route tree')}}");
                    } 
		}
	    }
	});
});
</script>

<script>
$(function() {
    $('#orphanTree')
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
		    "url" : "json/modelRoutes/{{modelId}}",
		    "data" : function(n) { return { id : n.attr ? n.attr("id") : 'B-2' }; },
                    "dataFilter" : function(data, type) {
                        data = jQuery.parseJSON(data);
			success = data.success;
			if (!success) {
			    if('errorString' in data) {
				alert("{{_('error fetching node: ')}}"+data.errorString);
			    } else {
				alert("{{_('error fetching node')}}");
			    }
			    return NULL;
			}
			$.merge(updatesSavedForLoadNode, data.updates);
                        return JSON.stringify(data.data);
                    },
                    "success" : function(result) {
                        //alert('success');
                    },
                    "error" : function(jqxhr, textStatus, error) {
                        alert("{{_('error fetching unattached route tree')}}");
                    }

		}
	    }
	});
});
</script>
<script>
</script>

<div id="storeEditorParent"></div>

<script>
$(function () {
	$('#storeEditorParent').data('kidcount',0);
});

</script>

<script>
    {{!setupToolTips()}}
    $(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); })
</script>
