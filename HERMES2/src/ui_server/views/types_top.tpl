% title_slogan=_("Choose Types")
% rebase outer_wrapper **locals()

<script src="{{rootPath}}static/base64v1_0.js"></script>

% typesEntries = [
%    ['vaccines', _('Vaccines')],
%    ['trucks',   _('Transport')],
%    ['fridges',  _('Storage')],
%    ['people', _('Population')],
% ]

% def unpackTypesEntry(te):
%    ret = {}
%    ret['type'] = te[0]
%    ret['name'] = te[1]
%    return ret
% end


<h2 style="text-align:center;">{{_('Choose Types For Model')}}</h2>
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
    <td>
      <table>
      <tr><td style='height:60px'></td></tr>
      <tr><td>
	  <button id="copy_to_model_button">{{_('Create Empty DB')}}</button>
      </td></tr>
      <tr><td></td></tr>
      </table>
    </td>
  </tr>
</table>

<script>
// many characters in a jquery id need escaped.
function jId(i) {
    return '#' + i.replace( /(:|\.|\[|\]|\+|\=|\/)/g, "\\$1");
}

var modelId = {{modelId}};
var modelName = "{{modelName}}";


var typesMap = {
% for t in typesEntries:
    '{{t[0]}}' : { 'dispName' : '{{t[1]}}' },
% end
};

var currentType = 'vaccines';

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
    setCurrentType('vaccines');

    var btn = $('#copy_to_model_button')
    btn.button();
    btn.click( copySelected );
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

var columnNames = [
    "{{_('Name')}}",
    "{{_('RealName')}}",
    "{{_('ModelId')}}",
    "{{_('Info')}}",
];

var columnModel = [
    {name: 'dispName', index: 'dispName'},
    {name: 'name', index: 'name', hidden: true},
    {name: 'modelId', index: 'modelId', hidden: true},
    {name: 'flags', index: 'flags', formatter:infoFormatter},
];

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
    event.stopPropagation();

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
		url:'json/removeTypeFromModel',
		data : { 'modelId' : modelId,
			 'typeName' : name },
		success: function(data, textStatus, jqXHR) {
		    reloadGrid(grid);
		},
	    });
	});
}

function infoType(id) {

}

function editType(id) {

}
	    

function setupButtonTriples() {
//    $('.new_hermes_button_triple').each(function() {

    $('.new_hermes_button_triple_RW').hrmWidget({
	widget:'buttontriple',
	onDel:function(event) {
	    var id = $(this).parent().attr("id");
	    id = id.slice(3);  // remove 'bt_'
	    delType(id);
	},
	onInfo:function(event) {
	    var id = $(this).parent().attr("id");
	    id = id.slice(3);  // remove 'bt_'
	    infoType(id);
	},
	onEdit:function(event){
	    var id = $(this).parent().attr("id");
	    id = id.slice(3);  // remove 'bt_'
	    infoType(id);
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
    postData : {
	modelId : {{modelId}},
	type : function() { return currentType; },
    },
    colNames: columnNames,
    colModel: columnModel,
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
    copySelected(data.name);
}

$("#src_grid").jqGrid({
    url : '{{rootPath}}json/types-manage-grid',
    datatype : 'json',
    rowNum:9999,
    postData : {
	modelId : function() { return sel_model_id; },
	type : function() { return currentType; },
    },
    colNames : columnNames,
    colModel : columnModel,
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
//	alert(sel_model_id);
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

function copySelected(name) {
    if (typeof name == 'undefined')
	name = src.lastSelName;
    var request = $.ajax( {
	url:'json/copyTypeToModel',
	data : { 'modelId' : {{modelId}},
		 'srcModelId' : sel_model_id,
		 'typeName' : name },
        success: function(data, textStatus, jqXHR) {
	    reloadGrid(dest);
        },
    });

}

</script>
