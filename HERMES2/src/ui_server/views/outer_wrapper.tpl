<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
    <title>{{_('HERMES - Supply Chain Modeling for Public Health')}}</title>

<link rel="shortcut icon" type="image/x-icon" href="{{rootPath}}static/icons/favicon2.ico">
<link rel="stylesheet" href="{{rootPath}}static/jquery-ui-1.10.2/themes/base/jquery-ui.css" />

<link rel="stylesheet" href="{{rootPath}}static/jquery-ui-1.10.2/themes/base/jquery.ui.all.css" />
<link rel="stylesheet" href="{{rootPath}}static/jquery-ui-1.10.2/demos/demos.css" />

<link rel="stylesheet" type="text/css" media="screen" href="{{rootPath}}static/jqGrid-4.4.4/css/ui.jqgrid.css" />
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/jquery-svg-1.4.5/jquery.svg.css" />
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/hermes_custom.css" />
<!-- 
<link rel="stylesheet" type="text/css" href="{{rootPath}}static/jquery-rcrumbs-3234d9e/jquery.rcrumbs.min.css" />
 -->
 <link rel="stylesheet" type="text/css" href="{{rootPath}}static/jquery-rcrumbs-3234d9e/jquery.rcrumbs.css" />
<script src="{{rootPath}}static/jquery-1.9.1.min.js"></script>

<!--
<script src="http://code.jquery.com/ui/1.10.2/jquery-ui.js"></script>
-->
<script src="{{rootPath}}static/jquery-ui-1.10.2/ui/jquery-ui.js"></script>

<!--
	<script src="{{rootPath}}static/jquery-ui-1.10.2/ui/jquery.ui.core.js"></script>
	<script src="{{rootPath}}static/jquery-ui-1.10.2/ui/jquery.ui.widget.js"></script>
	<script src="{{rootPath}}static/jquery-ui-1.10.2/ui/jquery.ui.position.js"></script>
	<script src="{{rootPath}}static/jquery-ui-1.10.2/ui/jquery.ui.menu.js"></script>
-->

<script type="text/javascript" src="{{rootPath}}static/jstree-v.pre1.0/jquery.jstree.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jqGrid-4.4.4/js/i18n/grid.locale-en.js"></script>
<!--
<script type="text/javascript" src="{{rootPath}}static/jqGrid-4.4.4/js/jquery.jqGrid.min.js"></script>
-->
<script type="text/javascript" src="{{rootPath}}static/jqGrid-4.4.4/js/jquery.jqGrid.src.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jQuery-File-Upload-7.4.1/js/jquery.fileupload.js"></script>
<!-- 
<script type="text/javascript" src="{{rootPath}}static/jquery-rcrumbs-3234d9e/jquery.rcrumbs.min.js"></script>
 -->
<script type="text/javascript" src="{{rootPath}}static/jquery-rcrumbs-3234d9e/jquery.rcrumbs.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery-form-3.45.0.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery-migrate-1.2.1.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery.printElement.min.js"></script>
<script type="text/javascript" src="{{rootPath}}static/Jit-2.0.1/jit.js"></script>

<!--
	<link rel="stylesheet" href="../../themes/base/jquery.ui.all.css">
	<script src="../../jquery-1.9.1.js"></script>
	<script src="../../ui/jquery.ui.core.js"></script>
	<script src="../../ui/jquery.ui.widget.js"></script>
	<script src="../../ui/jquery.ui.position.js"></script>
	<script src="../../ui/jquery.ui.menu.js"></script>
	<link rel="stylesheet" href="../demos.css">
-->

<script src="{{rootPath}}static/jQuery-contextMenu-master/src/jquery.ui.position.js" type="text/javascript"></script>
<script src="{{rootPath}}static/jQuery-contextMenu-master/src/jquery.contextMenu.js" type="text/javascript"></script>
    
<link href="{{rootPath}}static/jQuery-contextMenu-master/src/jquery.contextMenu.css" rel="stylesheet" type="text/css" />


<script>
/*
* Magic to make AJAX ops like $.getJSON send the same cookies as normal fetches
*/
$(document).ajaxSend(function (event, xhr, settings) {
	settings.async = true,
    settings.xhrFields = {
       withCredentials: true
    };
});

