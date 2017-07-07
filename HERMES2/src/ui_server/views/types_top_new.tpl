% title_slogan=_("Choose Types")
% rebase outer_wrapper **locals()
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
<script src="{{rootPath}}static/base64v1_0.js"></script>
<script>
%if defined('createpipe') and createpipe:
	var createOn = true;
%else:
	var createOn = false;
%end
</script>
% typesEntries = {
%    'vaccines' : {
%        'label'         : _('Vaccine'),
%        'infoUrl'       : 'json/vaccine-info',
%        'editUrl'       : 'vaccine-edit',
%        'editForm'      : 'json/vaccine-edit-form',
%        'commitForm'    : 'json/vaccine-edit-verify-commit',
%        'slogan'        : _("Modify Vaccine Type"),
% 	     'editHeader'    : _("Edit Your Vaccine Type"),
%        'createHeader'  : _("Creating Your Vaccine Type"),
%        },
%    'trucks' : { 
%        'label'         : _('Transport'),
%        'infoUrl'       : 'json/truck-info',
%        'editUrl'       : 'truck-edit',
%        'editForm'      : 'json/truck-edit-form',
%        'commitForm'    : 'json/truck-edit-verify-commit',
%        'slogan'        : _("Modify Transport Type"),
% 	     'editHeader'    : _("Edit Your Transport Type"),
%        'createHeader'  : _("Creating Your Transport Type"),
%        },
%    'fridges' : { 
%        'label'         : _('Storage'),
%        'infoUrl'       : 'json/fridge-info',
%        'editUrl'       : 'fridge-edit',
%        'editForm'      : 'json/fridge-edit-form',
%        'commitForm'    : 'json/fridge-edit-verify-commit',
%        'slogan'        : _("Modify Cold Storage Type"),
% 	     'editHeader'    : _("Edit Your Cold Storage Type"),
%        'createHeader'  : _("Creating Your Cold Storage Type"),
%        },
%    'people' : { 
%        'label'         : _('Population'),
%        'infoUrl'       : 'json/people-info',
%        'editUrl'       : 'people-edit',
%        'editForm'      : 'json/people-edit-form',
%        'commitForm'    : 'json/people-edit-verify-commit',
%        'slogan'        : _("Modify Population Type"),
% 	     'editHeader'    : _("Edit Your Population Type"),
%        'createHeader'  : _("Creating Your Population Type"),
%        },
%    'staff': {
%        'label'         : _('Staff'),
%        'infoUrl'       : 'json/staff-info',
%        'editUrl'       : 'staff-edit',
%        'editForm'      : 'json/staff-edit-form',
%        'commitForm'    : 'json/staff-edit-verify-commit',
%        'slogan'        : _("Modify Staff Type"),
%        'editHeader'    : _("Edit Your Staff Type"),
%        'createHeader'  : _("Creating Your Staff Type")
%        },
%    'perdiems': {
%        'label'         : _('Per Diems'),
%        'infoUrl'       : 'json/perdiem-info',
%        'editUrl'       : 'perdiem-edit',
%        'editForm'      : 'json/perdiem-edit-form',
%        'commitForm'    : 'json/perdiem-edit-verify-commit',
%        'slogan'        : _("Modify Per Diem Type"),
%        'editHeader'    : _("Edit Your Per Diem Type"),
%        'createHeader'  : _("Creating Your Per Diem Type")
%        }
% }
% orderedTypesList = ['vaccines','fridges','trucks','people','staff','perdiems']
<script>
var modelId = {{modelId}};
var modelName = "{{modelName}}";
var myURL = "{{rootPath}}{{baseURL}}?id={{modelId}}"

var typesMap = {
% for te,t in typesEntries.items():
    '{{te}}' : { 'dispName' : '{{t["label"]}}', 
                   'infoUrl'  : '{{rootPath}}{{t["infoUrl"]}}',  
                   'editUrl'  : '{{rootPath}}{{t["editUrl"]}}',
                   'commitUrl': '{{rootPath}}{{t["commitForm"]}}',
                   'editFormUrl': '{{rootPath}}{{t["editForm"]}}',
                   'editHeader':'{{t["editHeader"]}}',
                   'createHeader':'{{t["createHeader"]}}'
                 },
% end
};
</script>

<style>

div.types-top-side-buttons-main{
	display: -webkit-flex;
	display: flex;
	margin: 0;
	padding: 0;
	flex-flow: column;
	-webkit-align-items: center;
	align-items: center;
	-webkit-justify-content: center;
	justify-content: center;
	*width:100px;
	*min-width:1000px;
	*min-height:600px;
}

