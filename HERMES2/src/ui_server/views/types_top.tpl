% title_slogan=_("Choose Types")
% rebase outer_wrapper **locals()

<script src="{{rootPath}}static/base64v1_0.js"></script>
<script>
%if defined('createpipe'):
	var createOn = true;
%else:
	var createOn = false;
%end
</script>

% typesEntries = [
%    ['vaccines', _('Vaccines'),    'json/vaccine-info', 'vaccine-edit'],
%    ['trucks',   _('Transport'),   'json/truck-info',   'truck-edit'],
%    ['fridges',  _('Storage'),     'json/fridge-info',  'fridge-edit'],
%    ['people', _('Population'),    'json/people-info',  'people-edit'],
%    ['perdiems', _('PerDiem Rules'),    'json/perdiem-info',  'perdiem-edit'],
%    ['staff', _('Staff'),    'json/staff-info',  'staff-edit'],
% ]

% def unpackTypesEntry(te):
%    ret = {}
%    ret['type'] = te[0]
%    ret['name'] = te[1]
%    ret['infoUrl'] = te[2]
%    ret['editUrl'] = te[3]
%    return ret
% end

<h2>
	{{_('Edit Compnents')}}
</h2>
<h4>
	{{_('Use the Source dropdown to select the source from which components can be selected.  Select which component to add to the {0} model and click the arrow button to add it. To remove existing components, click delete.'.format(modelName))}}
</h4>
<table>
  <tr>
    <td>
      <table> 
        <tr><td style="height:20px">
        </td></tr>
        % for te in typesEntries:
	%     t = unpackTypesEntry(te)
	<tr><td>
	    <button id="{{t['type']}}_button" style="width:100%">{{t['name']}}</button>
	</td></tr>
	% end
      </table>
    </td>
    <td>
      <table>
	<tr><td style="height:20px" id='dest_header'>
          {{_('Current type') }}
	</td></tr>
	<tr><td>
	    <table id='dest_grid'></table>
	</td></tr>
	<tr><td>
	    <div id='dest_pager'></div>
	</td></tr>
      </table>
    </td>
    <td>
      <table id='middle'>
        <tr><td style="height:80px"></td></tr>
        <tr><td>
	  <button id="copy_to_model_button">{{_('<--')}}</button>
        </td></tr>
        <tr><td></td></tr>
      </table>
    </td>
    <td>
      <table>
	<tr><td style="height:20px" id='src_header'>
	    <label for="src_model_select">{{_('source')}}</label>
	    <select name="src_model_select" id="src_model_select"></select>
	</td></tr>
	<tr><td>
	    <table id='src_grid'></table>
	</td></tr>
	<tr><td>
	    <div id='src_pager'></div>
	</td></tr>
      </table>
    </td>
% if 0: # until this button has functionality, hide it
    <td>
      <table>
      <tr><td style='height:60px'></td></tr>
      <tr><td>
	  <button id="copy_to_model_button">{{_('Create Empty DB')}}</button>
      </td></tr>
      <tr><td></td></tr>
      </table>
    </td>
% end
  </tr>
</table>
<table id="nextback" width=100%>
	<tr>
		<td width=10%>
			<input type="button" id="back_button" value='{{_("Previous Screen")}}'>
		</td>
		<td width=70%>
		</td>
		<td width=10%>
			<input type="button" id="expert_button" value='{{_("Skip to Model Editor")}}'>
		</td>
		<td width=10%>
			<input type="button" id="next_button" value='{{_("Next Screen")}}'>
		</td>
	</tr>
</table>
<table id="doneback" width=100%>
<tr>
	<td width=90%>
	</td>
	<td width=10%>
		<input type="button" id="done_button" value='{{_("Done")}}'>
	</td>
	
</tr>
</table>


<div id="info_dialog" title='replace me'></div>
<script>
// many characters in a jquery id need escaped.
function jId(i) {
    return '#' + i.replace( /(:|\.|\[|\]|\+|\=|\/)/g, "\\$1");
}

var modelId = {{modelId}};
var modelName = "{{modelName}}";
var myURL = "{{rootPath}}{{baseURL}}?id={{modelId}}"

var typesMap = {
% for t in typesEntries:
    '{{t[0]}}' : { 'dispName' : '{{t[1]}}', 
                   'infoUrl'  : '{{rootPath}}{{t[2]}}',  
                   'editUrl'  : '{{rootPath}}{{t[3]}}',
                 },
% end
};