$(document).ready(function() {
	$('#ajax_busy_blank').show(); 
	$('#ajax_busy_image').hide(); 

	$(document).ajaxStart(function(){ 
		$('#ajax_busy_blank').hide(); 
		$('#ajax_busy_image').show(); 
	})
	.ajaxStop(function(){ 
		$('#ajax_busy_blank').show(); 
		$('#ajax_busy_image').hide(); 
	});
    $("#models_top_breadcrumbs").rcrumbs();
	$("#wrappage_help_dialog").dialog({autoOpen:false});
	var btn = $("#wrappage_help_button");
	btn.click( function() {
		$.getJSON("{{rootPath}}json/page-help",{url:window.location.href})
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					$("#wrappage_help_dialog").html(data.value);		
				}
				else {
					$("#wrappage_help_dialog").html('{{_("Sorry - No help is available for this page.")}}');		
				}
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert('{{_("Error: ")}}'+jqxhr.responseText);
		});
		
		$("#wrappage_help_dialog").dialog("open");		
	});
	
	var langsel = $("#lang-menu");
	var contLangChange = 2;
	$("#langchange-confirm").dialog({
			resizable:false,
			width: 500,
			modal: true,
			title: "Change Language Confirmation",
			buttons: {
					{{_("Continue")}}: function() {
						contLangChange = 1;
						$(this).dialog("close");
					},
					{{_("Cancel")}}: function() {
						contLangChange = 0;
						$(this).dialog("close");
					}
				},
			close: function(event,ui){}
		});
	$("#langchange-confirm").dialog("close")
	langsel.change(function() {
		$("#langchange-confirm").dialog("open");
	});
	$("#langchange-confirm").on("dialogclose" ,function(event,ui){
		//alert(contLangChange);
		if(contLangChange==1){
			$.getJSON("json/change-language",{lang:langsel.val()})
				.done(function() {
					window.location.reload(false);
					})
				.fail(function(jqxhr, textStatus, error) {
					alert(jqxhr.responseText);
				}
			);
			contLangChange = 2;
		};
		//%inlizer.selectLocale(langsel.val())
		//alert(langsel.val());
	});

});

function validateFloat(evt) {
	var theEvent = evt || window.event;
	var key = theEvent.keyCode || theEvent.which;
	key = String.fromCharCode( key );
	var regex = /[0-9]|\.|-/;
	if( !regex.test(key) ) {
    	//theEvent.returnValue = false;
		if(theEvent.preventDefault) theEvent.preventDefault();
	}
}

function reportError(jqxhdrOrData, textStatus, error) {
	if (textStatus) {
		// We got here via a failed AJAX request
		var jqxhdr = jqxhdrOrData;
		if (jqxhdr.responseText && jqxhdr.responseText != '')
			alert('{{_("Error: ")}}'+jqxhdr.responseText);
		else alert('{{_("Error: Failed to talk to the server")}}');
	}
	else {
		var data = jqxhdrOrData;
		if (data.msg != 'Cancelled') alert('{{_("Failed: ")}}'+data.msg);
	}
}

// setup grid print capability for jqGrid.  Add print button to navigation bar and bind to click.
// Thanks to nelsonm: http://www.trirand.com/blog/?page_id=393/help/improved-print-grid-function/
function setPrintGrid(gid,pid,pgTitle){
    // print button title.
    var btnTitle = 'Print Grid';
    // setup print button in the grid top navigation bar.
    $('#'+gid).jqGrid('navSeparatorAdd','#'+gid+'_toppager_left', {sepclass :'ui-separator'});
    $('#'+gid).jqGrid('navButtonAdd','#'+gid+'_toppager_left', {caption: '', title: btnTitle, position: 'last', buttonicon: 'ui-icon-print', onClickButton: function() {    PrintGrid();    } });
    
    // setup print button in the grid bottom navigation bar.
    $('#'+gid).jqGrid('navSeparatorAdd','#'+pid, {sepclass : "ui-separator"});
    $('#'+gid).jqGrid('navButtonAdd','#'+pid, {caption: '', title: btnTitle, position: 'last', buttonicon: 'ui-icon-print', onClickButton: function() { PrintGrid();    } });
    
    function PrintGrid(){
        // attach print container style and div to DOM.
        //$('head').append('<style type="text/css">.prt-hide {display:none;}</style>');
        $('body').append('<div id="prt-container" class="prt-hide"></div>');

        // copy and append grid view to print div container.
        $('#gview_'+gid).clone().appendTo('#prt-container').css({'page-break-after':'auto'});
        // open all subgrids
        //$('#prt-container-div').find(">tr.jqgrow>td.sgcollapsed").click();
        // remove navigation divs.
        $('#prt-container div').remove('.ui-jqgrid-toppager,.ui-jqgrid-titlebar,.ui-jqgrid-pager');
        // print the contents of the print container.    
        $('#prt-container').printElement({pageTitle:pgTitle, 
        	overrideElementCSS:[{href:'{{rootPath}}static/print-container.css',media:'print'}],
        	//leaveOpen:true // this prevents a Chrome bug the eliminates grid lines but has side-effects
        	});
        // remove print container style and div from DOM after printing is done.
        $('head style').remove();
        $('body #prt-container').remove();
    }
}