div.types-top-side-buttons-top-place{
	margin: 0 auto;
	padding:0px;
	height: 25px;
	*-webkit-flex: 1 1 10%;
	*flex: 1 1 10%;
	order:1
	*background: red;
}

div.types-top-side-button-holder{
	margin: 0 auto;
	padding:5px;
	*-webkit-flex: 1 1 10%;
	*flex: 1 1 20%;
}

div.types-top-orig-main{
	display: -webkit-flex;
	display: flex;
	margin: 0;
	padding: 0;
	flex-flow: column;
	-webkit-align-items: left;
	align-items: left;
	*-webkit-justify-content: f;
	*justify-content: flex-start;
	*width:100px;
	*min-width:1000px;
	*min-height:600px;
}
	
div.types-top-orig-top {
	margin: 0 5px;
	padding:0px;
	height: 30px;
	*-webkit-flex: 1 1 10%;
	*flex: 1 1 10%;
	order:1;
	align-self:flex-start;
	*background: red;
}

div.types-top-orig-grid {
	margin: 0 auto;
	padding:0px;
	*-webkit-flex: 1 1 80%;
	*flex: 1 1 80%;
	order:2;
	*background: red;
}

div.types-top-orig-footer {
	margin: 0;
	padding:5px 0px;
	height: 25px;
	*-webkit-flex: 1 1 10%;
	*flex: 1 1 10%;
	order:3;
	*background: red;
}

div.types-top-dest-main{
	display: -webkit-flex;
	display: flex;
	margin: 0;
	padding: 0;
	flex-flow: column;
	-webkit-align-items: left;
	align-items: left;
	*-webkit-justify-content: f;
	*justify-content: flex-start;
	*width:100px;
	*min-width:1000px;
	*min-height:600px;
}
	
div.types-top-dest-top {
	margin: 0 5px;
	padding:0px;
	height: 30px;
	*-webkit-flex: 1 1 10%;
	*flex: 1 1 10%;
	order:1;
	align-self:flex-start;
	*background: red;
}

div.types-top-dest-grid {
	margin: 0 auto;
	padding:0px;
	*-webkit-flex: 1 1 80%;
	*flex: 1 1 80%;
	order:2;
	*background: red;
}

div.types-top-dest-footer {
	margin: 0;
	padding:5px 0px;
	height: 25px;
	*-webkit-flex: 1 1 10%;
	*flex: 1 1 10%;
	order:3;
	*background: red;
}

div.types-top-main{
	display: -webkit-flex;
	display: flex;
	margin: 0;
	padding: 0;
	flex-flow: row;
	-webkit-align-items: left;
	align-items: left;
	*-webkit-justify-content: f;
	*justify-content: flex-start;
	width:800px;
	*min-width:1000px;
	*min-height:600px;
}

div.types-top-main-top {
	display: block;
	margin: 4px;
	padding: 5px;
	min-height: 100px;
}

div.types-top-main-1{
	margin: 0 0;
	padding:20px;
	-webkit-flex: 1 1 15%;
	flex: 1 1 15%;
	order: 1;
}

div.types-top-main-2{
	margin: 0 0;
	padding:20px;
	-webkit-flex: 1 1 35%;
	flex: 1 1 35%;
	order: 2;
}

div.types-top-main-3{
	margin: 0 0;
	padding:20px;
	-webkit-flex: 1 1 15%;
	flex: 1 1 15%;
	order: 3;
}

div.types-top-main-4{
	margin: 0 0;
	padding:20px;
	-webkit-flex: 1 1 35%;
	flex: 1 1 35%;
	order: 4;
}

</style>
<div class='types-top-main-top'>
<p>
	<span class='hermes-top-main'>
		{{_('Edit Components')}}
	</span>
</p>

<p>
	<span class='hermes-top-sub'>
		{{_('Use the Source dropdown box to change what database or model to use to look for components.  Select the component you wish to add to the {0} model, and click the arrow button located between the two tables to make it available to the model. To remove an existing component from the model, click the Del(ete) button in the component\'s row in the Used Types table on the left.').format(modelName)}}
	</span>
