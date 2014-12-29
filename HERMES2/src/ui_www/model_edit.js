$( document ).ready(function() {
    for (attr in Attrs) {
	attr['visible'] = false;
    }
});

function setEditsBorder() {
    visibles = {};

    for (attr in Attrs) {
	var a = Attrs[attr];
	if (!(a.type in visibles)) {
	    visibles[a.type] = false;
	}
	if (a.visible != false) {
	    visibles[a.type] = true;
	}
    }

    for (type in visibles) {
	if (visibles[type] == true) {
	    $('.' + type + '-edits-border').each(function() {
		$(this).css('display', 'block');
	    });
	} else {
	    $('.' + type + '-edits-border').each(function() {
		$(this).css('display', 'none');
	    });
	}
    }
}	    

function toggle_attr(attr) {
    if (Attrs[attr].visible == 'rw') {
	ro_attr(attr);
    } else if (Attrs[attr].visible == 'ro') {
	hide_attr(attr);
    } else {
	show_attr(attr);
    }
}

function fix_visible() {
    for (attr in Attrs) {
	if (Attrs[attr].visible == 'rw') {
	    show_attr(attr);
	} else if (Attrs[attr].visible == 'ro') {
	    ro_attr(attr);
	} else {
	    hide_attr(attr);
	}
    }
}

function show_attr(attrib) {
    $('.' + attrib).each(function() {
	$(this).css('display', 'inline');
    });
    $('.edit_' + attrib).each(function() {
	$(this).css('display', 'inline');
    });
    $('.fixed_' + attrib).each(function() {
	$(this).css('display', 'none');
    });
    $('li.' + attrib + '_Button').html('<a href="#">view ' + Attrs[attrib].title + "</a>");
    Attrs[attrib].visible = 'rw';
    setEditsBorder();
}

function ro_attr(attrib) {
    $('.' + attrib).each(function() {
	$(this).css('display', 'inline');
    });
    $('.edit_' + attrib).each(function() {
	$(this).css('display', 'none');
    });
    $('.fixed_' + attrib).each(function() {
	$(this).css('display', 'inline');
    });
    $('li.' + attrib + '_Button').html('<a href="#">hide ' + Attrs[attrib].title + "</a>");
    Attrs[attrib].visible = 'ro';
    setEditsBorder();
}

function hide_attr(attrib) {
    $('.' + attrib).each(function() {
	$(this).css('display', 'none');
    });
    $('li.' + attrib + '_Button').html('<a href="#">edit ' + Attrs[attrib].title + "</a>");
    Attrs[attrib].visible = false;
    setEditsBorder();
}

// many characters in a jquery id need escaped.
function jId(i) {
    return '#' + i.replace( /(:|\.|\[|\]|\+|\=|\/)/g, "\\$1");
}

function splitUnits(val) {
    var patt1 = /^[\d\.]+/;
    var numeric = val.match(patt1);
    var patt2 = /[^\d\.]*$/;
    var units = val.match(patt2);
    return [numeric, units];
}

function emDragEnter(ev) {
    targetId = ev.currentTarget.id;
    size = $(jId(targetId)).css('font-size');
    t = splitUnits(size);
    size = '' + (t[0] * 1.5) + t[1]
    $(jId(targetId)).css('font-size', size);
}

function emDragLeave(ev) {
    targetId = ev.currentTarget.id;
    size = $(jId(targetId)).css('font-size');
    t = splitUnits(size);
    size = '' + (t[0] / 1.5) + t[1]
    $(jId(targetId)).css('font-size', size);
}

function emAllowDrop(ev) {
    ev.preventDefault();
}

function emDrag(ev) {
    ev.dataTransfer.setData("Text", ev.target.id);
}


function emDrop(ev) {
    ev.preventDefault();
    var data=ev.dataTransfer.getData("Text");
    var targetId = ev.currentTarget.id;
    size = $(jId(targetId)).css('font-size');
    t = splitUnits(size);
    size = '' + (t[0] / 1.5) + t[1]
    $(jId(targetId)).css('font-size', size);

    // need to figure out if the tree element currently has children
    // and if it has been opened before.
    var targetStatus = 'other';

    try {
	targetLi = $(jId(targetId)).parents('li')[0].id;
	if ($(jId(targetLi)+'.jstree-leaf').length) {
	    targetStatus = 'leaf';
	} else if ($(jId(targetLi)+'.jstree-closed').length) {
	    if ($(jId(targetLi)).children('ul').length) {
		targetStatus = 'populated';
	    } else {
		targetStatus = 'unpopulated';
	    }
	} else if ($(jId(targetLi)+'.jstree-open').length) {
	    targetStatus = 'populated';
	}
    } catch (err) {
    }
    
    
    var request = $.ajax({
        url:'json/modelUpdateDND',
        type:'POST',
        data:{ 'srcId' : data,
               'dstId' : targetId,
	       'dstStatus' : targetStatus,
               'context' : JSON.stringify(extraContext),
             },
        success: function(data, textStatus, jqXHR) {
            changeStringSuccess(data, textStatus, jqXHR)
        }
    });
}