// Add a method to jqGrid that will allow us to customize.
(function( $ ) {
	$.jgrid.extend({
		/*
    	getRowsById: function (rowid){
        	var totalRows = [];
        	// enum all elements of the jQuery object
        	this.each(function(){
            	if (!this.grid) { return; }
                	// this is the DOM of the table
                	// we
                	var tr = this.rows.namedItem(rowid);
                	if (tr !== null) { // or if (tr !== null)
                    	totalRows.push(tr);
                	}
        	});
        	return totalRows;
    	},
    	*/
    	hermify: function(opts) {
    		this.each(function(){
            	if (!this.grid) { return; }
            	if (opts.debug) {
    				console.log('starting hermify with opts '+opts);
    			}
				var $grid = $(this);
    			var cM = $grid.jqGrid('getGridParam','colModel');
    			var lastT=null;
    			for (var i = 0; i < cM.length; i++) {
    				if (cM[i].edittype == 'text') {
    					lastT = i;
    				}
    			}
    			if (opts.debug) console.log("lastT is "+lastT);
    			if (lastT) {
					var eO = $.extend({},cM[lastT].editoptions);
					var dA = (eO.dataEvents || []);
					dA.push({
		 				type:'keydown',
		 				fn: function(e) {
		 					var key = e.charCode || e.keyCode;
		 					if (key == 9) // tab
		 						{
		 							var rowId = $grid.jqGrid('getGridParam','selrow');
		 							var ids = $grid.jqGrid('getDataIDs');
		 							var indexHere = $grid.jqGrid('getInd',rowId) - 1;
		 							var newIndex = (indexHere + 1) % ids.length;
		 							if (newIndex == indexHere) {
		 								e.preventDefault(); // only one row, so do nothing
		 							}
		 							else {
		 								var extraP = $grid.jqGrid('getGridParam','postData');
										$grid.jqGrid("saveRow", rowId, { extraparam:extraP });
		 								$grid.jqGrid('setSelection',ids[newIndex]);
										e.preventDefault();
									}
		 						}
		 				}
					});
					eO.dataEvents = dA;
					cM[lastT].editoptions = eO;
				}
				else {
					if (opts.debug) console.log('no tabbing mods');
				}
				$grid.jqGrid('setGridParam',{
					loadError: function(xhr,status,error){ alert('{{_("Error: ")}}'+status); },
					beforeProcessing: function(data,status,xhr) {
						if (typeof(data.success) != 'undefined' && !data.success) {
							if (data.msg) alert('{{_("Failed: ")}}'+data.msg);
							else alert('{{_("Failed: No information about the error is available")}}');
						}
					}
				});
				if (opts.debug) console.log('loadError and beforeProcessing set');
            	if (opts.debug) {
    				console.log('finished hermify');
    			}
    		});
    		return this;
    	}
	});
}(jQuery));

