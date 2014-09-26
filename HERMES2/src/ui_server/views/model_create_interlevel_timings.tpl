%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<h1>{{_('What are the typical travel times between levels?')}}</h1>

<p>
<form id="model_create_timing_form">
  	<table>
%if defined('levelnames'):
%	for count,(supplier,client) in enumerate(zip(levelnames[:-1],levelnames[1:])):
		<tr>
		<td>{{_('A typical one-way trip from')}}</td>
		<td><b>{{supplier}}</b></td>
		<td>{{_('to')}}</td>
		<td><b>{{client}}</b></td>
		<td>{{_('takes')}}</td>
		<td><input type="number" id="model_create_timing_{{count}}" name="model_create_timing_{{count}}" min=1></td>
		<td><select id="model_create_timing_units_{{count}}" name="model_create_timing_units_{{count}}">
  	        <option value="year">{{_('Years')}}</option>
  	        <option value="month">{{_('Months')}}</option>
  	        <option value="week">{{_('Weeks')}}</option>
  	        <option value="day">{{_('Days')}}</option>
  	        <option value="hour">{{_('Hours')}}</option>
  	     </select></td>
		</tr>
%   end
%end
    </table>
</form>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="expert_button" value={{_("Expert")}}></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
      </tr>
    </table>

<div id="dialog-model"></div>

<script>
$(':input[type=number]').bind('mousewheel DOMMouseScroll', function(event){
  var val = parseInt(this.value);
  var maxattr = $(this).attr("max");
  var minattr = $(this).attr("min");
  if (event.originalEvent.wheelDelta > 0 || event.originalEvent.detail < 0) {
    if (typeof maxattr == typeof undefined || maxattr == false || val < maxattr) {
      this.value = val + 1;
    }
  }
  else {
    if (typeof minattr == typeof undefined || minattr == false || val > minattr) {
      this.value = val - 1;
    }
  }
  event.preventDefault(); //to prevent the window from scrolling
});

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/back"
	});
});

$(function() {

	function fillForm(data) {
		for (var i in data.times) $('#model_create_timing_'+i.toString()).val(data.times[i]);
		for (var i in data.units) $('#model_create_timing_units_'+i.toString()).val(data.units[i]);
		return true;
	};
	
	$.getJSON('{{rootPath}}json/model-create-timing-formvals')
	.then( function(data) {
			if (data.success) return fillForm(data);
			else return $.Deferred().reject(data).promise();
		})
	.done ( function(data) { /* Nothing to do */ } )
	.fail( reportError );
	
	$("#dialog-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				$( this ).dialog( "close" );
        	}
        }
	});

	var btn = $("#expert_button");
	btn.button();
	btn.click( function() {
		var dict = {};
		$("#model_create_timing_form input,select").each( function( index ) {
			var tj = $(this);
			dict[tj.attr('id')] = tj.val();
		});
		$.getJSON("{{rootPath}}json/model-create-timing-verify-commit",dict)
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					window.location = "next?expert=true";
				}
				else {
					$("#dialog-modal").text(data['msg']);
					$("#dialog-modal").dialog("open");
				}
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
		
	});

	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		var dict = {};
		$("#model_create_timing_form input,select").each( function( index ) {
			var tj = $(this);
			dict[tj.attr('id')] = tj.val();
		});
		$.getJSON("{{rootPath}}json/model-create-timing-verify-commit",dict)
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					window.location = "next";
				}
				else {
					$("#dialog-modal").text(data['msg']);
					$("#dialog-modal").dialog("open");
				}
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
		
	});
});

</script>
 