function clearRouteTemplate() {
    extraContext['routeTemplate'] = null;
    document.getElementById('routeTemplateText').innerHTML = 'None';
}

function setRouteTemplate(routeName) {
    extraContext['routeTemplate'] = routeName;
    document.getElementById('routeTemplateText').innerHTML = routeName;
}

function validateModel() {
    var request = $.ajax({
	url : 'json/meValidateModel',
	data : {
	    'modelId' : modelId,
	},
	success : function(data, textStatus, jqXHR) {
	    validateModelSuccess(data, textStatus, jqXHR);
	}
    });
}

function validateModelSuccess(data, textStatus, jqXHR) {
    if (!('success' in data)) {
	alert('got invalid server response from validate model');
	return;
    }
    
    if ('updateList' in data) {
	doUpdates(data.updateList);
    }
    
    if (data.success == false) {
	if ('errorString' in data) {
	    alert(data.errorString);
	} else {
	    alert('unknown server error');
	}
    }
}

var fieldChanges = {};

function doUpdate(u) {
	if (u.updateType == 'value') {
	/* value is a special case.  We need to support
	   updates for both 'input' and 'select' tags and
	   update the fixed copy as well.
	   
	   while we're at it save a copy of the updated 
	   field in the cache so changeString() knows that
	   it got updated.
	*/
	var fixedElement = document.getElementById('fixed_'+u.inputId);
	if (fixedElement) {
            if ('displayValue' in u) {
		fixedElement.innerHTML = u.displayValue;
            } else {
		fixedElement.innerHTML = u.value;
            }
	}
	var element = document.getElementById(u.inputId);
	if (element) {
	    if (element.nodeName == "INPUT") {
		element.value = u.value;
	    } else if (element.nodeName == "TEXTAREA") {
	    	element.value = u.value;
	    } else if (element.nodeName == "SELECT") {
	    	// hmm, apparently this could be done with 
	    	// a single line of jquery.  Oh well.
	    	for (var i = 0; element.options[i]; ++i) {
	    		if (element.options[i].value == u.value) {
	    			element.selectedIndex = i;
	    		}
	    	} 
        } else if ($(element).hasClass('hrm_widget')){
			var $elt = $(element);
			if ($elt.hasClass('hrm_widget_typeSelector')) {
				$elt.typeSelector('set',u.value);
			}
			else if ($elt.hasClass('hrm_widget_energySelector')) {
				$elt.energySelector('selId',u.value);
			}
			else if ($elt.hasClass('hrm_widget_currencySelector')) {
				$elt.currencySelector('selId',u.value);
			}
			else alert('unsupported widget type for "value" update type '+elt.nodeName);
	    } else {
	    	alert('invalid nodeName for "value" update type '+element.nodeName);
	    }
	}
	fieldChanges[u.inputId] = u.value;
    } else if (u.updateType == 'html') {
	// generic update of innerHTML
    	var element = document.getElementById(u.inputId);
	if (element)
	    element.innerHTML = u.value;
		var transformations = [['hrm_widget_become_currencySelector', 
		                        {widget:'currencySelector', label:''}],
		                       ['hrm_widget_become_perDiemSelector',
		                        {widget:'typeSelector', label:'', invtype:'perdiems', canBeBlank:false, modelId:modelId}]
							  ];
		for (var i = 0; i<transformations.length; ++i) {
			var cl = transformations[i][0];
			var args = transformations[i][1];
			$(element).find('.'+cl).each( function() {
				var $div = $(this);
				$div.removeClass(cl);
				$div.hrmWidget(args);
			});
		}

    } else if (u.updateType == 'widget') {
    	var widgetOpts = u.value;
    	var widgetType = widgetOpts.widget;
    	var id = u.inputId;
        var elt = document.getElementById(u.inputId);
    	widgetOpts.onChange = function( evt, parm2 ) { widgetChangeCB(id, widgetType, evt, parm2); };
        $(elt).hrmWidget(widgetOpts);
        $(elt).addClass('hrm_widget');
        $(elt).addClass('hrm_widget_'+widgetType);
        fieldChanges[u.inputId] = u.value.selected;
    } else if (u.updateType == 'savedValue') {
        fieldChanges[u.inputId] = u.value;
    } else if (u.updateType == 'focus') {
        document.getElementById(u.inputId).focus()
    } else if (u.updateType == 'node') {
        $(jId(u.inputId)).each(function() {
            $(this).children('div').remove();
            $(this).children('button').remove();
            $(this).children('p').replaceWith(u.value);
            fix_visible();
        });
    } else if (u.updateType == 'changeId') {
	$(jId(u.inputId)).each(function() {
	    $(this).attr("id", u.value);
	    // since the id changed, the entire node is invalid.
	    // to make things easier on the server, let's request
	    // that the node be resent from here
	    var request = $.ajax({
		url : 'json/ModelResendNode',
		data : {
		    'modelId':modelId,
		    'id':u.value
		},
		success : function(data, textStatus, jqXHR) {
		    changeStringSuccess(data, textStatus, jqXHR);
		}
	    });
	});
    } else if (u.updateType == 'create') {
        // create a node on a jstree
	v = u.value;
	treeId = TreeLabels[v.parent[0]];
	$(treeId).jstree("create", 
			 jId(v.parent),
			 v.location,
			 v.node,
			 false,
			 true);
	fixNewNodes();
    } else if (u.updateType == 'remove') {
        // remove a node from a jstree
	treeId = TreeLabels[u.inputId[0]];
	remId = jId(u.inputId);
	$(treeId).jstree("remove", remId);
    } else if (u.updateType == 'open') {
	treeId = TreeLabels[u.inputId[0]];
	$(treeId).jstree("open_node", jId(u.inputId));
    } else if (u.updateType == 'clearUpdates') {
	//console.log('clearing ' + u.inputId + ' updates');
        for (i in fieldChanges) {
            if (!fieldChanges.hasOwnProperty(i))
                continue;

            var parts = i.split(':');
            if (parts[3] == u.inputId) {
		//console.log(i + ' matches, deleting');
                delete fieldChanges[i];
	    } else {
		//console.log(i + " doesn't match");
	    }
        }
    } else if (u.updateType == 'addMessage') {
	handleNewMessage(u.inputId, u.value);
    } else if (u.updateType == 'clearMessages') {
	clearMessages();
    } else if (u.updateType == 'alert') {
	alert(u.value);
    } else {
	alert('invalid update type: '+u.updateType);
    }
}

