<!---
-->
<div id='tabs-6'>

<body>	
<h2>{{_('This is for little tests')}}</h2>
<button id="testbutton">{{_('Do it!')}}</button>
<script>
$(function () {
	var btn = $("#testbutton");
	btn.button();
	btn.click( function() {
		$.getJSON("json/test-button")
		.done(function(data) {
			if (data.success) {
				alert('success');
			}
			else {
				alert('Error: '+data.msg)
			}
		})
		.fail(function(jqxhdr, textStatus, error) {
			alert(jqxhdr.responseText);
		});
	});
});
</script>

</body>

</div>
