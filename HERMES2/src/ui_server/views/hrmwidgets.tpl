// Thanks to Patrick Desjardins http://stackoverflow.com/questions/149055/how-can-i-format-numbers-as-money-in-javascript
/*
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
*/
Number.prototype.formatMoney = function(c, d, t){
var n = this, 
    c = isNaN(c = Math.abs(c)) ? 2 : c, 
    d = d == undefined ? "." : d, 
    t = t == undefined ? "," : t, 
    s = n < 0 ? "-" : "", 
    i = parseInt(n = Math.abs(+n || 0).toFixed(c)) + "", 
    j = (j = i.length) > 3 ? j % 3 : 0;
   return s + (j ? i.substr(0, j) + t : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + t) + (c ? d + Math.abs(n - i).toFixed(c).slice(2) : "");
 };
 
 String.prototype.unformatMoney = function(t) {
	 var cStr = this, 
	    t = t == undefined ? "," : t;
	 var val = Number(cStr.replace(t,"").replace(t,""));
	 return val;
 };

 // Thanks to Anentropic http://stackoverflow.com/questions/1219860/html-encoding-in-javascript-jquery
 String.prototype.htmlEscape = function() {
	 return this.replace(/&/g, '&amp;')
     .replace(/"/g, '&quot;')
     .replace(/'/g, '&#39;')
     .replace(/</g, '&lt;')
     .replace(/>/g, '&gt;');
 };
 
// setup grid print capability for jqGrid.  Add print button to navigation bar and bind to click.
// Thanks to nelsonm: http://www.trirand.com/blog/?page_id=393/help/improved-print-grid-function/
function setPrintGrid(gid,pid,pgTitle){
    // print button title.
    var btnTitle = '{{_("Print Grid")}}';
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

// adds a 'expand/collapse all' button to the header row; this should only be
// used for grids that contain subgrids (governed by opts.has_subgrid); this
// function is called from hermify
function addToggleExpansionButton($grid) {
    var plusIcon = 'ui-icon-plus';
    var minusIcon = 'ui-icon-minus';
    $("#jqgh_" + $grid[0].id + "_subgrid")
        .html('<a style="cursor: pointer;">'
            + '<span class="ui-icon ' + plusIcon
            + '" title={{_("expand/collapse")}}>'
            + '</span></a>')
        .click(function () {
            var $spanIcon = $(this).find(">a>span"),
                $body = $(this).closest(".ui-jqgrid-view")
                    .find(">.ui-jqgrid-bdiv>div>.ui-jqgrid-btable>tbody");
            if ($spanIcon.hasClass(plusIcon)) {
                $spanIcon.removeClass(plusIcon)
                    .addClass(minusIcon);
                $body.find(">tr.jqgrow>td.sgcollapsed")
                    .click();
            } else {
                $spanIcon.removeClass(minusIcon)
                    .addClass(plusIcon);
                $body.find(">tr.jqgrow>td.sgexpanded")
                    .click();
            }
        }
    );
}

// Add a method to jqGrid that will allow us to customize.
(function( $ ) {
	$.jgrid.extend({
		hermify: function(opts) {
    		this.each(function(){
            	if (!this.grid) { return; }

            	if (opts.debug) {
    				console.log('starting hermify with opts: '
                        + JSON.stringify(opts));
    			}
				
                var $grid = $(this);

    			var cM = $grid.jqGrid('getGridParam','colModel');
    			var lastT = null;
    			for (var i = 0; i < cM.length; i++) {
    				if (cM[i].edittype == 'text') {
    					lastT = i;
    				}
    			}
    			if (opts.debug) console.log("lastT is " + lastT);
    			if (lastT) {
					var eO = $.extend({},cM[lastT].editoptions);
					var dA = (eO.dataEvents || []);
					dA.push({
		 				type:'keydown',
		 				fn: function(e) {
		 					var key = e.charCode || e.keyCode;
		 					if (key == 9) { // tab
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
					},
					autoencode:true
				});
				if (opts.debug) console.log('loadError, beforeProcessing, and autoencode set');
				if (opts.resizable) {
					function resize_grid() {
						var offset = $grid.offset(); //position of grid on page
						//hardcoded minimum width
						if ( $(window).width() > 710 ) {
                            // the maximum width should be set as a freaction of the available
                            // space, rather than subtracting a fixed amount.
                            if (!opts.subgrid) {
							    $grid.jqGrid('setGridWidth', $(window).width()-offset.left-50);
                            }
                            else {
                                $grid.jqGrid('setGridWidth', $(window).width()-offset.left-70);
                            }
						}
                        if (!opts.subgrid) {
    						$grid.jqGrid('setGridHeight', $(window).height()-offset.top-130);
                        }
					}
					$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
					$(window).resize(resize_grid);  //bind resize_grid to window resize
					resize_grid();
					if (opts.debug) console.log('resize handling set');
					
				}
				if (opts.resizable_hz) {
					function resize_grid_hz() {
						var offset = $grid.offset(); //position of grid on page
						//hardcoded minimum width
						if ( $(window).width() > 710 ) {
                            // the maximum width should be set as a freaction of the available
                            // space, rather than subtracting a fixed amount.
                            if (!opts.subgrid) {
							    if ($grid.parent().parent().parent().parent().parent().prop("tagName").toLowerCase()=='td') {
                                    $grid.jqGrid('setGridWidth', $(window).width()-offset.left-50);
                                } else {
                                    $grid.jqGrid('setGridWidth', $grid.parent().parent().parent().parent().parent().width()-2);
                                }
                            }
                            else {
                                $grid.jqGrid('setGridWidth', $(window).width()-offset.left-70);
                            }
						}
					}
					$(window).load(resize_grid_hz); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
					$(window).resize(resize_grid_hz);  //bind resize_grid to window resize
					resize_grid_hz();
					if (opts.debug) console.log('horizontal resize handling set');
					
				}
				if (opts.printable) {
					if (opts.debug) console.log('starting printable handling');
					var gridId = this.id;
					var pagerId = $($(this).jqGrid('getGridParam','pager')).attr('id');
					var caption = $(this).jqGrid('getGridParam','caption');
					if (gridId && pagerId) {
						if (opts.debug) 
							console.log('setPrintGrid '+gridId+' '+pagerId+' '+caption);
						setPrintGrid(gridId, pagerId, caption);						
					}
					else {
						if (opts.debug)
							console.log('missing ids so no printable can be set');
					}
					if (opts.debug) console.log('finished printable handling');
				}
//				if (opts.groupby) {
//					if (opts.debug) console.log('group by '+opts.groupby);
//					$grid.jqGrid('setGridParam',{ grouping:true });
//					$grid.jqGrid('groupingGroupBy', opts.groupby, {
//						groupField:[opts.groupby],
//						groupDataSorted:true,
//						groupText:['<b>{0} - {1} '+"{{_('Item(s)')}}"+'</b>'],
//						groupColumnShow:[false]
//					});
//					$grid.jqGrid('groupingSetup');
//					this.grid.populate();
//					if (opts.debug) console.log('finished grouping');
//				}
				if ($grid.jqGrid('getGridParam','grouping')) {
					if (opts.debug) console.log('attempting to modify grouped behavior');
					var groupCollapsed = {};
					$grid.jqGrid('setGridParam', {
						onClickGroup: function(hid, collapsed) {
							var idPrefix = this.id + "ghead_";
							var $this = $(this);
							var groups = $(this).jqGrid("getGridParam", "groupingView").groups;
							var offset = hid.lastIndexOf('_');
							var gid = parseInt(hid.substr(offset+1));
							//console.log('change to '+groups[gid].displayValue+' : now collaped = '+collapsed);
							groupCollapsed[gid] = collapsed;
						},
					    loadComplete: function () {
					        var $this = $(this), i, l;
							var groups = $(this).jqGrid("getGridParam", "groupingView").groups;
					        for (i = 0, l = groups.length; i < l; i++) {
					        	if (groupCollapsed[i] != undefined && !groupCollapsed[i]) {
					                $this.jqGrid('groupingToggle', this.id + 'ghead_' + groups[i].idx + '_' + i);
					        	}
					        }
					    },						
					})
					if (opts.debug) console.log('done modifying grouped behavior');
				}
            	if (opts.debug) {
    				console.log('finished hermify');
    			}

                // expand-collapse all button if we have subgrids
                if (opts.has_subgrid) {
                    addToggleExpansionButton($grid);
                }
                
                $grid.jqGrid("setGridParam", {
                    afterInsertRow: function(rowid, rowdata, rowelem) {
                        $grid.find("button").button();
                    }
                });
                
                //appends this function to already-defined gridComplete
                $grid.bind('jqGridGridComplete.jqGrid',function(e) {
                    $grid.find("button").button();
                });

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
            callbackData: null,
        }, options );
        
        var opFuncNames = ['afterBuild','onChange','onServerSuccess','onServerError','onServerFail','callbackData'];
        
 		if (settings['widget']=='modelSelector') {
			$.fn.modelSelector = function( arg, arg2 ) {
				var sel = this.first().find("select");
				if (arg=='selId') {
					return sel.val();
				}
				else if (arg=='selName') {
					return sel.data('modelName');
				}
				else if (arg=='setId'){
					if (arg2 == undefined) {
						return;
					}
					else {
						sel.val(arg2).change();
					}
				}
				else if (arg=='activate'){
					sel.prop('disabled',false);
					//only works in Chrome
					sel.css("-webkit-appearance","menulist");
					
				}
				else if (arg=='deactivate'){
					sel.prop('disabled',true);
					//only works in Chrome
					sel.css("-webkit-appearance","none");
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
 				$(sel).addClass('hrm_widget_modelSelector');
 				var myThis = this;
				sel.change( function(evt) {
					$.getJSON('{{rootPath}}json/set-selected-model', {id:sel.val()})
					.done(function(data) {
						sel.data('modelName',data['name']);
						if ('onChange' in settings && settings.onChange != null) {
							settings.onChange.bind($(myThis))(evt, sel.val());
						}
	    			})
	  				.fail(function(jqxhr, textStatus, error) {
	  					alert("Error: "+jqxhr.responseText);
					});
				});

				var parms = {};
			        if ('writable' in settings)
				    if (settings.writeable)
					parms.writeable = true;
			        if ('includeRef' in settings)
				    parms.includeRef = 1;
			        if ('selectModel' in settings)
				    parms.selectModel = settings.selectModel;
				$.getJSON('{{rootPath}}list/select-model',parms)
				.done(function(data) {
    				sel.append(data['menustr']);
    				sel.data('modelName',data['selname']);
    				if ('afterBuild' in settings && settings.afterBuild != null) {
    					settings.afterBuild.bind($elem)(sel,data);
    				}
					if ($(document).tooltips) $(document).tooltips('applyTips');
    			})
  				.fail(function(jqxhr, textStatus, error) {
  					alert("Error: "+jqxhr.responseText);
				});
 			});
 		}
 		else if (settings['widget']=='currencySelector1') {
 			$.fn.currencySelector1 = function( arg ) {
 				var myThis = this;
 				var sel = this.first().find("select");
 				if (arg=='selId') {
 					return sel.val();
 				}
 				else if (arg=='rebuild') {
 					var modelId;
 					if (settings.modelId instanceof Function) {
 						modelId = settings.modelId.bind($(myThis))(sel);
 					}
 					else {
 						modelId = settings.modelId;
 					}
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
 							sel.html(decodeURIComponent(data['menustr']));
 							sel.data('prev_value',sel.val());
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
 				else if (arg=='save') {
 					sel.data('prev_value', sel.val());
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
 						settings.onChange.bind($(myThis))(evt, $(evt.target).val());
 					}
 					else {
 						$elem.currencySelector1('save');
 					}
 				});
 				$elem.currencySelector1('rebuild');
 			});
 		}
 		else if (settings['widget']=='currencySelector') {
			function buildDialog(parent) {
				$('#hrm_cur_sel_dlg_div_shared').remove();  // in case it exists
				var $dlgDiv = $(document.createElement('div')).attr('id','hrm_cur_sel_dlg_div_shared');
				if (!parent) parent = $(this);
				parent.append($dlgDiv);
				var $btn;
				if (parent.is('button')) $btn = parent;
				else $btn = parent.find('button').first();
				var modelId;
				if (settings.modelId instanceof Function) {
					modelId = settings.modelId.bind($(this))($btn);
				}
				else {
					modelId = settings.modelId;
				}
				var selected='';
				if ($btn && $btn.data('code') && $btn.data('code')!='') {
					selected = $btn.data('code');
				}
				else if (settings.selected) {
					if (settings.selected instanceof Function)
						selected = settings.selected.bind($(this))($btn);
					else 
						selected = settings.selected;
				}
				var recreate;
				if (settings.recreate) recreate = true;
				else recreate = false;
 				$dlgDiv.dialog({
					autoOpen:false,
					draggable:false,
					dialogClass:'hrm_dialog_no_title',
					maxHeight:600,
					minHeight:100,
					position:{my:'left top', at:'left top', of:$btn},
					resizable:true,
					closeOnEscape:true,
					buttons: {
						'{{_("Close")}}': function(evt) {
							$('#hrm_cur_sel_dlg_div_shared').dialog('close');
							if (recreate) {
								$('#hrm_cur_sel_dlg_div_shared').remove();
							}
						},
					},
				});
    			$dlgDiv.data('currentBtn',$btn);
				$.getJSON('{{rootPath}}list/select-currency', { 
					modelId: modelId,
					idstring: encodeURIComponent(selected)
				})
				.done(function(data) {
					if (data.success) {
						//$dlgDiv.data('defaultSelection',decodeURIComponent(data.defaultid));
						$dlgDiv.data('defaultSelection',data.defaultid.htmlEscape());
						$dlgDiv.html("");
	    				//var selId = decodeURIComponent(data.selid);
	    				var selId = data.selid.htmlEscape();
						var $ul = $(document.createElement('ul'));
		    			for (var i = 0; i < data.pairs.length; i++) {
		    				//var curCode = decodeURIComponent(data.pairs[i][1]);
		    				var curCode = data.pairs[i][1];
		    				//var curStr = decodeURIComponent(data.pairs[i][0]);
		    				var curStr = data.pairs[i][0];
		    				var $li = $(document.createElement('li'))
		    				.data('code',curCode)
		    				.data('str',curStr);

					    	if ($li.data('code') == selId) $li.addClass('selected');		    		
		    				
		    				var $a = $(document.createElement('a'))
		    				.attr('href','#')
			    			.text(curCode + ' : ' + curStr);
		    				$li.append($a);
		    				$ul.append($li);

		    			}
		    			$ul.menu();
		    			$dlgDiv.append($ul);
		    			$('.hrm_cur_sel_btn').each(function() {
		    				if ( ! $(this).button('option','text') 
		    						|| $(this).button('option','label') == '') {
		    					$(this).button('option','label', selId)
		    					.button('option','text', true)
		    					.data('code',selId)
		    					.data('prev_value',selId);
		    				}
	    				}); 
		    				
		    			// Need to use this instance's menu select handler to get
		    			// options context right.
		    			$dlgDiv.find('ul').first()
		    			.off('menuselect')
		    			.on('menuselect', function(evt,ui) {
		    				var $li = $(ui.item);
		    				var newCode = $li.data('code');
		    				$dlgDiv.find('a').removeClass('selected');
		    				$li.addClass('selected');
		    				var $btn = $dlgDiv.data('currentBtn');
		    				$btn.button('option','label', newCode.htmlEscape())
		    				.data('code',newCode);
		    				$dlgDiv.dialog('close');
		    				$btn.data('changeHandler').bind($btn.parent())(evt, newCode);
		     				if (settings.recreate) $dlgDiv.remove();
		    			});
					}
					else {
							alert('{{_("Failed: ")}}'+data.msg.htmlEscape());
					}
				})
					.fail(function(jqxhr, textStatus, error) {
						alert("Error: "+jqxhr.responseText.htmlEscape());
				});
				return $dlgDiv;
				
			};
			function btnClick(evt) {
				evt.preventDefault();
				
				var $b = $(evt.target).parent();
				var $dlgDiv;
				if (settings.recreate) { 
					$dlgDiv = buildDialog.bind($b)($b);
				}
				else {
					$dlgDiv = $('#hrm_cur_sel_dlg_div_shared');
					$dlgDiv.data('currentBtn',$b)
				    .find('a').each( function() {
				    	var $li = $(this).parent();
				    	$li.removeClass('selected');
				    	if ($li.data('code') == $b.data('code'))
				    		$li.addClass('selected');		    		
				    });
				}
				
				$dlgDiv.dialog('option', 'position',
						{my:'left top', at:'left top', of:this}
				);
				$dlgDiv.dialog('open').dialog('widget').zIndex($b.zIndex()+2); 
			};
			$.fn.currencySelector = function( arg, arg2 ) {
 				var myThis = this;
 				var $btn = this.find("button").first();
				if (arg=='selId') {
					if (arg2 == undefined) {
						return $btn.data('code');
					}
					else {
						$btn.data('code',arg2);
						if (arg2 == '' || arg2 == null)
							$btn.button('option', 'label', '???');
						else
							$btn.button('option','label',arg2.htmlEscape());						
						return $btn.data('code');
					}
				}
				else if (arg=='rebuild') {
					if (! settings.recreate) {
						var $dlgDiv = $('#hrm_cur_sel_dlg_div_shared');
						if ($dlgDiv.length == 0) $dlgDiv = buildDialog.bind(myThis)(myThis);						
					}
    				if ('afterBuild' in settings  && settings.afterBuild != null) {
    					settings.afterBuild.bind($btn.parent())($btn);
    				}
					if ($(document).tooltips) $(document).tooltips('applyTips');
				}
				else if (arg=='save') {
					$btn.data('prev_value', $btn.data('code'));
				}
				else if (arg=='revert') {
					var oldCode = $btn.data('prev_value');
					$btn.data('code', oldCode);
					$btn.button('option','label',oldCode);						
				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				var $elem = $(elem);
 				$elem.html('<label>'+settings['label'].htmlEscape()+'</label>');
				var $btn = $(document.createElement('button'));
 				$btn.addClass('hrm_widget_currencySelector');
				var selected;
				if (settings.selected) {
					if (settings.selected instanceof Function)
						selected = settings.selected.bind($(this))($btn);
					else 
						selected = settings.selected;
				}
 				$elem.append($btn);
 				if (selected) {
 					$btn.button({
 						icons: { secondary:'ui-icon-triangle-1-s' },
 						label:selected.htmlEscape()
 					})
 					.data('code',selected)
 					.data('prev_value',selected);
 				}
 				else {
					var $dlgDiv = $('#hrm_cur_sel_dlg_div_shared');
					if ($('#hrm_cur_sel_dlg_div_shared').length == 0
							|| ! $('#hrm_cur_sel_dlg_div_shared').hasClass('ui-dialog-content')) {
	 					$btn.button({
	 						icons: { secondary:'ui-icon-triangle-1-s' },
	 						text:false
	 					}) 					
					}
					else {
						selected = $dlgDiv.data('defaultSelection');
	 					$btn.button({
	 						icons: { secondary:'ui-icon-triangle-1-s' },
	 						label:selected
	 					})
	 					.data('code',selected)
	 					.data('prev_value',selected);						
					}
 				}
				$btn.data('changeHandler', function(evt,newCode) {
	     			if ('onChange' in settings && settings.onChange != null) {
	     				settings.onChange.bind(this)(evt, newCode);
	     			}
	     			else {
	     				this.currencySelector('save');
	     			}
 				});
				$btn.addClass('hrm_cur_sel_btn').click(btnClick);
				
				$elem.currencySelector('rebuild');			
 			});
 		}

 		else if (settings['widget']=='energySelector') {
			$.fn.energySelector = function( arg, arg2 ) {
				var sel = this.first().find("select");
 				var myThis = this;
				if (arg=='selId') {
					if (arg2) {
						sel.val(arg2);
						sel.data('requested', arg2);
						return arg2;
					}
					else {
						return sel.val();
					}
				}
				else if (arg=='selPhrase') {
					return sel.find(':selected').first().text();
				}
				else if (arg=='rebuild') {
					var selected = '';
					if (settings.selected) {
						if (settings.selected instanceof Function) {
							selected = settings.selected.bind($(myThis))(sel);
						}
						else selected = settings.selected;
						sel.data('prev_value',selected);
					}
				
					var url = settings.OptionURL || '{{rootPath}}list/select-energy';
					$.getJSON(url, { 
						encode: true,
						selected: selected,
						allowblank: (!!settings.canBeBlank)
					})
					.done(function(data) {
						if (data.success) {
							sel.html(data['menustr']);
							if (sel.data('requested')) {
								sel.val(sel.data('requested'));
								sel.data('requested',false);
							}
							sel.data('prev_value',sel.val());
							if ('afterBuild' in settings  && settings.afterBuild != null) {
								settings.afterBuild.bind(sel.parent())(sel,data);
							}
							if ($(document).tooltips) $(document).tooltips('applyTips');
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
 				sel.data('requested',false);
				$(sel).addClass("hrm_widget_energySelector"); 					
 				$elem.append(sel);
 				var myThis = this;
				sel.change( function(evt) {
					if ('onChange' in settings && settings.onChange != null) {
						var typeName = unescape($(evt.target).val());
						if ( settings.onChange.bind($(myThis))(evt, typeName) ) {
							sel.data('prev_value',sel.val());
						}
						else {
							$elem.energySelector('revert');
						}
					}
					else {
						sel.data('prev_value',sel.val());						
					}
				});
				$elem.energySelector('rebuild');
 			});
 		}
 		
 		else if (settings['widget']=='typeSelector') {
			$.fn.typeSelector = function( arg, arg2 ) {
				var sel = this.first().find("select");
 				var myThis = this;
				if (arg=='selValue') {
					return unescape(sel.val());
				}
				else if (arg=='set') {
					sel.val(arg2.htmlEscape());
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
						typestring: selected,
						allowblank: (!!settings.canBeBlank)
					})
					.done(function(data) {
						if (data.success) {
	    					sel.html(data['menustr']);
							sel.data('prev_value',sel.val());
	    					if ('afterBuild' in settings  && settings.afterBuild != null) {
	    						settings.afterBuild.bind(sel.parent())(sel,data);
	    					}
	    					if ($(document).tooltips) $(document).tooltips('applyTips');							
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
 				var invTpStr = null;
 				if (settings.invtype) {
 					if (settings.invtype instanceof Function) {
 						$(sel).addClass("hrm_widget_typeSelector_"+settings.invtype.bind($(sel))(sel));
 					}
 					else {
 	 					$(sel).addClass("hrm_widget_typeSelector_"+settings.invtype);
 					}
 				}
 				else {
 					$(sel).addClass("hrm_widget_typeSelector"); 					
 				}
 				var myThis = this;
				sel.change( function(evt) {
					if ('onChange' in settings && settings.onChange != null) {
						var typeName = unescape($(evt.target).val());
						if ( settings.onChange.bind($(myThis))(evt, typeName) ) {
							sel.data('prev_value',sel.val());
						}
						else {
							$elem.typeSelector('revert');
						}
					}
					else {
						sel.data('prev_value',sel.val());						
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
    					if ($(document).tooltips) $(document).tooltips('applyTips');
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
				$(sel).addClass("hrm_widget_routeTypeSelector"); 					
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
					else {
						sel.data('prev_value',sel.val());						
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
 				var days = ['S','M','T','W','T','F','S'];
 				var daysLong = ['{{_("Sunday")}}',
 				                '{{_("Monday")}}',
 				                '{{_("Tuesday")}}',
 				                '{{_("Wednesday")}}',
 				                '{{_("Thursday")}}',
 				                '{{_("Friday")}}',
 				                '{{_("Saturday")}}'];
 				var months = ['J','F','M','A','M','J','J','A','S','O','N','D']
 				var monthsLong = ['{{_("January")}}',
 				                  '{{_("February")}}',
 				                  '{{_("March")}}',
 				                  '{{_("April")}}',
 				                  '{{_("May")}}',
 				                  '{{_("June")}}',
 				                  '{{_("July")}}',
 				                  '{{_("August")}}',
 				                  '{{_("September")}}',
 				                  '{{_("October")}}',
 				                  '{{_("November")}}',
 				                  '{{_("December")}}'
 				                  ];
 				                  
 				
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
 					$td.append("<span title='"+daysLong[i]+"' style'pointer:none;'>"+days[i]+"</span>");
 					$('<input />', { type: 'checkbox', id: divId+'_0_'+i}).appendTo( $td );
 					$td.appendTo($row);
 				}
				$row.appendTo($tbl);
 				var $row = $('<tr />').html('<td style="text-align:right;">'+l1+'</td>');
 				$row.addClass('hrm_boxcalendar');
 				for (var i = 0; i<4; i++) {
 					var $td = $('<td />');
 					$td.addClass('hrm_boxcalendar');
 					$td.append("<span title='Week "+(i+1)+"' style'pointer:none;'>W"+(i+1)+"</span>");
 					$('<input />', { type: 'checkbox', id: divId+'_1_'+i}).appendTo( $td );
 					$td.appendTo($row);
 				}
				$row.appendTo($tbl);
 				var $row = $('<tr />').html('<td style="text-align:right;">'+l2+'</td>');
 				$row.addClass('hrm_boxcalendar');
 				for (var i = 0; i<12; i++) {
 					var $td = $('<td />');
 					$td.addClass('hrm_boxcalendar');
 					$td.append("<span title='"+monthsLong[i]+"' style'pointer:none;'>"+months[i]+"</span>");
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
				if ($(document).tooltips) $(document).tooltips('applyTips');
 			});
 		}
 		else if (settings['widget']=='floatTextBox') {
			$.fn.floatTextBox = function( arg, arg2 ) {
	 			var tId = this.attr('id');
 				if (tId == undefined) $.error('text input has no id');
	 			var tp = this.attr('type');
	 			if (tp != 'text') $.error('element is not a text input');
 				if (arg=='saveState') {
 					this.data('prev_value',this.val());
 				}
 				else if (arg=='revertState') {
 					this.val(this.data('prev_value'));
 				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				$elem = $(elem);
	 			var tId = $elem.attr('id');
 				if (tId == undefined) $.error('text input has no id');
	 			var tp = $elem.attr('type');
	 			if (tp != 'text') $.error('element is not a text input');
	 			$elem.keypress(validateFloat);
	 			$elem.floatTextBox('saveState');
	 			$elem.off('blur.floatTextBox');
 				$elem.on('blur.floatTextBox', function(evt) {
					if ('onBlur' in settings && settings.onBlur != null) {
						settings.onBlur.bind($elem)($elem);
					}
 				});

    			if ('afterBuild' in settings && settings.afterBuild != null) {
    				settings.afterBuild.bind($elem)($elem);
    			};
				if ($(document).tooltips) $(document).tooltips('applyTips');
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

			$(document).tooltip({show:{effect:"slideDown", duration:70, delay:800},
								hide:{effect:"slideUp", duration:70, delay:200}});

 			return this.first().each(function(index,elem) {
 				$(elem).tooltips('applyTips');
 			});
 		}
 		else if (settings['widget']=='stdDoneButton') {
 			$('#wrappage_done_row').show();
 			$('#wrappage_done_button').button()
 			.click( function() {
 				window.location = settings['doneURL'];
 			});

 			return this.first().each(function(index,elem) {
 				// Nothing to do
 			});
 		}
 		else if (settings['widget']=='stdCancelSaveButtons') {
 			$('#wrappage_cancelsave_row').show();
 			$('#wrappage_cancel_button').button()
 			.click( function() {
 				window.location = settings['doneURL'];
 			});
 			$('#wrappage_save_button').button()
 			.click( function() {
 				var dest = settings['doneURL'];
 				$.when( settings['getParms']() )
 				.then( function(parmDict) {
 					return ($.when( settings['checkParms'](parmDict) )
 							.then( function(chkData) {
 								if (chkData.success && (chkData.value == undefined || chkData.value)) {
 									if (chkData.goto) dest = chkData.goto;
 									return parmDict; 	 							
 								}
 								else return $.Deferred().reject(chkData);
 							}).promise());
 				})
 				.then( 
 					function(parmDict) {
 						window.location= dest;
 					},
 					function(chkData) {
						var $dlg = $('#wrappage_dialog_modal');
 						if (! $dlg.hasClass('ui-dialog')) {
 							$dlg.dialog({
 								resizable: false,
 								modal: true,
 								autoOpen:false,
 									buttons: {
 									OK: function() {
 										$( this ).dialog( "close" );
 									}
 								}
 							});
 						}
 						if (chkData.msg)
 							$("#wrappage_dialog_modal").text(chkData.msg);
 						else if (chkData.responseText)  // it is really a jqxhdr
 							$("#wrappage_dialog_modal").text(chkData.responseText);
 						else
 							$("#wrappage_dialog_modal").text('{{_("An error occurred")}}');
 						if (chkData.title) {
 	 						$("#wrappage_dialog_modal").dialog('option','title',chkData.title); 							
 						}
 						$("#wrappage_dialog_modal").dialog("open");
 					}
 				);
 			});

 			return this.first().each(function(index,elem) {
 				// Nothing to do
 			});
 		}
 		else if (settings['widget']=='stdBackNextButtons') {
 			$('#wrappage_backnext_row').show();
 			$('#wrappage_back_button').button()
 			.click( function() {
 				window.location = settings['backURL'];
 			});
 			$('#wrappage_next_button').button()
 			.click( function() {
 				$.when( settings['getParms']() )
 				.then( function(parmDict) {
 					return ($.when( settings['checkParms'](parmDict) )
 							.then( function(chkData) {
 								if (chkData.success && (chkData.value == undefined || chkData.value)) {
 									return parmDict;
 								}
 								else return $.Deferred().reject(chkData);
 							}).promise());
 				})
 				.then( 
 					function(parmDict) {
 						window.location= settings['nextURL'] + '?' + $.param(parmDict);
 					},
 					function(chkData) {
						var $dlg = $('#wrappage_dialog_modal');
 						if (! $dlg.hasClass('ui-dialog')) {
 							$dlg.dialog({
 								resizable: false,
 								modal: true,
 								autoOpen:false,
 									buttons: {
 									OK: function() {
 										$( this ).dialog( "close" );
 									}
 								}
 							});
 						}
 						if (chkData.msg)
 							$("#wrappage_dialog_modal").text(chkData.msg);
 						else if (chkData.responseText)  // it is really a jqxhdr
 							$("#wrappage_dialog_modal").text(chkData.responseText);
 						else
 							$("#wrappage_dialog_modal").text('{{_("An error occurred")}}');
 						if (chkData.title) {
 	 						$("#wrappage_dialog_modal").dialog('option','title',chkData.title); 							
 						}
 						$("#wrappage_dialog_modal").dialog("open");
 					}
 				);
 			});

 			return this.first().each(function(index,elem) {
 				// Nothing to do
 			});
 		}
 		else if (settings['widget']=='editFormManager') {
			$.fn.editFormManager = function( arg, arg2 ) {
 				if (arg=='getEntries') {
 					var dict = {modelId:settings.modelId}
 					$(this).find('input,select').each( function( index ) {
 						var tj = $(this);
 						if (tj.hasClass('hrm_price')) {
 							dict[tj.attr('id')] = tj.val().unformatMoney()
 						}
 						else if (tj.is(':checkbox')) {
 							dict[tj.attr('id')] = tj.is(':checked')
 						}
 						else if (tj.is('select')) {
 	 						dict[tj.attr('id')] = tj.val(); 							
 						}
 						else {
 	 						dict[tj.attr('id')] = tj.val();
 						}
 					});
 					$(this).find('.hrm_currency').each(function() {
 						var tj = $(this);
 						dict[tj.attr('id')] = tj.currencySelector('selId');
 					})
 					$(this).find('.hrm_energy').each(function() {
 						var tj = $(this);
 						dict[tj.attr('id')] = tj.energySelector('selId');
 					})
 					$(this).find('.hrm_fuel').each(function() {
 						var tj = $(this);
 						dict[tj.attr('id')] = tj.energySelector('selId');
 					})
 					return dict;
 				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				$elem = $(elem);
 				$elem.html(settings.html);
 				$(document).ready( function() {
 	 				$elem.find('.hrm_currency').each( function(idx) {
 	 					$field = $(this);
 	 					var sel = $field.text();
 	 					$field.text('');
 	 					$field.hrmWidget({
 	 						widget:'currencySelector',
 	 						modelId:settings.modelId,
 	 						label:'',
 	 						selected:sel
 	 					})
 	 				});
 	 				$elem.find('.hrm_energy').each( function(idx) {
 	 					$field = $(this);
 	 					var sel = $field.text();
 	 					$field.text('');
 	 					$field.hrmWidget({
 	 						widget:'energySelector',
 	 						label:'',
 	 						selected:sel
 	 					})
 	 				});
 	 				$elem.find('.hrm_fuel').each( function(idx) {
 	 					$field = $(this);
 	 					var sel = $field.text();
 	 					$field.text('');
 	 					$field.hrmWidget({
 	 						widget:'energySelector',
 	 						label:'',
 	 						selected:sel,
 	 						OptionURL:'{{rootPath}}list/select-fuel'
 	 					})
 	 				});
 	 				$elem.find('.hrm_price').each( function(idx) {
 	 					$field = $(this);
 	 					$field.val( parseFloat($field.val()).formatMoney(2) );
 	 				})
 	 				$elem.change( function( eventObj ) {
 	 					var elem = $(eventObj.target);
 	 					if (elem.is('select')) {
 	 						var opt = elem.children(":selected");
 	 						if (opt.attr("data-enable")) {
 	 	 						var enableIdList = opt.attr("data-enable").split(",");
 	 	 						for (i in enableIdList) { 
 	 	 							var id = enableIdList[i];
 	 	 							$("#"+id).show(); 
 	 	 						}; 	 							
 	 						}
 	 						if (opt.attr("data-disable")) {
 	 	 						var disableIdList = opt.attr("data-disable").split(",");
 	 	 						for (i in disableIdList) { 
 	 	 							var id = disableIdList[i];
 	 	 							$("#"+id).hide(); 
 	 	 						};
 	 						}
 	 					}
 	 				});
	    			if ('afterBuild' in settings && settings.afterBuild != null) {
	 	    			settings.afterBuild.bind($elem)($elem);
	 	    		};
					if ($(document).tooltips) $(document).tooltips('applyTips');
 				})

 			});
 			
 		}
 		else if (settings['widget']=='openbuttontriple') {
 			$.fn.buttontriple = function( arg, arg2, arg3 ) {
				if (arg=='set') {
					var $btn = this.find('.'+this.data('map')[arg2]);
					$btn.unbind('click');
					$btn.click(arg3);
					if (arg3) $btn.attr('disabled',false);
					else $btn.attr('disabled',true);
				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
 			}

			return this.each(function(index,elem) {
				$elem = $(elem);
				var divId = $elem.attr('id');
				if (divId == undefined) $.error('wrapper div has no id');
				//buttonList now takes optional 4th parameter: JSON call which, when passed a modelId, provides a true/false value to enable/disable the button
				buttonList = [
				              ['{{_("Open")}}', 'hermes_edit_button', 'onOpen'],
				              ['{{_("Run")}}', 'hermes_run_button', 'onRun'],
				              ['{{_("Results")}}', 'hermes_results_button', 'onResults','json/get-results-avail'],
				              ['{{_("Copy")}}', 'hermes_copy_button', 'onCopy'],
				              ['{{_("Info")}}', 'hermes_info_button', 'onInfo'],
				              ['{{_("Del")}}', 'hermes_del_button', 'onDel']
				              ];
				var map = {}
				for (x in buttonList) {
					var lbl = buttonList[x][0];
					var cl = buttonList[x][1];
					var cbName = buttonList[x][2];
					map[cbName] = cl;
					$elem.append("<button type=\"button\" class=\""+cl+"\"> "+lbl+" </button>");
					if (settings[cbName])
						$elem.find("."+cl).click(settings[cbName]);
					else
						$elem.find("."+cl).prop("disabled",true);
                    $elem.find("."+cl).button();    //neccessary until models_top.tpl jqGrid calls hermify
                    var modelId = divId;                   
                    if(typeof buttonList[x][3] != 'undefined') {
                        var enabledOn = buttonList[x][3];
                        var cl_ = cl;   //necessary because otherwise in .done section below .getJSON, cl is set to next iterarated button's cl
                        var x_ = x;
                        $.getJSON('{{rootPath}}'+buttonList[x][3],{modelId:modelId})
                        .done(function(data) {
                            if (data.success) {
                                if (data.data) {
                                    $("div#" + divId + ".hermes_button_triple ." + cl_).removeAttr("disabled");
                                } else {
                                    $("div#" + divId + ".hermes_button_triple ." + cl_).attr("disabled","disabled"); 
                                    $("div#" + divId + ".hermes_button_triple ." + cl_).addClass("ui-button-disabled");
                                    $("div#" + divId + ".hermes_button_triple ." + cl_).addClass("ui-state-disabled");
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
				}
				$elem.data('map',map);
				if ($(document).tooltips) $(document).tooltips('applyTips');
			});
		}
 		else if (settings['widget']=='buttontriple') {
			$.fn.buttontriple = function( arg, arg2, arg3 ) {
 				if (arg=='set') {
 					var $btn = this.find('.'+this.data('map')[arg2]);
 					$btn.button();
 					$btn.unbind('click');
 					$btn.click(arg3);
 					if (arg3) $btn.attr('disabled',false);
 					else $btn.attr('disabled',true);
 				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {
 				$elem = $(elem);
 				var divId = $elem.attr('id');
 				if (divId == undefined) $.error('wrapper div has no id');
 				buttonList = [
 				              ['{{_("Edit")}}', 'hermes_edit_button', 'onEdit'],
 				              ['{{_("Info")}}', 'hermes_info_button', 'onInfo'],
 				              ['{{_("Del")}}', 'hermes_del_button', 'onDel']
 				              ];
 				var map = {}
 				for (x in buttonList) {
 					var lbl = buttonList[x][0];
 					var cl = buttonList[x][1];
 					var cbName = buttonList[x][2];
 					map[cbName] = cl;
 					$elem.append("<button type=\"button\" class=\""+cl+"\"> "+lbl+" </button>");
 					if (settings[cbName])
 						$elem.find("."+cl).click(settings[cbName]);
 					else
 						$elem.find("."+cl).prop("disabled",true);
                    $elem.find("."+cl).button();
 				}
 				$elem.data('map',map);
				if ($(document).tooltips) $(document).tooltips('applyTips');
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