function changeWidgetSuccess(widgetType, id, data, textStatus, jqXHR) {
    // this has become the catchall handler for anything
    // that just returns an update list
    if (!('success' in data)) {
    	alert('got invalid server response from a widget update');
    	return;
    }
    
    if ('updateList' in data) {
    	doUpdates(data.updateList);
    }
    
    if (data.success == false) {
    	if ('errorString' in data) {
    		alert(data.errorString);
    	} else {
    		alert('unknown server error');
    	}
    }
    $(document).tooltips('applyTips');	
}

function widgetChangeCB(id, widgetType, evt, parm2) {
    var origStr = "";
    
    if (id in fieldChanges) {
    	origStr = fieldChanges[id];
    }

    var curStr = null;
    if ($.inArray(widgetType, ['typeSelector', 'energySelector', 'currencySelector']) > -1) {
    	curStr = parm2;
    }
    else {
    	alert('change to unsuppoted widget type '+widgetType);
    }

    if (origStr != curStr) {
    	var request = $.ajax({
    		url:'json/modelUpdate',
    		type:'POST',
    		data:{
    			'inputId' : id,
    			'origStr' : origStr,
    			'newStr' : curStr
    		},
    		success: function(data, textStatus, jqXHR) {
    			changeWidgetSuccess(widgetType, id, data, textStatus, jqXHR);
    		}
    	});
    }
}

function fixNewNodes() {
    $(".em_replace_me").each(function() {
        $(this).children('ins').remove();
        $(this).replaceWith( $(this).contents() );
    });
    fix_visible();
    $(document).tooltips('applyTips');
}

function doUpdates(updateList) {
    for (var i = 0; i < updateList.length; i++) {
	doUpdate(updateList[i]);
    }
}

function changeStringSuccess(data, textStatus, jqXHR) {
    // this has become the catchall handler for anything
    // that just returns an update list
    if (!('success' in data)) {
	alert('got invalid server response from a field update');
	return;
    }
    
    if ('updateList' in data) {
	doUpdates(data.updateList);
    }
    
    if (data.success == false) {
	if ('errorString' in data) {
	    alert(data.errorString);
	} else {
	    alert('unknown server error');
	}
    }
    $(document).tooltips('applyTips');
}

