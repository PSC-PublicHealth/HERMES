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
 		else if (settings['widget']=='currencySelector') {
 			$.fn.currencySelector = function( arg ) {
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
 						$elem.currencySelector('save');
 					}
 				});
 				$elem.currencySelector('rebuild');
 			});
 		}

 		else if (settings['widget']=='currencySelector2') {
			$.fn.currencySelector = function( arg ) {
 				var myThis = this;
 				var $ul = this.first().find("ul");
 				/*
				var sel = this.first().find("select");
				*/
				if (arg=='selId') {
					return $ul.data('code');
				}
				else if (arg=='rebuild') {
					var modelId;
					if (settings.modelId instanceof Function) {
						modelId = settings.modelId.bind($(myThis))($ul);
					}
					else {
						modelId = settings.modelId;
					}
					var selected = '';
					if (settings.selected) {
						if (settings.selected instanceof Function) {
							selected = settings.selected.bind($(myThis))($ul);
						}
						else selected = settings.selected;
					}
				
					$.getJSON('{{rootPath}}list/select-currency', { 
						modelId: modelId,
						idstring: encodeURIComponent(selected)
					})
					.done(function(data) {
						if (data.success) {
							/*
							$ul = $(document.createElement('ul'));
							$ul.addClass('hrm_cur_select');
							*/
			    			for (var i = 0; i < data.pairs.length; i++) {
			    				var curCode = decodeURIComponent(data.pairs[i][1]);
			    				var curStr = decodeURIComponent(data.pairs[i][0]);
			    				$li = $(document.createElement('li'))
			    				.data('code',curCode)
			    				.data('str',curStr)
				    			.text(curStr)
				    			.addClass('ui-front')
			    				.click( function() {
			    					var outerThis = this;
			    					if ($ul.hasClass('hrm_cur_select_open')) {
			    						$ul.removeClass('hrm_cur_select_open');
			    					}
			    					else {
			    						$ul.addClass('hrm_cur_select_open');			    						
			    					}
			    					$(this).parent().find('li').each( function(ind,elt) {
			    						if (outerThis == elt) {
			    							$(elt).addClass('selected');
			    							if ($ul.hasClass('hrm_cur_select_open')) {
			    								$(elt).text( $(elt).data('str'));
			    							}
			    							else {
			    								$(elt).text( $(elt).data('code'));
			    							}
			    						}
			    						else {
			    							$(elt).removeClass('selected');
			    						}
			    					});
			    				});
			    				if (curCode == data.selid) {
			    					$li.addClass('selected')
				    				.text(curCode);
			    				}
			    				$ul.append($li);
								$ul.data('prev_value',data.selid);
			    			}
							//$(".cur_sel").append($ul);
							
							/*
							sel.html(decodeURIComponent(data['menustr']));
							sel.data('prev_value',sel.val());
							*/
    						if ('afterBuild' in settings  && settings.afterBuild != null) {
    							settings.afterBuild.bind($ul.parent())($ul,data);
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
					/*
					sel.data('prev_value', sel.val());
					*/
					$ul.data('prev_value', sel.val());
				}
				else if (arg=='revert') {
					/*
					sel.val(sel.data('prev_value'));
					*/
					$ul.val(sel.data('prev_value'));

				}
				else {
					$.error('Unknown operation '+arg.toString());
				}
			}

 			return this.each(function(index,elem) {

 				var $elem = $(elem);
 				$elem.html('<label>'+settings['label']+'</label>');
 				/*
 				var sel = $(document.createElement("select"));
 				*/
				var $ul = $(document.createElement('ul'));
				$ul.addClass('hrm_cur_select');
				/*
 				$elem.append(sel);
 				*/
 				$elem.append($ul);
 				console.log($elem);
 				var myThis = this;
 				/*
				sel.change( function(evt) {
				*/
				$ul.change( function(evt) {
					if ('onChange' in settings && settings.onChange != null) {
						settings.onChange.bind($(myThis))(evt, $(evt.target).val());
					}
					else {
						$elem.currencySelector('save');
					}
				});
				$elem.currencySelector('rebuild');
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

