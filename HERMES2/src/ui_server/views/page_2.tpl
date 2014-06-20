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