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
<div id="tabs-debug">

<h2>Some Server-Side Info</h2>
<div id="hereDebugUI"></div>
<!-- <iframe id="myframe"></iframe> -->

<table>
<tr>
<td><button id="becomesystembutton">{{_('Become System')}}</button>
</td><td><button id="becomeanyuserbutton">{{_('Become Anyuser')}}</button>
</td><td><button id="clearsessionbutton">{{_('Clear Server-side Session')}}</button>
</td><td><button id="clearnotesbutton">{{_('Clear Session Notes')}}</button>
</td><td><button id="clearfsbutton">{{_('Clear FS Metadata')}}</button>
</td><td><button id="cleanresultsgroup">{{_('Clean resultsGroup table')}}</button>
</td><td><button id="toggledevelbutton">{{_('Toggle Developer Mode')}}</button>
</td><td><button id="delfromsessionbutton">{{_('Delete Element From Session')}}</button>
<td>
</tr>
</table>

<div id="dfsb_div">
<label>Delete what key?</label>
<input type=text id='dfsb_key_text'></input>
</div>

</div>

<script>

var drawTable = function() {
    $.getJSON('json/show-dict', {})
	    .done(function(json) {
  		    var st = JSON.stringify(json, null, 4);
  		    $('#hereDebugUI').empty().append('<pre>'+st+'</pre>');
  		    })
  	    .fail(function(jqxhr, textStatus, error) {
  		    alert(jqxhr.responseText);
  		    // To put the text in the iframe:
  		    //$('#myframe').attr({border:'1', srcdoc:jqxhr.responseText});
		    });
    }

$(function() {
	var btn = $("#clearsessionbutton");
	btn.button();
	btn.click( function() {
	    $.getJSON('json/clear-session-data',{})
        .done(function(json) { console.log('Session data cleared'); })
        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
        .always(function(data) { drawTable(); });
	});
	var btn2 = $("#clearnotesbutton");
	btn2.button();
	btn2.click( function() {
	    $.getJSON("json/clear-notes-data",{})
	        .done(function(json) { console.log("notes data cleared"); })
	        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
	        .always(function(data) { drawTable(); });
	});
	var btn3 = $("#becomesystembutton");
	btn3.button();
	btn3.click( function() {
	    $.getJSON("json/become-system",{})
	        .done(function(json) { alert('You should now be the system user') })
	        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
	        .always(function(data) { drawTable(); });
	});
	var btn4 = $("#becomeanyuserbutton");
	btn4.button();
	btn4.click( function() {
	    $.getJSON("json/become-anyone",{})
	        .done(function(json) { alert('You should now be the generic user') })
	        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
	        .always(function(data) { drawTable(); });
	});
	var btn5 = $("#clearfsbutton");
	btn5.button();
	btn5.click( function() {
	    $.getJSON("json/clear-fs-metadata",{})
	        .done(function(json) { console.log("fs metadata cleared"); })
	        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
	        .always(function(data) { drawTable(); });
	});
	var btn6 = $("#cleanresultsgroup");
	btn6.button();
	btn6.click( function() {
	    $.getJSON("json/clean-resultsgroup-table",{})
	        .done(function(data) {
	        	if (data.success) {
	        		alert("resultsGroup table cleaned; "+data.value);	        		
	        	}
	        	else {
        			alert('{{_("Failed: ")}}'+data.msg);	        		
	        	}
	        })
	        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
	        .always(function(data) { drawTable(); });
	});
	var btn7 = $("#toggledevelbutton");
	btn7.button();
	btn7.click( function() {
	    $.getJSON("json/toggle-devel-mode",{})
	        .done(function(json) { console.log("developer mode toggled"); })
	        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
	        .always(function(data) { drawTable(); });
	});
	$('#dfsb_div').dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			'{{_("Cancel")}}': function() {
				$( this ).dialog( "close" );
        	},
        	'{{_("OK")}}': function() {
        		$( this ).dialog( "close" );
        		$.getJSON("json/delete-from-session",{name:$('#dfsb_key_text').val()})
    	        .done(function(data) { 
    	        	if (data.success) alert('done!')
    	        	else alert(data.msg);
    	        })
    	        .fail(function(jqxhdr,textStatus,error) { alert(jqxhdr.responseText); })
    	        .always(function(data) { drawTable(); });
        	}
        }		
	});
	var btn8 = $("#delfromsessionbutton").button()
		.click(function(){ $('#dfsb_div').dialog('open') });
	drawTable();	
  });



</script>
