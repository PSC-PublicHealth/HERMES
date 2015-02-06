<!DOCTYPE html>
<html>
<head>
	<meta charset="utf-8">
    <title>{{_('HERMES - Supply Chain Modeling for Public Health')}}</title>

<link rel="shortcut icon" type="image/x-icon" href="{{rootPath}}static/icons/favicon2.ico">
<link rel="stylesheet" href="{{rootPath}}static/jquery-ui-1.10.2/themes/base/jquery-ui.css" />

<link rel="stylesheet" href="{{rootPath}}static/jquery-ui-1.10.2/themes/base/jquery.ui.all.css" />
<link rel="stylesheet" href="{{rootPath}}static/jquery-ui-1.10.2/demos/demos.css" />
<link rel="stylesheet" href="{{rootPath}}static/animate.css"/>
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
<script type="text/javascript" src="{{rootPath}}static/hermes-ui-utils.js"></script>
<script src="{{rootPath}}static/jquery.corner.js"></script>

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

<script src="{{rootPath}}hrmwidgets.js" type="text/javascript"></script>

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

$.extend($.ui.dialog.prototype.options, { autoOpen: false, show: {effect: 'fade', duration: 250}, hide: {effect: 'fade', duration: 150} });  //set dialogs to fade in and out

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
%if defined('pagehelptag'):
		console.log("1 = {{pagehelptag}}");
		$.getJSON("{{rootPath}}json/page-help",{url:"None",tag:"{{pagehelptag}}"})
%else:
		$.getJSON("{{rootPath}}json/page-help",{url:window.location.href,tag:"None"})
%end
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
	var regex = /[^/:-~]/;
	if( !regex.test(key) ) {
		if (theEvent.preventDefault) theEvent.preventDefault();
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
			<div class="art-shapes">
				<div style="float:left">
	     			<h1 class="art-headline">
						HERMES
					</h1>
	     			<h2 class="art-slogan">
						{{get('title_slogan','Slogan is undefined')}}
					</h2>
				</div>
				<div style="float:right;margin-right:15px">
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
	    			<li><a href="{{rootPath}}top?createnew=1&crmb=clear">{{_('Create')}}</a></li>
	    			<li><a href="{{rootPath}}models-top?crmb=clear">{{_('Models')}}</a></li>	    			
	    			<li><a href="{{rootPath}}results-top?crmb=clear">{{_('Results')}}</a></li>
	    			<li><a href="{{rootPath}}vaccines-top?crmb=clear">{{_('Database')}}</a></li>
	    			<li><a href="{{rootPath}}run-top?crmb=clear">{{_('Run Status')}}</a></li>
	    			<li><a href="{{rootPath}}show-help">{{_('Help')}}</a></li>
	    			<script>
	    			check_developer_mode('{{rootPath}}').done(function(result){
	    				if(result.mode){
	    					//$('.art-hmenu').append("<li><a href='{{rootPath}}run-top?crmb=clear'>{{_('Run Hermes')}}</a></li>");
	    					$('.art-hmenu').append("<li><a href='{{rootPath}}cost-top?crmb=clear'>{{_('Costs')}}</a></li>");
		    				$('.art-hmenu').append("<li><a href='{{rootPath}}people-top?crmb=clear'>{{_('People')}}</a></li>");
		    				$('.art-hmenu').append("<li><a href='{{rootPath}}vaccines-top?crmb=clear'>{{_('Vaccines')}}</a></li>");
		    				$('.art-hmenu').append("<li><a href='{{rootPath}}fridge-top?crmb=clear'>{{_('ColdStorage')}}</a></li>");
		    				$('.art-hmenu').append("<li><a href='{{rootPath}}truck-top?crmb=clear'>{{_('Transport')}}</a></li>");
		    				$('.art-hmenu').append("<li><a href='{{rootPath}}demand-top?crmb=clear'>{{_('Demand')}}</a></li>");
		    				$('.art-hmenu').append("<li><a href='{{rootPath}}tabs'>{{_('Developer')}}</a></li>");
	    				}
	    			});
	    			</script>
	    			
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
		     								

												<div id="wrappage_help_dialog" title="Quick Help" class="hrm_quickhelp">
												<p>{{_("This text will be replaced.")}}
												</div>


												<table style="width:100%;border-style=none" >
												<tr>
													<td>
														<div class="rcrumbs" id="models_top_breadcrumbs">
															% if defined('breadcrumbPairs'):
																% if isinstance(breadcrumbPairs,type([])):
																	% raise RuntimeError('Bare tuples for breadcrumbs are no longer supported')
																% else:
																	{{! breadcrumbPairs.render() }}
																% end
															% else:
															<ul></ul>
															% end
														</div>
													</td>
													<td width=10% align='right'>
														<div id="ajax_busy">
														  <img id="ajax_busy_blank" src="{{rootPath}}static/icons/ajax-loader-blank.png" width='32' height='32' />
														  <img id="ajax_busy_image" src="{{rootPath}}static/icons/ajax-loader.gif" width='32' height='32' />
														</div>
													</td>
													<td width=10% style="text-align:right">
														<input type="image" id="wrappage_help_button" src="{{rootPath}}static/icons/helpicon.bmp">
													</td>
												</tr>
											</table>

% if defined('topCaption'):
<h1>{{topCaption}}</h1>
% end

%include

<table width=100%>
<tr id='wrappage_backnext_row' style='display:none'>
<td width 10%><input type="button" id="wrappage_back_button" value='{{_("Previous Screen")}}'></td>
<td></td>
<td width=10%><input type="button" id="wrappage_bn_misc_button" value='{{_("Advanced")}}' style='display:none'></td>
<td width=10%><input type="button" id="wrappage_next_button" value='{{_("Next Screen")}}'></td>
</tr>
<tr id='wrappage_done_row' style='display:none'>
<td></td>
<td width=10%><input type="button" id="wrappage_done_button" value='{{_("Done")}}'></td>
</tr>
<tr id='wrappage_cancelsave_row' style='display:none'>
<td></td>
<td width=10%><input type="button" id="wrappage_cs_misc_button" value='{{_("Advanced")}}' style='display:none'></td>
<td width=10%><input type="button" id="wrappage_cancel_button" value='{{_("Cancel")}}'></td>
<td width=10%><input type="button" id="wrappage_save_button" value='{{_("Save")}}'></td>
</tr>
</table>
<div id="wrappage_dialog_modal" title='{{_("Invalid Entry")}}'></div>



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
	  			&nbsp; &nbsp; &nbsp; &nbsp;{{_('HERMES Project')}} - Copyright &copy; 2015. {{_('All Rights Reserved.')}}
			</div>
		</footer> 
    </div>    
</body>
