<!---
-->

<div id='tabs-5'>

<body>	
<h2>{{_('This is a file uploader')}}</h2>
Drag-and-drop works; paste not so much.
<br>

<input id="fileupload" type="file" name="files[]" data-url="{{rootPath}}upload" multiple>
<div id="progress">
    <div class="bar" style="width: 0%;"></div>
</div>

<script>
$(function () {
	/*
	* This code block prevents the browser from handling drag-and-drop events
	* for the page, which allows the uploader's drag-and-drop behavior to
	* operate.  If it's activated, though, preventDefaultFunc will need to
	* get unbound when this tab is popped down.
	*/
	//var preventDefaultFunc = function (e) {
    //	e.preventDefault();
	//}
	//$(document).bind('drop dragover', preventDefaultFunc);
    $('#fileupload').fileupload({
        dataType: 'json',
        formData: [ { name: 'foo', value: 7}, {name: 'bar', value: 'baz'}],
        done: function (e, data) {
        	if (typeof data.result.files == 'undefined') {
        		alert(data.result.message);
        	}
        	else {
        		$.each(data.result.files, function (index, file) {
        			alert( 'got '+file.name+' '+file.size+' bytes');
        		});
        	}
		},
	    progressall: function (e, data) {
  			var progress = parseInt(data.loaded / data.total * 100, 10);
        	$('#progress .bar').css('width',progress + '%');
        }
    });
});
</script>

</body>

</div>