function changeString(inputId) {
    origStr = "";
    if (inputId in fieldChanges) {
	origStr = fieldChanges[inputId];
    }
    
    var curStr = document.getElementById(inputId).value;
    if (origStr != curStr) {
	var request = $.ajax({
	    url:'json/modelUpdate',
            type:'POST',
	    data:{
		'inputId' : inputId,
		'origStr' : origStr,
		'newStr' : curStr
	    },
	    success: function(data, textStatus, jqXHR) {
		changeStringSuccess(data, textStatus, jqXHR);
	    }
	});
    }
}

function changeTextArea(inputId) {
    origStr = "";
    if (inputId in fieldChanges) {
        origStr = fieldChanges[inputId];
    }

    var curStr = document.getElementById(inputId).value;
    if (origStr != curStr) {
        var request = $.ajax({
	    url:'json/modelUpdate',
            type:'POST',
	    data:{
		'inputId' : inputId,
		'origStr' : origStr,
		'newStr' : curStr
	    },
	    success: function(data, textStatus, jqXHR) {
		changeStringSuccess(data, textStatus, jqXHR);
	    }
	});
    }
}

function changePullDown(inputId) {
    origStr = "";
    if (inputId in fieldChanges) {
	origStr = fieldChanges[inputId];
    }
   
    var value = getSelectValue(inputId);
    
    if (origStr != value) {
	var request = $.ajax({
	    url:'json/modelUpdate',
	    data:{
		'inputId' : inputId,
		'origStr' : origStr,
		'newStr' : value
	    },
	    success: function(data, textStatus, jqXHR) {
		// currently there's no difference in working with pullDowns
		changeStringSuccess(data, textStatus, jqXHR);
	    }
	});
    }
    
}

function unhideCount(selId, hideId, inputId) {
    var index = document.getElementById(selId).selectedIndex;
    if (index != 0) {
        document.getElementById(hideId).style.display='inline';
        document.getElementById(inputId).focus();
    }
}

function addNewTuple(inputId) {
    var selId = 'addSel_' + inputId;
    var countId = 'addCount_' + inputId;
    selectElement = document.getElementById(selId);
    var index = selectElement.selectedIndex;
    var newValue = selectElement.options[index].value;
    var newCount = document.getElementById(countId).value;

    var request = $.ajax ({
        url:'json/modelUpdateAddTuple',
        data:{
            'inputId' : inputId,
            'value' : newValue,
            'count' : newCount
        },
        success: function(data, textStatus, jqXHR) {
            changeStringSuccess(data, textStatus, jqXHR);
        }
    });
    // so that if this is called from a "form submit", don't actually try to submit a form
    return false;
}

function changeTupleCount(inputId) {
    origStr = "";
    if (inputId in fieldChanges) {
        origStr = fieldChanges[inputId];
    }
    var curStr = document.getElementById(inputId).value;
    if (origStr != curStr) {
	var request = $.ajax({
	    url:'json/modelUpdate',
	    data:{
		'inputId' : inputId,
		'origStr' : origStr,
		'newStr' : curStr
	    },
	    success: function(data, textStatus, jqXHR) {
		changeStringSuccess(data, textStatus, jqXHR);
	    }
	});
    }
}



function decodeBase64(s) {
    // supposedly this handles utf-8
    return B64.decode(s);

    // this doesn't handle utf-8
    var e={},i,b=0,c,x,l=0,a,r='',w=String.fromCharCode,L=s.length;
    var A="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    for(i=0;i<64;i++){e[A.charAt(i)]=i;}
    for(x=0;x<L;x++){
        c=e[s.charAt(x)];b=(b<<6)+c;l+=6;
        while(l>=8){((a=(b>>>(l-=8))&0xff)||(x<(L-2)))&&(r+=w(a));}
    }
    return r;
};

function packInputId(modelId, itemId, field, secondaryId, tree) {
    ret = tree + ':' + modelId + ':' + field + ':' + B64.encode(itemId);
    if (secondaryId !== null)
	ret += ':' + B64.encode(secondaryId);
}

function unpackInputId(id) {
    ret = {};

    var parts = id.split(':');
    ret.tree = parts[0];
    ret.modelId = parts[1];
    ret.field = parts[2];
    var itemId = parts[3];
    itemId = decodeBase64(itemId);
    ret.itemType = itemId.substr(0, 1);
    ret.itemId = itemId.substr(1);

    ret.secondary = null;
    if (parts.length > 4)
	ret.secondary = decodeBase64(parts[4]);
    return ret;
}

function unpackNodeId(id) {
    ret = {}
    ret.tree = id.substr(0, 1);
    ret.nodeType = id.substr(1, 2);
    ret.nodeIdId = id.substr(2);
    
    if (ret.nodeType == 'R') {
	ret.nodeId = decodeBase64(ret.nodeId)
    }
    
    return ret;
}


