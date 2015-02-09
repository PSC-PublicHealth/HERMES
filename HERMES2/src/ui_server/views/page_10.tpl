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
<div id='tabs-10'>

<body>
<style>
.ui-menu { width: 100px; }
</style>


<h2>{{_('Pop-up Menu Tests')}}</h2>

<table>
  <tr>
  	<td><label>Plan A</label></td>
  	<td>

<ul id="menup10" class="menu">
  <li><a href="#">Click Me</a>
    <ul class="submenu">
	  <li><a href='#'>Item 1</a></li>
	  <li><a href='#'>Item 2</a></li>
	  <li><a href='#'>Item 3</a></li>
    </ul>
  </li>
</ul>

  	</td>
  </tr>

  <tr>
  	<td><label>Plan B</label></td>
  	<td>
		<button id="testbutton">{{_('Do it!')}}</button>
  	</td>
  </tr>

  <tr>
  	<td><label>jQuery contextMenu plug-in</label></td>
  	<td>
		<button id="testdiv1" class="context-menu-class">{{_('Do it!')}}</button>
		<div id="testdiv2" class="context-menu-class">{{_('Do it!')}}</div>
  	</td>
        <td>
                <button type="button" id="add-trigger">add new trigger</button>
        </td> 
  </tr>

</table>


<div id='test_menu_dlg_div'>
<ul id="menup10b" class="menu">
  <li><a href='#'>Item 1</a></li>
  <li><a href='#'>Item 2</a></li>
  <li><a href='#'>Item 3</a></li>
</ul>
</div>


<script>
$(function() {
  $('#menup10').menu();
});


$(function() {
	$('#menup10b').menu( {
		click: function() {alert('click');}
	});
	var dlgHome = $('#test_menu_dlg_div');
	var btn = $("#testbutton");
	dlgHome.dialog({
		autoOpen: false,
		dialogClass: 'noTitleStuff',
		closeOnEscape: true,
		height: "auto",
		minHeight: 50,
		minWidth: 50,
		width: "auto",
		title:"Edit",
		modal:true,
		draggable:false,
		position: { my: "left top", at: "left bottom", of: btn },
		// open: function(event,ui) { $(this).siblings('.ui-dialog').find('.ui-dialog-content').dialog('close'); }
		open: function(event,ui) { $('.ui-widget-overlay').bind('click', function () { $(this).siblings('.ui-dialog').find('.ui-dialog-content').dialog('close'); })}
	});

	btn.button();
	btn.click( function() {
		dlgHome.dialog("open");
	});
});

$(function(){
    // add new trigger
    $('#add-trigger').on('click', function(e) {
        //$('<button class="context-menu-class box menu-injected">'
        $('<button id="bleh" class="context-menu-class">'
            + 'click me <em>(injected)</em>'
            + '</button>').insertBefore(this);

        // not need for re-initializing $.contextMenu here :)
    });
   
    $.contextMenu({
        selector: '.context-menu-class', 
        trigger: 'left',
        callback: function(key, options) {
        
            var m = "clicked: " + key;
            var id = options.$trigger.attr("id");
            m += ", element: " + id;
            alert(m); 
        },
        items: {
            "edit": {name: "Edit", icon: "edit"},
            "cut": {name: "Cut", icon: "cut"},
            "copy": {name: "Copy", icon: "copy"},
            "paste": {name: "Paste", icon: "paste"},
            "delete": {name: "Delete", icon: "delete"},
            "sep1": "---------",
            "quit": {name: "Quit", icon: "quit"}
        }
    });
    
    $('.context-menu-one').on('click', function(e){
        console.log('clicked', this);
    })
});

</script>

</body>

</div>