</p>
</div> <!-- types-top-main-top -->
<div class='types-top-main'>
	<div class='types-top-main-1'>
    	<div class='types-top-side-buttons-main'>
    		<div class='types-top-side-buttons-top-place'></div>
	        %   for te in orderedTypesList:
	        %   	t = typesEntries[te]
	        <div class='types-top-side-button-holder'>
	        	<button id="{{te}}_button" style="width:150px">{{t['label']}}</button>
	        </div>
    		%   end
    		<div class='types-top-side-buttons-bottom-place'></div>
		</div> <!-- types-top-side-buttons-top-place -->
	</div> <!-- types-top-main-1 -->
	
	<div class='types-top-main-2'>
		<div class='types-top-orig-main'>
			<div class='types-top-orig-top' id='dest_header'>
					{{_('Current type') }}
			</div>
			<div class='types-top-orig-grid'>
					<table id='dest_grid'></table>
					<div id='dest_pager'></div>
			</div>
			<div class='types-top-orig-footer'>
					<div id='create_new_type_button'>{{_('Create a New Component')}}</div>
			</div>
		</div> <!-- types-top-orig-main -->
	</div> <!-- types-top-main-2 -->
	
	<div class='types-top-main-3' style='align-self:center;'>
		<button id="copy_to_model_button">{{_('Add Component To Model')}}</button>
	</div> <!-- types-top-main-3 -->
	
	<div class='types-top-main-4'>
    	<div class='types-top-dest-main'>
    		<div class='types-top-dest-top' id='src_header'>
		    	<label for="src_model_select">{{_('source')}}</label>
		    	<select name="src_model_select" id="src_model_select"></select>
		    </div>
		    <div class='types-top-dest-grid'>
		    	<table id='src_grid'></table>
		    	<div id='src_pager'></div>
		    </div>
		    <div class='types-top-dest-footer'></div>
	    </div> <!-- types-top-dest-main -->
	</div> <!-- types-top-main-4 -->
</div> <!-- types-top-main -->

<!--
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
-->

<div id="info_modal">
	<div class="modal-dialog">
		<div id="info_dialog" title='replace me'></div>
	</div>
</div>
<div id="edit_dialog" title='replace me'>
	<div id="edit_form_content"></div>
</div>
<div id="save_name_modal">
	<form>
		<fieldset>
			<table>
				<tr>
					<td>
						{{_("What would you like to name your new type?")}}
					</td>
				</tr>
				<tr>
					<td>
						<input type="hidden" name="new_type_dbname_text"
							id="new_type_dbname_text" />
						<input type="text" name="new_type_name_text" 
							id="new_type_name_text" style="width:100%" 
							class="text ui-widget-content ui-corner-all" />
					</td>
				</tr>
			</table>
		</fieldset>
	</form>
</div>

<div id="save_name_exists_modal" title='{{_("Notification")}}'></div>
<div id="req_modal">{{_('There are required entries that have invalid values, please correct the fields that are highlighted in red.')}}</div>
<script>

// many characters in a jquery id need escaped.
function jId(i) {
    return '#' + i.replace( /(:|\.|\[|\]|\+|\=|\/)/g, "\\$1");
}

$("#req_modal").dialog({autoOpen:false, height:"auto", width:"auto", modal:true,
		buttons:{
			'{{_("OK")}}':function(){
				$(this).dialog("close");
			}
		}
	});

console.log(typesMap);
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
    btn.button({
    	icons: {primary:'ui-icon-arrowthick-1-w'}
    });
    btn.click( copySelected );

    // info dialog
    $("#info_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
    //$("#edit_dialog").dialog({autoOpen:false, height:"auto", width:"auto"});
    $("#edit_dialog").dialog({
    	autoOpen:false, 
    	modal:true,
    	height:"auto", 
    	width:"auto"
    });
    
//    if(createOn){
//		var btn = $("#wrappage_bn_misc_button");
//		btn.button();
//		btn.click( function() {
//			window.location = "{{rootPath}}model-create/next?expert=true";
//		});
//    }
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
console.log('point 2');

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
    {name: 'dispName', width:250, index: 'dispName', search:true, stype:'text',sopt:['cn']},
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
    s += "\");'>{{_('Info')}}</button>";
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
    		alert('{{_("Failed33: ")}}'+data.msg);
	    }
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert("Error: "+jqxhr.responseText);
	});
    
}

function doesTypeExistInModel(typename,displayname){
	return $.ajax({
		url:'{{rootPath}}json/check-if-type-exists-for-model',
		data:{
			'modelId':{{modelId}},
			'typename':typename,
			'displayname':displayname
		}
	}).promise();
}