$(function(){
    $.contextMenu({
        selector: '.store-edit-menu', 
        trigger: 'left',
        callback: function(key, options) {
            var packedId = options.$trigger.attr("id");
	    var id = unpackInputId(packedId);
	    
	    if (key == 'edit') {
	        meStoreEdit(modelId, id.itemId, id.tree, id.itemType);
	    } else if (key == 'recEdit') {
		meRecursiveStoreEdit(modelId, id.itemId, id.tree, id.itemType);
            } else {
		meRequestBasicEdit(modelId, packedId, key)
	    }
        },
        items: {
            "edit": {name: "Edit Store", icon: "edit"},
	    "recEdit": {name: "Recursive Edit"},
            "cut": {name: "Detach Store", icon: "cut"},
            "copy": {name: "Copy Store to Unattached", icon: "copy"},
            "delete": {name: "Delete Store", icon: "delete"},
        }
    });
    
    $('.context-menu-one').on('click', function(e){
        console.log('clicked', this);
    })
});

$(function(){
    $.contextMenu({
        selector: '.route-edit-menu', 
        trigger: 'left',
        callback: function(key, options) {
            var packedId = options.$trigger.attr("id");
	    var id = unpackInputId(packedId);
	    
	    if (key == 'edit') {
	        meRouteEdit(modelId, id.itemId, id.tree, id.itemType);
	    } else if (key == 'template') {
		setRouteTemplate(id.itemId);
            } else {
		meRequestBasicEdit(modelId, packedId, key)
	    }
        },
        items: {
            "edit": {name: "Edit Route", icon: "edit"},
//            "cut": {name: "Detach Store", icon: "cut"},
//            "copy": {name: "Copy Store", icon: "copy"},
            "delete": {name: "Delete Route", icon: "delete"},
	    "template": {name: "set as default template"},
        }
    });
    
    $('.context-menu-one').on('click', function(e){
        console.log('clicked', this);
    })
});

$(function(){
    $.contextMenu({
        selector: '.stop-edit-menu', 
        trigger: 'left',
        callback: function(key, options) {
            var packedId = options.$trigger.attr("id");
	    var id = unpackInputId(packedId);
	    
	    if (key == 'edit') {
//	        meRouteEdit(modelId, id.itemId);
            } else {
		meRequestBasicEdit(modelId, packedId, key)
	    }
        },
        items: {
//            "edit": {name: "Edit Route", icon: "edit"},
//            "cut": {name: "Detach Store", icon: "cut"},
//            "copy": {name: "Copy Store", icon: "copy"},
            "delete": {name: "Delete Stop", icon: "delete"},
        }
    });
    
    $('.context-menu-one').on('click', function(e){
        console.log('clicked', this);
    })
});

function meRequestBasicEdit(modelId, packedId, request) {
    var request = $.ajax({
	url : 'json/RequestBasicEdit',
	data : {
	    'modelId' : modelId,
	    'packedId' : packedId,
	    'request' : request,
	    'context' : JSON.stringify(extraContext),
	},
	success : function(data, textStatus, jqXHR) {
	    changeStringSuccess(data, textStatus, jqXHR);
	}
    });
}

function meStoreEdit(modelId, storeId, tree, nodeType) {
    var count = $('#storeEditorParent').data('kidcount');
    count += 1;
    $('#storeEditorParent').data('kidcount',count);
    var divId = "storeEditChild_"+count.toString();
    var $newdiv = $( "<div id='"+divId+"' />" );
    var innerDivId = "inner_"+divId;
    $('#storeEditParent').append($newdiv);
    $newdiv.dialog({
	autoOpen:false, 
	height:"auto", 
	width:"auto",
	buttons: {
	    Ok: function() {
		$( this ).find('form').submit();
	    },
	    Cancel: function() {
	      	$( this ).dialog( "close" );
	    }
	}
    });
    $newdiv.html( "<div id='"+innerDivId+"' />" );
    $('#'+innerDivId).hrmWidget({
	widget:'storeEditor',
	modelId:modelId,
	idcode:storeId,
	closeOnSuccess:divId,
	callbackData:{modelId:modelId, resendId:tree + nodeType + storeId},
	afterBuild:function() { 
	    $newdiv.dialog('open'); 
	},
	onServerSuccess: function(data, cbData) {
	    //alert('server success ' + cbData.resendId);
	    var request = $.ajax({
		url : 'json/ModelResendNode',
		data : {
		    'modelId':cbData.modelId,
		    'id':cbData.resendId
		},
		success : function(data, textStatus, jqXHR) {
		    changeStringSuccess(data, textStatus, jqXHR);
		}
	    });
	}
    });
    $newdiv.dialog('option','title',"Editing location "+storeId+" of model "+modelId);
}

