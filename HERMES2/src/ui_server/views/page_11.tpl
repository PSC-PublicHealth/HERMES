
<div id='tabs-10'>

<body>
<style>
.ui-menu { width: 100px; }
</style>

<h2>{{_('Data Entry Tool')}}</h2>

To completely clear all the data, set 'name' to 'clearall', click outside the field to force a reload, then reload the page.

<table>
	<tr>
		<td><button id="downloadbutton">Download Data</button></td>
		<td></td>
	</tr>
  <tr>
  	<td>
		<button id="newkey">New Key</button>
  	</td>
  </tr>
  <tr>
  	<td>
	  <select id="keymenu" class="ui-menu"></select>
  	</td>
  	<td>
	  <input type="text" id="newval" name="newval">
  	</td>
  </tr>

  <tr>
  	<td colspan="2">
  		<table>
  		<tr>
  			<td>
  				<table id="innertable"></table>
  			</td>
  			<td>
  				<table id="innertable2"></table>
  			</td>
  		</tr>
  		</table>
  	</td>
  </tr>

  <tr>
  	<td colspan="2" style="text-align: center;">
		<button id="savebutton">Save</button>
  	</td>
  </tr>

</table>

<div id="new-key-form" title="Add A Keyword">
<label for="newkeyword">Enter your keyword:</label>
<input type="text" name="newkeyword" id="newkeyword"></input>
</div>

<script>
  $(function() {
  var kvPairs = {};

	function keysInOrder() {
		var keys = $.map(kvPairs, function(value, key) { return key; });
		while (keys.indexOf('name') !== -1) {
			keys.splice(keys.indexOf('name'),1);
		}
		keys.sort();
		keys.splice(0,0,'name');
		console.log(keys);
		return keys;
	};

	function rebuildMenu() {
		$("#keymenu").empty();
		keys = keysInOrder();
		$.each(keys, function(i, key) {
			$("#keymenu").append('<option value="'+key+'">'+key+'</option>');
		});
	};
	
	function tblInsert($tbl, kList) {
		$tbl.empty();
		//$tbl.append("<tr><th><label>Key</label></th><th><label>Value</label></th></tr>");
		$tbl.append("<tr><th>Key</th><th>Value</th></tr>");
		$.each(kList, function(i, k) {
			$tbl.append('<tr><td>'+k+'</td><td>'+kvPairs[k]+'</td></tr>');
		});
	}
	function rebuildTable() {
		var keys = keysInOrder();
		tblInsert($("#innertable"), keys.slice(0,keys.length/2));
		tblInsert($("#innertable2"), keys.slice(keys.length/2));
	};

	$("#keymenu").change( function() {
		var k = $("#keymenu").val();
		if (kvPairs[k]) $("#newval").val(kvPairs[k]);
		else $("#newval").val("");
	});

	$("#newval").blur(function(evt) { 
		if ( $("#newval").val().length>0 ) {
			if ( $("#keymenu").val() == "name") {
				$.getJSON('json/data-entry-get-by-name',{ "name":$("#newval").val() })
				.done(function(data) {
					console.log('fetch data follows');
					console.log(data);
					if (data.success) {
						kvPairs = {};
						$.each(data.value, function(k, v) {
							kvPairs[k] = v;
						});
						$("#keymenu").val("name");
						rebuildMenu();
						rebuildTable();
					}
					else {
						alert('{{_("Failed: ")}}'+data.msg);
					}
    			})
  				.fail(function(jqxhr, textStatus, error) {
  					alert(jqxhr.responseText);
				});
			}
			else {
				kvPairs[$("#keymenu").val()] = $("#newval").val();
				$("#newval").val("");
				rebuildMenu();
				rebuildTable();
			}
		}
	});

	$("#new-key-form").dialog({
		autoOpen: false,
		modal: true,
		buttons: {
			Ok: function() {
				kvPairs[$("#newkeyword").val()] = null;
				$("#newkeyword").val("");
				rebuildMenu();
				rebuildTable();
				$(this).dialog("close");
			},
			Cancel:function() {
				$(this).dialog("close");
			}
		}
	});

	$("#newkey").button().click( function() { $("#new-key-form").dialog("open"); } );

	btn = $("#savebutton");
	btn.button();
	btn.click( function() {
		$.ajax({
			url:'json/data-entry-enter',
			type: 'POST',
			contentType:'application/json',
			data: JSON.stringify(kvPairs),
			dataType:'json',
			success:function(data, textStatus, jqXHR) {
				console.log("data for save success follows");
				console.log(data);
				if (!data.success) {
					alert('Failed: '+data.msg);
				}
			},
			error:function(jqXHR, textStatus, errorThrown) {
				alert(textStatus);
			}
		})
	});
	
	btn = $("#downloadbutton");
	btn.button().click( function(evt) {
		evt.preventDefault();
		window.location.href = 'json/data-entry-download';
	})
	
  $.getJSON('json/data-entry-get-keys')
	.done(function(data) {
		console.log('keys follow');
		console.log(data);
		if (data.success) {
			kvPairs = {};
			$.each(data.keys, function(i, key) {
				kvPairs[key] = null;
			});
			rebuildMenu();
			rebuildTable();
		}
		else {
			alert('{{_("Failed: ")}}'+data.msg);
		}
    })
  	.fail(function(jqxhr, textStatus, error) {
  		alert(jqxhr.responseText);
	});
  });
</script>
</body>

</div>