function findModifiedDBName(typename,displayname){
	count = 0;
	$.ajax({
		url:'{{rootPath}}json/get-all-typenames-in-model',
		data:{
			'modelId':{{modelId}}
		}
	})
	.done(function(result){
		if(result.success){
			while(result.typenames.indexOf(typename)!=0){
				typename = typename.slice(typename.length-1)+count;
				count++;
			}
			return typename;
		}
		else{
			alert(result.msg);
		}
	})
	.fail(function(jqxhr, textStatus, error) {
		alert("Error: "+jqxhr.responseText);
	});
};

$("#create_new_type_button").button();
$("#create_new_type_button").click(function(){
	editType("new");
});

$("#save_name_exists_modal").dialog({
	autoOpen:false,
	modal:true,
	buttons:{
		'{{_("OK")}}':function(){
			$(this).dialog("close");
		}
	},
	open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
	    	if (e.keyCode == $.ui.keyCode.ENTER) {
	    		e.preventDefault();
	    		$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
	    	}
	    };
    },
});

$("#save_name_modal").dialog({
	autoOpen:false,
	height: 300,
	width: 400,
	modal: true,
	open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
	    	if (e.keyCode == $.ui.keyCode.ENTER) {
	    		e.preventDefault();
	    		$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
	    	}
	    };
    },
	buttons:{
		'{{_("Save")}}':function(){
			doesTypeExistInModel($("#new_type_dbname_text").val(),$("#new_type_name_text").val())
			.done(function(result){
				if(result.success){
					if(result.exists){
						// Need to figure out how to translate this, think I know, but will leave it for now
						// STB TODO TRANSLATE
						if (result.which == 'type'){
							var textString = "The " + typesMap[currentType].dispName + " type " + $("#new_type_dbname_text").val() 
											+ " you shouldn't see this.";
						}
						else{
							var textString = "The " + typesMap[currentType].dispName + " type " + $("#new_type_name_text").val() 
								+ " already exists in this Model, please provide a new name.";
						}
						$("#save_name_exists_modal").text(textString);
						$("#save_name_exists_modal").dialog("open");
					}
					else{
						//var value = $("#new_type_name_text").val();
						if(!$("#new_type_name_text").val()){
							var textString = '{{_("The new type name cannot be left blank.")}}';
							$("#save_name_exists_modal").text(textString);
							$("#save_name_exists_modal").dialog("open");
						}
						else{
							$("#save_name_exists_modal").dialog("close");
							var dict = $("#edit_form_content").editFormManager('getEntries');
							dict['Name'] = $("#new_type_dbname_text").val();
							dict['DisplayName'] = $("#new_type_name_text").val();
							$.ajax({
	    						url:typesMap[currentType].commitUrl,
	    						data:dict,
	    					})
	    					.done(function(result){
	    						if(result.success && (result.value == undefined || result.value)) {
	    							$("#save_name_modal").dialog("close");
	    							$("#edit_dialog").dialog("close");
	    							reloadGrid(dest);
	    						}
	    						else{
	    							alert(result.msg);
	    						}
	    					}); 
						}
					}
				}
				else{
					alert(result.msg);
				}
			})
			.fail(function(jqxhr, textStatus, error) {
				alert("Error: "+jqxhr.responseText);
			});
		},
		'{{_("Cancel")}}':function(){
			$(this).dialog("close");
		}
	}
});