function meRecursiveStoreEdit(modelId, storeId, tree, nodeType) {
    var count = $('#storeEditorParent').data('kidcount');
    count += 1;
    $('#storeEditorParent').data('kidcount',count);
    var divId = "storeEditChild_"+count.toString();
    var $newdiv = $( "<div id='"+divId+"' />" );
    var innerDivId = "inner_"+divId;
    $('#storeEditParent').append($newdiv);
    $newdiv.dialog({
	autoOpen:false, 
	height:"auto", 
	width:"auto",
	buttons: {
	    //Ok: function() {
	    //$( this ).find('form').submit();
	    //},
	    Done: function() {
	      	$( this ).dialog( "close" );
	    }
	}
    });
    $newdiv.html( "<div id='"+innerDivId+"' />" );
    $('#'+innerDivId).hrmWidget({
	widget:'recursiveStoreEditor',
	modelId:modelId,
	idcode:storeId,
	tree:tree,
	closeOnSuccess:divId,
	callbackData:{modelId:modelId, resendId:tree + nodeType + storeId},
	afterBuild:function() { 
	    $newdiv.dialog('open'); 
	},
	onServerSuccess: function(data, cbData) {
	    alert('server success ' + cbData.resendId);
	    //var request = $.ajax({
	    //url : 'json/ModelResendNode',
	    // data : {
	    //'modelId':cbData.modelId,
	    //'id':cbData.resendId
	    //},
	    //success : function(data, textStatus, jqXHR) {
	    //changeStringSuccess(data, textStatus, jqXHR);
	    //}
	    //});
	}
    });
    $newdiv.dialog('option','title',"Editing location "+storeId+" of model "+modelId);
}

// a start of a more generic version of getSelectValue
function getInputValue(id) {
    var element = document.getElementById(id);
    if (!element) {
	return false;
    }

    if (element.nodeName == "SELECT") {
	var index = element.selectedIndex
	var value = element.options[index].value;
	return value;
    } else {
	return false;
    }
}
	

function getSelectValue(id) {
    var element = document.getElementById(id);
    var index = element.selectedIndex
    var value = element.options[index].value;

    return value;
}

function updateRSEDialog(unique, storeId, tree) {
    var category = getSelectValue('rse_category_' + unique);
    var field = getSelectValue('rse_field_' + unique);

    var request = $.ajax({
	url:'json/meUpdateRSEDialog',
	data:{
	    'modelId' : modelId,
	    'idcode' : storeId,
	    'tree' : tree,
	    'category' : category,
	    'field' : field,
	    'unique' : unique
	},
	success: function(data, textStatus, jqXHR) {
	    changeStringSuccess(data, textStatus, jqXHR);
	}
    });
}

function updateRSEValue(unique, storeId, tree, action) {
    var category = getSelectValue('rse_category_' + unique);
    var field = getSelectValue('rse_field_' + unique);
    var value = document.getElementById('rseInput_' + action + '_' + unique).value;
    
    var div = document.getElementById('rse_content_' + unique);
    div.innerHTML = '<p>Updating.  This may take a moment...</p>';

    var request = $.ajax({
	url:'json/meUpdateRSEValue',
	data: {
	    'modelId' : modelId,
	    'idcode' : storeId,
	    'tree' : tree,
	    'category' : category,
	    'field' : field,
	    'unique' : unique,
	    'action' : action,
	    'value' : value,
	    'secondary' : 'X',
	    'tertiary' : 'X'
	},
	success: function(data, textStatus, jqXHR) {
	    changeStringSuccess(data, textStatus, jqXHR);
	}
    });
	    
}

function updateRSECostValue(unique, storeId, tree, action) {
    var category = getSelectValue('rse_category_' + unique);
    var field = getSelectValue('rse_field_' + unique);
    var cost = document.getElementById('rseInput_set_cost_' + unique).value;
    var costcur = $('#rseInput_set_costcur_' + unique).currencySelector('selId');
    var costyear = document.getElementById('rseInput_set_costyear_' + unique).value;
    
    var div = document.getElementById('rse_content_' + unique);
    div.innerHTML = '<p>Updating.  This may take a moment...</p>';

    var request = $.ajax({
	url:'json/meUpdateRSEValue',
	data: {
	    'modelId' : modelId,
	    'idcode' : storeId,
	    'tree' : tree,
	    'category' : category,
	    'field' : field,
	    'unique' : unique,
	    'action' : action,
	    'value' : cost,
	    'secondary' : costcur,
	    'tertiary' : costyear
	},
	success: function(data, textStatus, jqXHR) {
	    changeStringSuccess(data, textStatus, jqXHR);
	}
    });
}

