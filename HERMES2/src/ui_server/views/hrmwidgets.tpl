// Thanks to Patrick Desjardins http://stackoverflow.com/questions/149055/how-can-i-format-numbers-as-money-in-javascript
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

// Add a method to jqGrid that will allow us to customize.
(function( $ ) {
	$.jgrid.extend({
		hermify: function(opts) {
    		this.each(function(){
            	if (!this.grid) { return; }

            	if (opts.debug) {
    				console.log('starting hermify with opts: ' + JSON.stringify(opts));
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
				if (opts.resizable) {
					function resize_grid() {
						var offset = $grid.offset() //position of grid on page
						//hardcoded minimum width
						if ( $(window).width() > 710 ) {
							$grid.jqGrid('setGridWidth', $(window).width()-offset.left-50);
						}
						$grid.jqGrid('setGridHeight', $(window).height()-offset.top-130);
					}
					$(window).load(resize_grid); //necessary to trigger resize_grid onload due to loading breadcrumbs changing grid offset
					$(window).resize(resize_grid);  //bind resize_grid to window resize
					resize_grid();
					if (opts.debug) console.log('resize handling set');
					
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
            callbackData: null,
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
			$.fn.currencySelector = function( arg, arg2 ) {
 				var myThis = this;
 				var $btn = this.find("button").first();
				if (arg=='selId') {
					if (! arg2) {
						console.log('returning '+$btn.data('code'));
						return $btn.data('code');
					}
					else {
						$btn.data('code',arg2);
						$btn.button('option','label',arg2);						
						return $btn.data('code');
					}
				}
				else if (arg=='rebuild') {
					var modelId;
					if (settings.modelId instanceof Function) {
						modelId = settings.modelId.bind($(myThis))($btn);
					}
					else {
						modelId = settings.modelId;
					}
					var selected='';
					if (settings.selected) {
						if (settings.selected instanceof Function)
							selected = settings.selected.bind($(myThis))($btn);
						else 
							selected = settings.selected;
					}
					var $dlgDiv = $('#hrm_cur_sel_dlg_div_shared');
					if ($dlgDiv.length == 0) {
						$dlgDiv = $(document.createElement('div'))
						.attr('id','hrm_cur_sel_dlg_div_shared');
		 				this.append($dlgDiv);
					}
		 			if (! $dlgDiv.hasClass('ui-dialog-content')) {
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
								}
							},
						});
						$.getJSON('{{rootPath}}list/select-currency', { 
							modelId: modelId,
							idstring: encodeURIComponent(selected)
						})
						.done(function(data) {
							if (data.success) {
								$dlgDiv.data('defaultSelection',decodeURIComponent(data.defaultid));
								$dlgDiv.html("");
								var $ul = $(document.createElement('ul'));
				    			for (var i = 0; i < data.pairs.length; i++) {
				    				var curCode = decodeURIComponent(data.pairs[i][1]);
				    				var curStr = decodeURIComponent(data.pairs[i][0]);
				    				var $li = $(document.createElement('li'))
				    				.data('code',curCode)
				    				.data('str',curStr);
				    				var $a = $(document.createElement('a'))
				    				.attr('href','#')
					    			.text(curCode + ' : ' + curStr);
				    				$li.append($a);
				    				$ul.append($li);
				    			}
				    			$ul.menu();
				    			$dlgDiv.append($ul);
			    				var selId = decodeURIComponent(data.selid);
				    			$('.hrm_cur_sel_btn').each(function() {
				    				if ( ! $(this).button('option','text') 
				    						|| $(this).button('option','label') == '') {
				    					$(this).button('option','label', selId)
				    					.button('option','text', true)
				    					.data('code',selId)
				    					.data('prev_value',selId);
				    				}
				    			});
							}
							else {
	  							alert('{{_("Failed: ")}}'+data.msg);
							}
	    				})
	  					.fail(function(jqxhr, textStatus, error) {
	  						alert("Error: "+jqxhr.responseText);
						});
					}
    				if ('afterBuild' in settings  && settings.afterBuild != null) {
    					settings.afterBuild.bind($btn.parent())($btn);
    				}
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
 				$elem.html('<label>'+settings['label']+'</label>');
				var $btn = $(document.createElement('button'));
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
 						label:selected
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
				$btn.click( function(evt) { 
					evt.preventDefault();
					
					var $b = $(evt.target).parent();
					var $dlgDiv = $('#hrm_cur_sel_dlg_div_shared');
    				
    				$dlgDiv.data('currentBtn',$b)
				    .find('a').each( function() {
				    	var $li = $(this).parent();
				    	$li.removeClass('selected');
				    	if ($li.data('code') == $b.data('code'))
				    		$li.addClass('selected');				    		
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
    					$btn.button('option','label', newCode)
    					.data('code',newCode);
    					$dlgDiv.dialog('close');
     					if ('onChange' in settings && settings.onChange != null) {
     						console.log('calling onChange handler');
     						settings.onChange.bind($btn.parent())(evt, newCode);
     					}
     					else {
     						$elem.currencySelector('save');
     					}
    				}); 
    				$dlgDiv.dialog('option', 'position',
    						{my:'left top', at:'left top', of:this}
    				)
    				.dialog('open'); 
    			})
    			.addClass('hrm_cur_sel_btn');
				
				if ($('#hrm_cur_sel_dlg_div_shared').length == 0
						|| ! $('#hrm_cur_sel_dlg_div_shared').hasClass('ui-dialog-content')) {
					$elem.currencySelector('rebuild');					
				}
				else {
    				if ('afterBuild' in settings  && settings.afterBuild != null) {
    					settings.afterBuild.bind($btn.parent())($btn);
    				}					
				}
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

			$(document).tooltip({show:{effect:"slideDown", duration:70, delay:1300},
								hide:{effect:"slideUp", duration:70, delay:200}});

 			return this.first().each(function(index,elem) {
 				$(elem).tooltips('applyTips');
 			});
 		}
 		else if (settings['widget']=='editFormManager') {
			$.fn.editFormManager = function( arg, arg2 ) {
 				if (arg=='getEntries') {
 					var dict = {modelId:settings.modelId}
 					$(this).find('input,select').each( function( index ) {
 						var tj = $(this);
 						dict[tj.attr('id')] = tj.val();
 						
 					});
 					$(this).find('.hrm_currency').each(function() {
 						var tj = $(this);
 						dict[tj.attr('id')] = tj.currencySelector('selId');
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
 	 				$elem.find('.hrm_price').each( function(idx) {
 	 					$field = $(this);
 	 					console.log($field.val());
 	 					$field.val( parseFloat($field.val()).formatMoney(2) );
 	 				})
 	 				$elem.change( function( eventObj ) {
 	 					var elem = $(eventObj.target);
 	 					if (elem.is('select')) {
 	 						var opt = elem.children(":selected");
 	 						var enableIdList = opt.attr("data-enable").split(",");
 	 						var disableIdList = opt.attr("data-disable").split(",");
 	 						for (i in enableIdList) { 
 	 							var id = enableIdList[i];
 	 							$("#"+id).show(); 
 	 						};
 	 						for (i in disableIdList) { 
 	 							var id = disableIdList[i];
 	 							$("#"+id).hide(); 
 	 						};
 	 					}
 	 				});
	    			if ('afterBuild' in settings && settings.afterBuild != null) {
	 	    				settings.afterBuild.bind($elem)($elem);
	 	    			};
 				})

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