function editType(id) {
	//console.log("new HERE!!!!");
	if(id == "new"){
		var new_inc = 0;
		$.ajax({
			url:'{{rootPath}}json/get-new-type-number',
			data:{
				'modelId':{{modelId}},
				'type':currentType
				}
			})
			.done(function(result){
				if(result.success){
					new_inc = result.inc;
					var modelId = {{modelId}};
					var name = "model_"+modelId+"_"+currentType+"_"+new_inc;
					$.ajax({
						url:typesMap[currentType].editFormUrl,
						data:{
							'modelId':modelId,
							'protoname':'new_type',
							'newname':name
						}
					})
					.done(function(data){
						console.log(data);
						$("#edit_form_content").hrmWidget({
			    			widget:'editFormManager',
			    			html:data['htmlstring'],
			    			modelId:modelId,
			    		});
						$("#edit_dialog").dialog({
			    			title:typesMap[currentType].editHeader,
			    			autoOpen: true,
			    			buttons:{
			    				'{{_("Cancel")}}':function(){
			    					$(this).dialog("close");
			    				},
			    				'{{_("Save")}}':function(){
			    					var flag = false;
			    					var debug = true;
			    					$(".required_string_input").each(function(){
			    						var value = $(this).val();
			    						if(!value || value.length === 0 || !value.trim()){
			    							$(this).css("border-color","red");
			    							if(debug) alert("String Bad " + $(this).attr('id'))
			    							flag=true;
			    						}
			    					});
			    					$(".required_int_input").each(function(){
			    						var value = $(this).val();
			    						if(!value || value.length === 0 || !value.trim()){
			    							$(this).css("border-color","red");
			    							if(debug) alert("int Bad " + $(this).attr('id'))
			    							flag=true;
			    						}
			    						if($(this).hasClass("canzero")){
			    							if(value < 0.0){
			    								$(this).css("border-color","red");
			    								flag=true;
			    								if(debug) alert("int zero Bad " + $(this).attr('id'))
			    							}
			    						}
			    						else{
			    							if(value <= 0.0){
			    								$(this).css("border-color","red");
			    								flag=true;
			    								if(debug) alert("int eq zero Bad " + $(this).attr('id'))
			    							}
			    						}
			    					});
			    					$(".required_float_input").each(function(){
			    						var value = $(this).val();
			    						//alert("could be zero");}
			    						if(!value || value.length === 0 || !value.trim()){
			    							$(this).css("border-color","red");
			    							if(debug) alert("float Bad " + $(this).attr('id') + "Value = " + value)
			    							flag=true;
			    						}
			    						if($(this).hasClass("canzero")){
			    							if(value < 0.0){
			    								$(this).css("border-color","red");
			    								if(debug) alert("float zero Bad " + $(this).attr('id'))
			    								flag=true;
			    							}
			    						}
			    						else{
			    							if(value <= 0.0){
			    								$(this).css("border-color","red");
			    								if(debug) alert("float eq zero Bad " + $(this).attr('id'))
			    								flag=true;
			    							}
			    						}
			    					});
			    					if(!flag){
				    					var dict = $('#edit_form_content').editFormManager('getEntries');
				    					dict['overwrite'] = 1;
				    					$.ajax({
				    						url:typesMap[currentType].commitUrl,
				    						data:dict,
				    					})
				    					.done(function(result){
				    						if(result.success && (result.value == undefined || result.value)) {
				    							$("#edit_dialog").dialog("close");
				    							reloadGrid(dest);
				    						}
				    						else{
				    							alert(result.msg);
				    						}
				    					}); 
				    				}
			    					else{
			    						$("#req_modal").dialog("open");
			    					}
			    				}
			    			},
			    			close:function(){
			    				$("#edit_form_content").html("");
			    			}
			    		});
					})
					.fail(function(jqxhr, textStatus, error) {
						alert("Error: "+jqxhr.responseText);
					});
					//$("#edit_dialog").dialog("open");
				}
				else{
					alert('{{_("There was a problem getting the new increment for the new type name")}}');
				}
			})
			.fail(function(jqxhr, textStatus, error) {
				alert("Error: "+jqxhr.responseText);
			});
		
	}
	else{
		upId = unpackId(id); 
		var modelId = upId.modelId;
		var name = upId.name; 
		var grid = upId.grid;
	    $.ajax({
	    	url:typesMap[currentType].editFormUrl,
	    	data:{
	    		'modelId':modelId,
	    		'protoname':name,
	    		'newname':'None',
	    		'overwrite':1,
	    		'backUrl':B64.encode(myURL + "&startClass=" + currentType)
	    	}
	    })
	    .done(function(data){
	    	if(data.success){
	    		$("#edit_form_content").hrmWidget({
	    			widget:'editFormManager',
	    			html:data['htmlstring'],
	    			modelId:modelId
	    		});
	    		$("#edit_dialog").dialog({
	    			title:typesMap[currentType].editHeader,
	    			buttons:{
	    				'{{_("Cancel")}}':function(){
	    					$(this).dialog("close");
	    				},
	    				'{{_("Save")}}':function(){
	    					var dict = $('#edit_form_content').editFormManager('getEntries');
	    					dict['overwrite'] = 1;
	    					$.ajax({
	    						url:typesMap[currentType].commitUrl,
	    						data:dict,
	    					})
	    					.done(function(result){
	    						if(result.success && (result.value == undefined || result.value)) {
	    							$("#edit_dialog").dialog("close");
	    							reloadGrid(dest);
	    						}
	    						else{
	    							alert(result.msg);
	    						}
	    					}); 
	    				},
	    				'{{_("Save As New Component")}}':function(){
	    					var dict = $('#edit_form_content').editFormManager('getEntries');
	    					$.ajax({
	    						url:'{{rootPath}}json/get-all-typenames-in-model',
	    						data:{
	    							'modelId':{{modelId}}
	    						}
	    					})
	    					.done(function(result){
	    						if(result.success){
	    							count=0;
	    							typename = dict['Name'];
	    							while(result.typenames.indexOf(typename)!=-1){
	    								typename = typename.slice(0,typename.length-1)+count;
	    								count++;
	    							}
	    							$("#new_type_dbname_text").val(typename);
	    	    					$("#new_type_name_text").val(dict['DisplayName'] + " (modified)");
	    	    					
	    	    					$("#save_name_modal").dialog("open");
	    						}
	    						else{
	    							alert(result.msg);
	    						}
	    					})
	    					.fail(function(jqxhr, textStatus, error) {
	    						alert("Error: "+jqxhr.responseText);
	    					});
	    					
	    				}
	    			}
	    		});
	    		$("#edit_dialog").dialog("open");
	 
	    	}
	    	else{
	    		alert('{{_("Failed11: ")}}'+data.msg);
		    }  
		})
		.fail(function(jqxhr, textStatus, error) {
		    alert("Error: "+jqxhr.responseText);
		});
	}
};

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
    caption: "{{_('Used Types')}}",
}).jqGrid('hermify',{debug:true});
	