function updateRSERoutePerDiemValue(unique, storeId, tree, action) {
    var category = getSelectValue('rse_category_' + unique);
    var field = getSelectValue('rse_field_' + unique);
    var perDiemType = $('#rseInput_set_perdiem_' + unique).typeSelector('selValue');
    
    var div = document.getElementById('rse_content_' + unique);
    div.innerHTML = '<p>Updating.  This may take a moment...</p>';

    var request = $.ajax({
	url:'json/meUpdateRSEValue',
	data: {
	    'modelId' : modelId,
	    'idcode' : storeId,
	    'tree' : tree,
	    'category' : category,
	    'field' : field,
	    'unique' : unique,
	    'action' : action,
	    'value' : perDiemType,
	    'secondary' : null,
	    'tertiary' : null
	},
	success: function(data, textStatus, jqXHR) {
	    changeStringSuccess(data, textStatus, jqXHR);
	}
    });
}

function updateRSETypeValue(unique, storeId, tree) {
    var category = getSelectValue('rse_category_' + unique);
    var field = getSelectValue('rse_field_' + unique);
    var action = getSelectValue('rse_input_action_' + unique);
    var value = document.getElementById('rse_input_value_' + unique).value;
    var type = getSelectValue('rse_input_type_' + unique);
    var repl = getSelectValue('rse_input_repl_' + unique);
    var div = document.getElementById('rse_content_' + unique);
    div.innerHTML = '<p>Updating.  This may take a moment...</p>';

    var request = $.ajax({
	url:'json/meUpdateRSEValue',
	data: {
	    'modelId' : modelId,
	    'idcode' : storeId,
	    'tree' : tree,
	    'category' : category,
	    'field' : field,
	    'unique' : unique,
	    'action' : action,
	    'value' : value,
	    'secondary' : type,
	    'tertiary' : repl
	},
	success: function(data, textStatus, jqXHR) {
	    changeStringSuccess(data, textStatus, jqXHR);
	}
    });
	    
}


function meRouteEdit(modelId, routeId, tree, nodeType) {
    var count = $('#storeEditorParent').data('kidcount');
    count += 1;
    $('#storeEditorParent').data('kidcount',count);
    var divId = "storeEditChild_"+count.toString();
    var $newdiv = $( "<div id='"+divId+"' />" );
    var innerDivId = "inner_"+divId;
    $('#storeEditParent').append($newdiv);
    $newdiv.dialog({
	autoOpen:false, 
	height:"auto", 
	width:"auto",
	buttons: {
	    Ok: function() {
		$( this ).find('form').submit();
	    },
	    Cancel: function() {
	      	$( this ).dialog( "close" );
	    }
	}
    });
    $newdiv.html( "<div id='"+innerDivId+"' />" );
    $('#'+innerDivId).hrmWidget({
	widget:'routeEditor',
	modelId:modelId,
	routename:routeId,
	closeOnSuccess:divId,
	callbackData:{modelId:modelId, resendId:tree + nodeType + B64.encode(routeId)},
	afterBuild:function() { 
	    $newdiv.dialog('open'); 
	},
	onServerSuccess: function(data, cbData) {
 	    var request = $.ajax({
		url : 'json/ModelResendNode',
		data : {
		    'modelId':cbData.modelId,
		    'id':cbData.resendId
		},
		success : function(data, textStatus, jqXHR) {
		    changeStringSuccess(data, textStatus, jqXHR);
		}
	    });
	}
    });
    $newdiv.dialog('option','title',"Editing route "+routeId+" of model "+modelId);
}


function openNode(event, data) {
    var node = data.args[0];
    //var nodeId = data.args[0].attr("id");
    // hide nodes child messages 
    $(node).children('.em-child-message-border').each(function() {
	$(this).css('display', 'none');
    }); 
    //alert("openNode: " + data.args[0].attr("id"));
}

function closeNode(event, data) {
    var node = data.args[0];
    $(node).children('.em-child-message-border').each(function() {
	if ($(this).children().length > 0)
	    $(this).css('display', 'block');
    });

    //alert("closeNode: " + data.args[0].attr("id"));
}

var updatesSavedForLoadNode = [];

function loadNode(event, data) {
    fixNewNodes();
    insertSavedMessages();
    doUpdates(updatesSavedForLoadNode);
    UpdatesSavedForLoadNode = [];
    //alert("loadNode: " + data.args[0].attr("id"));
}

var nodeMessages = {};
var messagesExist = false;
var messageClasses = [ 'em-message-border', 'em-child-message-border' ]; 