// This defines the hrmWidget jquery plugin
(function( $ ) {
    
    $.fn.hrmWidget = function(options) {
 	
        var settings = $.extend({
            // These are the defaults.
            label: "default hrmWidget label",
            innerLabels: true,
            afterBuild: null,
            onChange: null,
            onServerSuccess: null,
            onServerError: null,
            onServerFail: null,
            callbackData: null
        }, options );
        
        var opFuncNames = ['afterBuild','onChange','onServerSuccess','onServerError','onServerFail','callbackData'];
        
 		if (settings['widget']=='modelSelector') {
			$.fn.modelSelector = function( arg ) {
				var sel = this.first().find("select");
				if (arg=='selId') {
					return sel.val();
				}
				else if (arg=='selName') {
					return sel.data('modelName');
				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				$elem = $(elem);
 				$elem.html('<label>'+settings['label']+'</label>');
 				var sel = $(document.createElement("select"));
 				$elem.append(sel);
 				var myThis = this;
				sel.change( function() {
					$.getJSON('{{rootPath}}json/set-selected-model', {id:sel.val()})
					.done(function(data) {
						sel.data('modelName',data['name']);
						if ('onChange' in settings && settings.onChange != null) {
							settings.onChange.bind($(myThis))(sel,data);
						}
	    			})
	  				.fail(function(jqxhr, textStatus, error) {
	  					alert("Error: "+jqxhr.responseText);
					});
				});

				$.getJSON('{{rootPath}}list/select-model')
				.done(function(data) {
    				sel.append(data['menustr']);
    				sel.data('modelName',data['selname']);
    				if ('afterBuild' in settings && settings.afterBuild != null) {
    					settings.afterBuild.bind($elem)(sel,data);
    				}
    			})
  				.fail(function(jqxhr, textStatus, error) {
  					alert("Error: "+jqxhr.responseText);
				});
 			});
 		}
 		else if (settings['widget']=='currencySelector') {
			$.fn.currencySelector = function( arg ) {
 				var myThis = this;
				var sel = this.first().find("select");
				if (arg=='selId') {
					return sel.val();
				}
				else if (arg=='selName') {
					return decodeURIComponent(sel.data('currencyName'));
				}
				else if (arg=='rebuild') {
					var modelId;
					if (settings.modelId instanceof Function) {
						modelId = settings.modelId.bind($(myThis))(sel);
					}
					else modelId = settings.modelId;
					var selected = '';
					if (settings.selected) {
						if (settings.selected instanceof Function) {
							selected = settings.selected.bind($(myThis))(sel);
						}
						else selected = settings.selected;
					}
				
					$.getJSON('{{rootPath}}list/select-currency', { 
						modelId: modelId,
						idstring: encodeURIComponent(selected)
					})
					.done(function(data) {
						if (data.success) {
							sel.data('prev_value',sel.val());
    						sel.html(decodeURIComponent(data['menustr']));
    						if ('afterBuild' in settings  && settings.afterBuild != null) {
    							settings.afterBuild.bind(sel.parent())(sel,data);
    						}
						}
						else {
  							alert('{{_("Failed: ")}}'+data.msg);
						}
    				})
  					.fail(function(jqxhr, textStatus, error) {
  						alert("Error: "+jqxhr.responseText);
					});
				}
				else if (arg=='revert') {
					sel.val(sel.data('prev_value'));
				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {

 				var $elem = $(elem);
 				$elem.html('<label>'+settings['label']+'</label>');
 				var sel = $(document.createElement("select"));
 				$elem.append(sel);
 				var myThis = this;
				sel.change( function(evt) {
					if ('onChange' in settings && settings.onChange != null) {
						var currencyId = $(evt.target).val();
						if ( settings.onChange.bind($(myThis))(evt, currencyId) ) {
							sel.data('prev_value',sel.val());
							var modelId;
							if (settings.modelId instanceof Function) {
								modelId = settings.modelId.bind($(myThis))(sel);
							}
							else modelId = settings.modelId;
							$.getJSON('{{rootPath}}json/set-default-currency', 
								{id:encodeURIComponent(sel.val()), modelId:modelId})
							.done(function(data) {
								if ( data.success ) {
									sel.data('currencyName',decodeURIComponent(data['name']));
								}
								else {
  									alert('{{_("Failed: ")}}'+data.msg);
								}
	    					})
	  						.fail(function(jqxhr, textStatus, error) {
	  							alert("Error: "+jqxhr.responseText);
							});
						}
						else {
							$elem.currencySelector('revert');
						}
					}
				});
				$elem.currencySelector('rebuild');


/*
 				$elem = $(elem);
 				$elem.html('<label>'+settings['label']+'</label>');
 				var sel = $(document.createElement("select"));
 				$elem.append(sel);
 				var myThis = this;
				sel.change( function() {
					$.getJSON('{{rootPath}}json/set-selected-currency', {id:sel.val()})
					.done(function(data) {
						if ( data.success ) {
							sel.data('currencyName',data['name']);
							if ('onChange' in settings && settings.onChange != null) {
								settings.onChange.bind($(myThis))(sel,data);
							}
						}
						else {
  							alert('{{_("Failed: ")}}'+data.msg);
						}
	    			})
	  				.fail(function(jqxhr, textStatus, error) {
	  					alert("Error: "+jqxhr.responseText);
					});
				});

				$.getJSON('{{rootPath}}list/select-currency')
				.done(function(data) {
					if ( data.success ) {
    					sel.append(data['menustr']);
    					sel.data('currencyName',data['selname']);
    					if ('afterBuild' in settings && settings.afterBuild != null) {
    						settings.afterBuild.bind($elem)(sel,data);
    					}
					}
					else {
  						alert('{{_("Failed: ")}}'+data.msg);
					}
    			})
  				.fail(function(jqxhr, textStatus, error) {
  					alert("Error: "+jqxhr.responseText);
				});
*/
 			});
 		}
 		else if (settings['widget']=='typeSelector') {
			$.fn.typeSelector = function( arg ) {
				var sel = this.first().find("select");
 				var myThis = this;
				if (arg=='selValue') {
					return unescape(sel.val());
				}
				else if (arg=='rebuild') {
					var modelId;
					if (settings.modelId instanceof Function) {
						modelId = settings.modelId.bind($(myThis))(sel);
					}
					else modelId = settings.modelId;
					var invtype;
					if (settings.invtype instanceof Function) {
						invtype = settings.invtype.bind($(myThis))(sel);
					}
					else invtype = settings.invtype;
					var selected = '';
					if (settings.selected) {
						if (settings.selected instanceof Function) {
							selected = settings.selected.bind($(myThis))(sel);
						}
						else selected = settings.selected;
					}
				
					$.getJSON('{{rootPath}}list/select-type', { 
						modelId: modelId,
						invtype: invtype,
						encode: true,
						typestring: selected
					})
					.done(function(data) {
    					sel.html(data['menustr']);
						sel.data('prev_value',sel.val());
    					if ('afterBuild' in settings  && settings.afterBuild != null) {
    						settings.afterBuild.bind(sel.parent())(sel,data);
    					}
    				})
  					.fail(function(jqxhr, textStatus, error) {
  						alert("Error: "+jqxhr.responseText);
					});
				}
				else if (arg=='revert') {
					sel.val(sel.data('prev_value'));
				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				var $elem = $(elem);
 				$elem.html('<label>'+settings['label']+'</label>');
 				var sel = $(document.createElement("select"));
 				$elem.append(sel);
 				var myThis = this;
				sel.change( function(evt) {
					if ('onChange' in settings && settings.onChange != null) {
						var typeName = unescape($(evt.target).val());
						if ( settings.onChange.bind($(myThis))(evt, typeName) ) {
							sel.data('prev_value',sel.val());
						}
						else {
							$elem.routeTypeSelector('revert');
						}
					}
				});
				$elem.typeSelector('rebuild');
 			});
 		}
 		else if (settings['widget']=='routeTypeSelector') {
			$.fn.routeTypeSelector = function( arg ) {
				var sel = this.first().find("select");
 				var myThis = this;
				if (arg=='selValue') {
					return unescape(sel.val());
				}
				else if (arg=='rebuild') {
					var selected = '';
					if (settings.selected) {
						if (settings.selected instanceof Function) {
							selected = settings.selected.bind($(myThis))(sel);
						}
						else selected = settings.selected;
					}
				
					$.getJSON('{{rootPath}}list/select-route-type', { 
						typestring: selected
					})
					.done(function(data) {
    					sel.html(data['menustr']);
    					sel.data('prev_value',sel.val());
    					if ('afterBuild' in settings && settings.afterBuild != null) {
    						settings.afterBuild.bind(sel.parent())(sel,data);
    					}
    				})
  					.fail(function(jqxhr, textStatus, error) {
  						alert("Error: "+jqxhr.responseText);
					});
				}
				else if (arg=='revert') {
					sel.val(sel.data('prev_value'));
				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				var $elem = $(elem);
 				$elem.html('<label>'+settings['label']+'</label>');
 				var sel = $(document.createElement("select"));
 				$elem.append(sel);
 				var myThis = this;
				sel.change( function(evt) {
					if ('onChange' in settings && settings.onChange != null) {
						var typeName = unescape($(evt.target).val());
						if ( settings.onChange.bind($(myThis))(evt, typeName) ) {
    						sel.data('prev_value',sel.val());
						}
						else {
							$elem.routeTypeSelector('revert');
						}
					}
				});
				$elem.routeTypeSelector('rebuild');
 			});
 		}
 		else if (settings['widget']=='boxCalendar') {
			$.fn.boxCalendar = function( arg, arg2 ) {
				var $tbl = this.find("table");
	 			var divId = this.attr('id');
 				if (divId == undefined) $.error('wrapper div has no id');
 				var cboxArray = $tbl.find('input');
 				if (cboxArray.length != (7+4+12)) $.error('boxCalendar has the wrong number of boxes');
				if (arg=='getState') {
 					var offset = 0;
 					var str = '';
 					for (var i=0; i<7; i++) {
 						cb = cboxArray[offset]
 						if (cb.id != (divId + '_0_'+i)) $.error('boxCalendar boxes are not in order');
 						if (cb.checked) str += '1';
 						else str += '0';
 						offset += 1;
 					}
 					str += ':'
 					for (var i=0; i<4; i++) {
 						cb = cboxArray[offset]
 						if (cb.id != (divId + '_1_'+i)) $.error('boxCalendar boxes are not in order');
 						if (cb.checked) str += '1';
 						else str += '0';
 						offset += 1;
 					}
 					str += ':'
 					for (var i=0; i<12; i++) {
 						cb = cboxArray[offset]
 						if (cb.id != (divId + '_2_'+i)) $.error('boxCalendar boxes are not in order');
 						if (cb.checked) str += '1';
 						else str += '0';
 						offset += 1;
 					}
 					return str;
				}
				else if (arg=='setState') {
					var offset = 0;
					var parts = arg2.split(':');
					if ((parts.length != 3) 
						|| (parts[0].length != 7) || (parts[1].length != 4) || (parts[2].length != 12))
						$.error('boxCalendar set string format is invalid');
 					for (var i=0; i<7; i++) {
 						cb = cboxArray[offset]
 						if (cb.id != (divId + '_0_'+i)) $.error('boxCalendar boxes are not in order');
 						if (parts[0].charAt(i) == '0') cb.checked = false;
 						else if (parts[0].charAt(i) == '1') cb.checked = true;
 						else $.error('boxCalendar set string format is invalid');
 						offset += 1;
 					}
 					for (var i=0; i<4; i++) {
 						cb = cboxArray[offset]
 						if (cb.id != (divId + '_1_'+i)) $.error('boxCalendar boxes are not in order');
 						if (parts[1].charAt(i) == '0') cb.checked = false;
 						else if (parts[1].charAt(i) == '1') cb.checked = true;
 						else $.error('boxCalendar set string format is invalid');
 						offset += 1;
 					}
 					for (var i=0; i<12; i++) {
 						cb = cboxArray[offset]
 						if (cb.id != (divId + '_2_'+i)) $.error('boxCalendar boxes are not in order');
 						if (parts[2].charAt(i) == '0') cb.checked = false;
 						else if (parts[2].charAt(i) == '1') cb.checked = true;
 						else $.error('boxCalendar set string format is invalid');
 						offset += 1;
 					}
 					$tbl.attr('data-old-state',arg2);
				}
 				else if (arg=='revertState') {
 					var oldState = $tbl.attr('data-old-state');
 					this.boxCalendar('setState',oldState);
 				}
 				else if (arg=='saveState') {
 					var state = this.boxCalendar('getState');
 					$tbl.attr('data-old-state',state);
 				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				$elem = $(elem);
 				var divId = $elem.attr('id');
 				if (divId == undefined) $.error('wrapper div has no id');
 				$elem.html('<label>'+settings['label']+'</label>');
 				var $tbl = $(document.createElement("table"));
 				$tbl.addClass('hrm_boxcalendar');
 				var l0 = "";
 				var l1 = "";
 				var l2 = "";
 				if (settings['innerLabels']) {
 					l0 = '{{_("days each week")}}';
 					l1 = '{{_("weeks each month")}}';
 					l2 = '{{_("months each year")}}';
 				}
 				var $row = $('<tr />').html('<td style="text-align:right;">'+l0+'</td>');
 				$row.addClass('hrm_boxcalendar');
 				for (var i = 0; i<7; i++) {
 					var $td = $('<td />');
 					$td.addClass('hrm_boxcalendar');
 					$('<input />', { type: 'checkbox', id: divId+'_0_'+i}).appendTo( $td );
 					$td.appendTo($row);
 				}
				$row.appendTo($tbl);
 				var $row = $('<tr />').html('<td style="text-align:right;">'+l1+'</td>');
 				$row.addClass('hrm_boxcalendar');
 				for (var i = 0; i<4; i++) {
 					var $td = $('<td />');
 					$td.addClass('hrm_boxcalendar');
 					$('<input />', { type: 'checkbox', id: divId+'_1_'+i}).appendTo( $td );
 					$td.appendTo($row);
 				}
				$row.appendTo($tbl);
 				var $row = $('<tr />').html('<td style="text-align:right;">'+l2+'</td>');
 				$row.addClass('hrm_boxcalendar');
 				for (var i = 0; i<12; i++) {
 					var $td = $('<td />');
 					$td.addClass('hrm_boxcalendar');
 					$('<input />', { type: 'checkbox', id: divId+'_2_'+i}).appendTo( $td );
 					$td.appendTo($row);
 				}
				$row.appendTo($tbl);
 				$elem.append($tbl);
 				
 				$elem.change( function() {
					if ('onChange' in settings && settings.onChange != null) {
						settings.onChange.bind($(this))($tbl);
					}
 				});

    			if ('afterBuild' in settings && settings.afterBuild != null) {
    				settings.afterBuild.bind($elem)($tbl);
    			};

 			});
 		}
 		else if (settings['widget']=='tooltips') {
			$.fn.tooltips = function( arg, arg2 ) {
				if (arg=='applyTips') {
					$.each(settings['tips'], function(key,value) {
						$(key).each( function(counter) {
							$this = $(this);
							if (! $this.attr('title')) {
								if (typeof value === 'function') {
									$this.attr('title', value(this));
								}
								else {
									$this.attr('title',value);
								}
							}
						});
					});			
				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

			$(document).tooltip({show:{effect:"slideDown", duration:800, delay:1000},
								hide:{effect:"slideUp", duration:800, delay:1000}});

 			return this.first().each(function(index,elem) {
 				$(elem).tooltips('applyTips');
 			});
 		}
 		else {
 			var opFuncs = {};
        	for (var i = 0; i<opFuncNames.length; i++) {
        		if (settings[opFuncNames[i]]) {
        			opFuncs[opFuncNames[i]] = settings[opFuncNames[i]];
        			delete settings[opFuncNames[i]];
				}
        	}
 			return this.each(function(index,elem) {
        		$elem = $(elem);
        		$elem.data('opFuncs',opFuncs);
				$.getJSON( "{{rootPath}}json/widget-create", settings )
				.done(function(data) {
					if (data.success) {
						$elem.html(data['htmlstring']);
						if (opFuncs['afterBuild'])
							opFuncs['afterBuild']();
						if ($(document).tooltips) $(document).tooltips('applyTips');
					}
					else {
						alert('{{_("Error: ")}}'+data.msg);
					}
				})
				.fail(function(jqxhdr, textStatus, error) {
					alert('{{("Failed: ")}}' + jqxhdr.responseText);
				});
			});
 		};
 	};
}( jQuery ));

% if defined('backNextButtons') and backNextButtons:

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = window.location.pathname + "/back"
	});
});

