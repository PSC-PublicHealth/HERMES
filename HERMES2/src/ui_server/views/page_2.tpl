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
<div id='tabs-2'>
<h2>{{_('Show A Menu')}}</h2>

{{_('This should show a menu.')}}

  <style>
  .ui-menu { width: 150px; }
  </style>
  
  <select id="menu" class="ui-menu">
  </select>
  
  <button id="mybutton">{{_('My Button')}}</button>

<script>
  $(function() {
  $.getJSON('json/show-menu')
	.done(function(data) {
		var sel = $("#menu");
		var s = "";
    	$.each(data.menu.content.menuitem, function() {
    		//s += "<li> <a href=" + this.href + " > " + this.text + " </a></li>";
    		s += "<option> " + this.text + " </option>";
    		})
		sel.append(s);
		//sel.change( function() { alert('select handler called'); } );
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert(jqxhr.responseText);
	});

	var btn = $("#mybutton");
	btn.button();
	btn.click( function() {
		alert('selected was ' + $("#menu").val());
	});

  });
  
 </script>
 </div>