function handleNewMessage(inputId, message) {
    if (!messagesExist)
	disableClearMessageButton(false)	
    var element = document.getElementById(inputId);
    if (!element)
	queueMessage(inputId, message);
    else
	addMessage(inputId, message);
}

function queueMessage(inputId, message) {
    if (!(inputId in nodeMessages))
	nodeMessages[inputId] = [message,];
    else
	nodeMessages[inputId].push(message);
}

function addMessage(inputId, message) {

    var element = document.getElementById(inputId);
    var pElement = document.createElement('p');
    pElement.innerHTML = message;
    element.appendChild(pElement);

    var childMsg = $(jId(inputId)).hasClass('em-child-message-border');
    var nodeOpen = $(jId(inputId)).parent().hasClass('jstree-open');
    var showMsg = false;
    if (childMsg) {
	if (!nodeOpen)
	    showMsg = true;
    } else {
	showMsg = true;
    }
    if (showMsg)
	element.style.display = "block";

    //var ih = element.innerHTML;
    //element.innerHTML = ih + message;
}

function insertSavedMessages() {
    $(".pre-emsmb").each(function() {
	inputId = $(this).attr('id');
	if (inputId in nodeMessages) {
	    var len = nodeMessages[inputId].length;
	    for (var i = 0; i < len; ++i) 
		addMessage(inputId, nodeMessages[inputId][i]);
	    delete nodeMessages[inputId];
	}
	$(this).removeClass('pre-emsmb');
    });
}

function clearMessages() {
    disableClearMessageButton(true);
    nodeMessages = {};
    messagesExist = false;

    var len = messageClasses.length;
    for (i = 0; i < len; ++i) {
	var mc = messageClasses[i];

	$('.' + mc).each(function() {
	    $(this).html('');
	    $(this).css('display', 'none');
	});
    }
}

function disableClearMessageButton(disabled) {
    //document.getElementById('clear_messages_button').disabled = disabled;
}

function listify(a) {
    if (Array.isArray(a))
	return a;
    return [a];
}

function cloneListify(a) {
    if (Array.isArray(a))
	return a.slice(0);
    return [a];
}

function disableElement(id, disable) {
    disable = (typeof disable === "undefined") ? true : disable;
    var element = document.getElementById(id);
    if (element) {
	element.disabled = disable;
    }
}

// enable or disable input fields based on the value of another input field
function autoenableOptions(opt) {
    var sId = opt.selectorId;
    var sVal = getInputValue(sId);
    var enabled = [];
    var disabled = [];
    var cond = {};

    if ('defEnabled' in opt)
	enabled = listify(opt.defEnabled);
    if ('defDisabled' in opt)
	disabled = listify(opt.defDisabled);
    if ('conditionals' in opt)
	cond = opt.conditionals;


    var curCond = [];
    if (sVal in cond)
	curCond = listify(cond[sVal]);

    //alert(JSON.stringify(curCond));

    var len = enabled.length;
    for (var i = 0; i < len; ++i) {
	var id = enabled[i]
	var disable = !(-1 == curCond.indexOf(id));
	disableElement(id, disable);
    }
    
    var len = disabled.length;
    for (var i = 0; i < len; ++i) {
	var id = disabled[i]
	var disable = (-1 == curCond.indexOf(id));
	disableElement(id, disable);
    }
    
}


function hideColumn(tableId, col, show) {
    show = (typeof show === "undefined") ? false : show;

    var disp;
    if (show) 
	disp = 'table-cell';
    else 
	disp = 'none';

    var tbl = document.getElementById(tableId);
    var rows = tbl.getElementsByTagName('tr');

    for (var row=0; row < rows.length; ++row) {
	var cells = rows[row].getElementsByTagName('td');
	cells[col].style.display=disp;
    }
}


// show or hide columns based on the value of an input field
function autohideColumns(opt) {
    var sId = opt.selectorId;
    var sVal = getInputValue(sId);

    var tableId = opt.tableId;

    var hide = [];
    var show = [];
    var cond = {};

    if ('defShow' in opt)
	show = listify(opt.defShow);
    if ('defHide' in opt)
	hide = listify(opt.defHide);
    if ('conditionals' in opt)
	cond = opt.conditionals;


    var curCond = [];
    if (sVal in cond)
	curCond = listify(cond[sVal]);

    //alert(JSON.stringify(curCond));

    var len = show.length;
    for (var i = 0; i < len; ++i) {
	var col = show[i];
	var status = (-1 == curCond.indexOf(col));
	hideColumn(tableId, col, status);
    }
    
    var len = hide.length;
    for (var i = 0; i < len; ++i) {
	var col = hide[i];
	var status = !(-1 == curCond.indexOf(col));
	hideColumn(tableId, col, status);
    }
}