$("#dest_grid").jqGrid('navGrid', '#dest_pager', {edit:false, add:false, del:false, search: false,refresh:false});

function catchNewType(event, ui, data, $source, $target) {
    ui.helper.dropped = false;
    //alert(data.name);
    copyType(data.name);
}
console.log('point 5');

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
    caption: "{{_('Available Types')}}",
}).jqGrid('hermify',{debug:true});
$("#src_grid").jqGrid('navGrid', '#src_pager', {edit:false, add:false, del:false,search:false,refresh:false});
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
				alert('{{_("Failed22: ")}}'+data.msg);        		
        	}
        },
        error: function(jqxhr, textStatus, errorThrown) {
			alert('{{_("Error: ")}}'+jqxhr.responseText);
        }
    });

}

$(function() {
	% if defined('createpipe') and createpipe:
		$(document).hrmWidget({widget:'stdBackNextButtons',
			getParms:function(){
				return {};
			},
			nextFunction:function() {
				//return {success:true};
				return $.ajax({
					url:"{{rootPath}}json/validate-required-types-of-model",
					data:{modelId:{{modelId}}}
				})
				.done(function(results){
					if(results.success){
						if(results.pass){
							var parmDict = {}; // should be the same as above
							window.location= '{{! breadcrumbPairs.getNextURL() }}' + '?' + parmDict;
						}
						else{
							$("#wrappage_dialog_modal").html(results.message);
							$("#wrappage_dialog_modal").dialog({
								autoOpen:true,
								modal:true,
								width:'auto',
								title: "{{_('Required Component Validation Failed')}}",
								buttons:{
									"{{_('Return To HERMES')}}":function(){
										$(this).dialog("close");
										$(this).html('');
										$(this).dialog("destroy");
									}
								}
							});
							//$("#wrappage_dialog_modal").dialog('option','title',"{{_('Required Component Validation Failed')}}");
							//$("#wrappage_dialog_modal").dialog("open");
						}
					}
					else{
						$("#wrappage_dialog_modal").html("{{_('There was an error with HERMES: ')}}" + results.msg);
						$("#wrappage_dialog_modal").dialog({
							autoOpen:true,
							modal:true,
							width:'auto',
							title: "{{_('Failur Running Component Validation')}}",
							buttons:{
								"{{_('Return To HERMES')}}":function(){
									$(this).dialog("close");
									$(this).html('');
									$(this).dialog("destroy");
								}
							}
						});
						//$("#wrappage_dialog_modal").dialog('option','title',"{{_('Failure Running Component Validation')}}");
						//$("#wrappage_dialog_modal").dialog("open");
					}
				})
				.fail(function(jqxhr, textStatus, errorThrown) {
					alert('{{_("There was a failure in calling component validation algorithm: ")}}'+jqxhr.responseText);
				});

			},
			nextURL:'{{! breadcrumbPairs.getNextURL() }}',
			backURL:'{{! breadcrumbPairs.getBackURL() }}',
		})
	% else:
		$(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'});
	% end
});

function validate_types(){
	
	return $.ajax({
		url:"{{rootPath}}json/validate-required-types-of-model",
		data:{modelId:{{modelId}}}
	}).promise();
}
</script>