var currentType = '{{startClass}}';

function setCurrentType(t) {
//    alert(t);
    var prevBtn = $('#' + currentType + '_button');
    var btn = $('#' + t + '_button');
//    prevBtn.prop('disabled', false);
//    btn.prop('disabled', true);
    prevBtn.button("enable");
    btn.button('disable');
    currentType = t;
    //alert(currentType);
    $('#dest_header').html(typesMap[t].dispName + "{{_(' in ')}}" + modelName);
    populateSrcModelSelect();
    reloadGrid(dest);
}
    
// types buttons

function setSetCurrentType(t) {
    return function() { setCurrentType(t); };
}

$(function() {
    // startup stuff
    // set up our left hand buttons
    for (var t in typesMap) {
	var btn = $('#' + t + '_button');
	btn.button();
	btn.click( setSetCurrentType(t) );
//	btn.click( "setCurrentType('" + t + "')" );
    }
    setCurrentType('{{startClass}}');

    var btn = $('#copy_to_model_button')
    btn.button();
    btn.click( copySelected );

    // info dialog
    $("#info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
    
    if(createOn){
		var btn = $("#back_button");
		btn.button();
		btn.click( function() {
			window.location = "{{rootPath}}model-create/back"
		});
		
		var btn = $("#next_button");
		btn.button();
		btn.click( function() {
			window.location = "{{rootPath}}model-create/next";
		});
		
		var btn = $("#expert_button");
		btn.button();
		btn.click( function() {
			window.location = "{{rootPath}}model-create/next?expert=true";
		});
		$("#doneback").remove();
    }
    else{
		var btn = $("#done_button");
		btn.button();
		btn.click( function() {
			window.location = "javascript:history.back()";
		})
		
		$("#nextback").remove();
	}
});

// dest and src jqGrids

var dest = {
    id : '#dest_grid',
    modelId : "{{modelId}}",
    lastSel : null,
    lastSelName : null,
};
var src = {
    id : '#src_grid',
    modelId : null,
    lastSel : null,
    lastSelName : null,
};

var grids = [dest, src];

function reloadGrid(grid) {
    grid.lastSel = null;
    grid.lastSelName = null;
    $(grid.id).trigger("reloadGrid");
}

function selectRow(id, grid) {
    if (!id)
	return;
    if (id == grid.lastSel)
	return;

    if (grid.lastSel) {
//	$(jId(grid.lastSel)).children().css("background-color", "");
    }

    grid.lastSelName = $(grid.id).jqGrid('getCell', id, 'name');
    grid.lastSel = id;
//    $(jId(grid.lastSel)).children().css("background-color", "green !important");
}

function clone(object) {
    return JSON.parse(JSON.stringify(object));
}

var columnNames = [
    "{{_('Name')}}",
    "{{_('RealName')}}",
    "{{_('ModelId')}}",
    "{{_('Info')}}",
];

var columnModelSrc = [
    {name: 'dispName', width:250, index: 'dispName'},
    {name: 'name', index: 'name', hidden: true},
    {name: 'modelId', index: 'modelId', hidden: true},
    {name: 'flags', index: 'flags', align:'center', formatter:infoFormatter},
];

var columnModelDest = clone(columnModelSrc);
var flagsColumn = 3;
if (columnModelDest[flagsColumn].name != 'flags')
    alert('column model definitions are out of synch!');
else
    columnModelDest[flagsColumn].formatter = tripleFormatter;



function unpackRowObject(row) {
    ret = {};
    ret.dispName = row[0];
    ret.name = row[1];
    ret.modelId = row[2];
    ret.flags = row[3];
    return ret;
}

function packId(rowObject) {
    row = unpackRowObject(rowObject);
    id = "" + row.modelId + ":" + B64.encode(row.name);
    return id;
}

function unpackId(id) {
    var parts = id.split(':');
    var ret = {};
    ret.modelId = parts[0];
    ret.name = B64.decode(parts[1]);
    ret.grid = null;
    for (gIndex in grids) {
	g = grids[gIndex];
	if (g.modelId == ret.modelId) {
	    ret.grid = g;
	}
    }

    return ret;
}

function infoFormatter(value, options, rowObject) {
    s = "";
    s += "<button class='new_hermes_info_button' onclick='infoType(\""
    s += packId(rowObject);
    s += "\");'>{{_('info')}}</button>";
    return s;
    return "<div class='new_hermes_info_button' id='bt_" + packId(rowObject) + "'></div>";
}

function tripleFormatter(value, options, rowObject) {
    if (value == 'R') { 
	return "<div class='new_hermes_button_triple_R' id='bt_" + packId(rowObject) + "'></div>";
    } else {
	return "<div class='new_hermes_button_triple_RW' id='bt_" + packId(rowObject) + "'></div>";
    }
}

function getRemoveConfirm(data, name) {
    var deps = data.value;
    var s = "";

    s += "{{_('Remove type: ')}}" + name;
    s += "<hr/>";
    if (deps.length == 0) {
	s += "{{_('Do you really wish to remove all instances of this type?')}}";
    } else {
	s += "{{_('This type is used by the following types:  ')}}";
	s += "<ul><li>";
	s += deps.join('</li><li>');
	s += "</li></ul>";
	s += "<hr/>";
	s += "{{_('Do you really wish to remove all instances of this type and its dependents?')}}";
    }

    var defer = $.Deferred();

    $('<div></div>').html(s)
	.dialog({
	    autoOpen: true,
	    modal: true,
	    title: '{{_("Confirm Additional Removals?")}}',
	    close: function() { $(this).dialog('destroy'); },
	    buttons: {
		'{{_("Remove")}}': function() {
		    $(this).dialog("close");
		    defer.resolve({success:true});
		},
		'{{_("Cancel")}}': function() { 
		    $(this).dialog("close");
		    defer.reject({success:false, msg:'Cancelled'});
		}
	    }
	});
    return defer.promise();
}

function delType(id) {
    //event.stopPropagation();
    
    upId = unpackId(id);
    var modelId = upId.modelId;
    var name = upId.name;
    var grid = upId.grid;

    $.getJSON('{{rootPath}}json/type-check-dependent-types',
	      {name:name, modelId:modelId})
	.then( function(data) {
	    if (data.success) return getRemoveConfirm(data, name);
	    else return $.Deferred().reject(data).promise();
	})
	.then( function() {
	    var request = $.ajax( {
		url:'{{rootPath}}json/removeTypeFromModel',
		data : { 'modelId' : modelId,
			 'typeName' : name },
		success: function(data, textStatus, jqXHR) {
		    reloadGrid(grid);
		},
	    });
	});
}

function infoType(id) {
    //event.stopPropagation();

    upId = unpackId(id);
    var modelId = upId.modelId;
    var name = upId.name;
    var grid = upId.grid;

    var jsonFn = typesMap[currentType].infoUrl;

    $.getJSON(jsonFn,{name:name, modelId:modelId})
	.done(function(data) {
	    if (data.success) {
		$("#info_dialog").html(data['htmlstring']);
		$("#info_dialog").dialog('option','title',data['title']);
		$("#info_dialog").dialog("open");	
	    }
	    else {
    		alert('{{_("Failed: ")}}'+data.msg);
	    }
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert("Error: "+jqxhr.responseText);
	});
    
}

function editType(id) {
    

    upId = unpackId(id);
    var modelId = upId.modelId;
    var name = upId.name;
    var grid = upId.grid;

    var url = typesMap[currentType].editUrl;
    var parms = '?modelId=' + modelId;
    parms += "&protoname='" + name + "'";
    parms += "&overwrite=1";
    parms += "&backURL=" + B64.encode(myURL + "&startClass=" + currentType)
    window.location = url + parms;
}
	    

function setupButtonTriples() {
//    $('.new_hermes_button_triple').each(function() {

    $('.new_hermes_button_triple_RW').hrmWidget({
	widget:'buttontriple',
	onDel:function(event) {
		event.stopPropagation();
	    var id = $(this).parent().attr("id");
	    id = id.slice(3);  // remove 'bt_'
	    delType(id);
	},
	onInfo:function(event) {
		event.stopPropagation();
	    var id = $(this).parent().attr("id");
	    id = id.slice(3);  // remove 'bt_'
	    infoType(id);
	},
	onEdit:function(event){
		event.stopPropagation();
	    var id = $(this).parent().attr("id");
	    id = id.slice(3);  // remove 'bt_'
	    editType(id);
	},
    });
    
    $('.new_hermes_button_triple_RW').each(function() {
	$(this).removeClass('new_hermes_button_triple_RW');
	$(this).addClass('hermes_button_triple');
    });

    $('.new_hermes_button_triple_R').hrmWidget({
	widget:'buttontriple',
	onInfo:function(event) {
	    var id = $(this).parent().attr("id");
	    id = id.slice(3);  // remove 'bt_'
	    infoType(id);
	},
    });
    
    $('.new_hermes_button_triple_R').each(function() {
	$(this).removeClass('new_hermes_button_triple_R');
	$(this).addClass('hermes_button_triple');
    });
}

$("#dest_grid").jqGrid({
    url : '{{rootPath}}json/types-manage-grid',
    datatype : 'json',
    rowNum:9999,
    height:300,
    postData : {
	modelId : {{modelId}},
	type : function() { return currentType; },
    },
    colNames: columnNames,
    colModel: columnModelDest,
    pager: '#dest_pager',
    pgbuttons: false,
    pginput: false,
    sortname: 'dispName',
    viewerecords: true,
    sortorder: 'asc',
    gridview: true,
    onSelectRow: function(id) {
	selectRow(id, dest);
    },
    gridComplete: function() { setupButtonTriples(); },
    
    // editurl:
    caption: "{{_('used types')}}",
});

$("#dest_grid").jqGrid('navGrid', '#dest_pager', {edit:false, add:false, del:false});

function catchNewType(event, ui, data, $source, $target) {
    ui.helper.dropped = false;
    //alert(data.name);
    copyType(data.name);
}

$("#src_grid").jqGrid({
    url : '{{rootPath}}json/types-manage-grid',
    datatype : 'json',
    rowNum:9999,
    postData : {
	modelId : function() { return sel_model_id; },
	type : function() { return currentType; },
    },
    height:300,
    colNames : columnNames,
    colModel : columnModelSrc,
    pager: '#src_pager',
    pgbuttons: false,
    pginput: false,
    sortname: 'dispName',
    viewerecords: true,
    sortorder: 'asc',
    gridview: true,
    onSelectRow: function(id) {
	selectRow(id, src);
    },
    gridComplete: function() { 
	setupButtonTriples(); 
//	src.modelId = sel_model_id;
    },
    // editurl:
    caption: "{{_('available types')}}",
});
$("#src_grid").jqGrid('navGrid', '#src_pager', {edit:false, add:false, del:false});
$("#src_grid").jqGrid('gridDnD', {connectWith : '#dest_grid', 
				  dragcopy : true, 
				  beforedrop : catchNewType });

var sel_model_name = null;
var sel_model_id = null;

$(function() {
    var sel = $("#src_model_select");
    sel.change( function() {
    	sel_model_id = $("#src_model_select").val();
    	src.modelId = sel_model_id;
//		alert(sel_model_id);
    	$.getJSON('{{rootPath}}json/set-selected-model', {id : sel_model_id})
	    	.done(function(data) {
	    		sel_model_name = data['name'];
	    		$("#src_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
	    		reloadGrid(src);
	    	})
	    	.fail(function(jqxhr, textStatus, error) {
	    		alert("Error: "+jqxhr.responseText);
	    	});
    });
    populateSrcModelSelect();
});

function populateSrcModelSelect() {
    $.getJSON('{{rootPath}}list/select-model-list', 
	      {'curType' : currentType, 
	       'curModel' : sel_model_id,
	       'ignoreModel' : {{modelId}}})
		.done(function(data) {
		    var sel = $("#src_model_select");
		    sel.html(data['menustr']);
		    sel_model_id = data['selid']
		    src.modelId = sel_model_id;
	    	sel_model_name = data['selname']
		    $("#src_grid").jqGrid('setLabel','usedin',"{{_('Used In ')}}"+sel_model_name);
		    reloadGrid(src);
		})
		.fail(function(jqxhr, textStatus, error) {
	  	    alert("Error: "+jqxhr.responseText);
		});
}

function copySelected() {
    return copyType(src.lastSelName);
}

function copyType(name) {
    var request = $.ajax( {
	url:'{{rootPath}}json/copyTypeToModel',
	data : { 'modelId' : {{modelId}},
		 	'srcModelId' : sel_model_id,
		 	'typeName' : name },
        success: function(data, textStatus, jqXHR) {
        	if (data.success) {
        	    reloadGrid(dest);        		
        	}
        	else {
				alert('{{_("Failed: ")}}'+data.msg);        		
        	}
        },
        error: function(jqxhr, textStatus, errorThrown) {
			alert('{{_("Error: ")}}'+jqxhr.responseText);
        }
    });

}

</script>