$(function() {
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		window.location = window.location.pathname + "/next";
	});
});

%end

% if defined('doneButton') and doneButton:

$(function() {
	var btn = $("#done_button");
	btn.button();
	btn.click( function() {
		window.location = window.location.pathname + "/done"
	});
});

%end

</script>

<style>.art-content .art-postcontent-0 .layout-item-0 { padding: 0px;  }
	.art-content .art-postcontent-0 .layout-item-1 { padding-right: 10px;padding-left: 10px;  }
	.ie7 .post .layout-cell {border:none !important; padding:0 !important; }
	.ie6 .post .layout-cell {border:none !important; padding:0 !important; }

</style>
    	
</head>

<body>
	<!-- IFrame for shim to google earth plugin -->
	<iframe id="content-iframe" style="border:0px;width:0px;height:0px"></iframe>
	<div id="art-main">
		<header class="art-header clearfix">
			<div class="art-shapes" style="width:1000px;">
				<div style="float:left">
	     			<h1 class="art-headline">
						HERMES
					</h1>
	     			<h2 class="art-slogan">
						{{get('title_slogan','Slogan is undefined')}}
					</h2>
				</div>
				<div style="float:right">
					%if inlizer.implemented:
					<h3 style="color:white;display:inline;">Languages:</h3>
					<h3 style="display:inline;">
						<select id="lang-menu">
							%for lang in inlizer.supportedLocales:
								%if lang == inlizer.currentLocaleName:
									<option selected>{{lang}}</option>
								%else:
									<option>{{lang}}</option>
								%end
							%end
						</select>
					</h3>
					%end
				</div>
			</div>
             	<!-- <div class="art-object1679104977"></div> -->                                       
		</header>
		
		<nav class="art-nav clearfix">
			<div class="art-nav-inner">
	  			<ul class="art-hmenu">
	    			<li><a href="{{rootPath}}top?crmb=clear">{{_('Welcome')}}</a></li>
	    			<li><a href="{{rootPath}}models-top?crmb=clear">{{_('Models')}}</a></li>
	    			<li><a href="{{rootPath}}people-top?crmb=clear">{{_('People')}}</a></li>
	    			<li><a href="{{rootPath}}vaccines-top?crmb=clear">{{_('Vaccines')}}</a></li>
	    			<li><a href="{{rootPath}}fridge-top?crmb=clear">{{_('ColdStorage')}}</a></li>
	    			<li><a href="{{rootPath}}truck-top?crmb=clear">{{_('Transport')}}</a></li>
	    			<li><a href="{{rootPath}}demand-top?crmb=clear">{{_('Demand')}}</a></li>
	    			<li><a href="{{rootPath}}cost-top?crmb=clear">{{_('Costs')}}</a></li>
	    			<li><a href="{{rootPath}}run-top?crmb=clear">{{_('Run Hermes')}}</a></li>
	    			<li><a href="{{rootPath}}results-top?crmb=clear">{{_('Results')}}</a></li>
	    			<li><a href="{{rootPath}}tabs">{{_('Developer')}}</a></li>
	    			<li><a href="{{rootPath}}show-help">{{_('Help')}}</a></li>
	  			</ul> 
     			</div>
		</nav>
      
		<div class="art-sheet clearfix">
			<div class="art-layout-wrapper clearfix">
	  			<div class="art-content-layout">
	  			
	    				<div class="art-content-layout-row">
	      					<div class="art-layout-cell art-content clearfix">
	      				
	      						<article class="art-post art-article">
		  						<div class="art-postcontent art-postcontent-0 clearfix">
		  							<div class="art-content-layout">			
		    							<div class="art-content-layout">
		     								<div class="art-content-layout-row">
		     								

												<div id="wrappage_help_dialog" title="Quick Help">
												<p>{{_("This text will be replaced.")}}
												</div>


												<table style="width:100%;border-style=none" >
												<tr>
													<td>
														<div class="rcrumbs" id="models_top_breadcrumbs">
															%if defined('breadcrumbPairs'):
																%if isinstance(breadcrumbPairs,type([])):
																	<ul>
																	%  for ref,lbl in breadcrumbPairs[:-1]:
																		<li><a href="{{rootPath}}{{ref}}">{{lbl}}</a><span class="divider"></span>></li>
																	%  end
																	%ref,lbl = breadcrumbPairs[-1]
																	<li><a href="{{rootPath}}{{ref}}">{{lbl}}</a></li>
																	</ul>
																%  else:
																	{{! breadcrumbPairs.render() }}
																%  end
															%else:
															<ul></ul>
															%end
														</div>
													</td>
													<td width=10% align='right'>
														<div id="ajax_busy">
														  <img id="ajax_busy_blank" src="{{rootPath}}static/icons/ajax-loader-blank.png" width='32' height='32' />
														  <img id="ajax_busy_image" src="{{rootPath}}static/icons/ajax-loader.gif" width='32' height='32' />
														</div>
													</td>
													<td width=10%>
														<input type="image" id="wrappage_help_button" src="{{rootPath}}static/icons/helpicon.bmp">
													</td>
												</tr>
											</table>

% if defined('topCaption'):
<h3>{{topCaption}}</h3>
%end

%include

% if defined('backNextButtons') and backNextButtons:
<form>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
      </tr>
    </table>
</form>
% elif defined('doneButton') and doneButton:
<form>
    <table width=100%>
      <tr>
        <td></td>
        <td width=10%><input type="button" id="done_button" value={{_("Done")}}></td>
      </tr>
    </table>
</form>
% end



									<div id="langchange-confirm" title={{_("Language Change Warning")}}>Changing the language will reset all unsaved input</div>

		      							</div>
		    						</div>
		  						</div>
		  					</div>
                			</article>	
	      				</div>
	    			</div>
	  			</div>
			</div>
		</div>
	
		<footer class="art-footer clearfix">
			<div class="art-footer-inner">
	  			&nbsp; &nbsp; &nbsp; &nbsp;{{_('HERMES Project')}} - Copyright © 2013. {{_('All Rights Reserved.')}}
			</div>
		</footer> 
    </div>    
</body>
