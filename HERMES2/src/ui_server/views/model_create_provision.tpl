%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs, _=_, inlizer=inlizer

<h1>{{_('What Equipment And Population Exist At Each Level?')}}</h1>
{{_('The shipping network for {0} has been created, but equipment and population must be specified at each level.').format(name)}}
{{_('All locations at a given level will be equipped as you describe below.  You can modify individual locations by editing the model.')}}
<p>
<form>
  	<table>

		% i = 0
		% for lname,lcount in zip(levelnames,levelcounts):
	  	<tr>
	  		% if lcount==1:
	  		<td>{{_("For the location at level:")}}</td>
	  		% else:
	  		<td>{{_("For the locations at level:")}}</td>
	  		% end
	  		<td>
			<button id="model_create_prov_b_{{i}}">{{lname}}</button>
			<div id="model_create_dlg_{{i}}">
				<div id="model_create_div_{{i}}"></div>
			</div>
			</td>
  		</tr>
		% i += 1
		% end

    </table>

    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
      </tr>
    </table>
</form>

<script>
$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/back"
	});
});
	
$(function() {
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/next?provision=true";  // settings already sent via ajax
	});
});

$(function () {
	var btn;
	% i = 0
	% for lname in levelnames:
		$("#model_create_prov_b_{{i}}").button()
		.click(function(event) {
			event.preventDefault();
			$('#model_create_dlg_{{i}}').dialog({
				autoOpen:false, 
				height:"auto", 
				width:"auto",
				buttons: {
	    			Ok: function() {
						$( this ).find('form').submit();
		   	 		},
	    			Cancel: function() {
	      				$( this ).dialog( "close" );
	    			}
				},
				'title':'{{_("Editing prototype for all {0} locations of model {1}").format(lname,name)}}'				
			});
			$('#model_create_div_{{i}}').hrmWidget({
				widget:'storeEditor',
				modelId:{{modelId}},
				idcode:{{canonicalStoresDict[lname]}},
				closeOnSuccess:'model_create_dlg_{{i}}',
				afterBuild:function() { 
					$('#model_create_dlg_{{i}}').dialog('open'); 
				}
			});


		});
	% i += 1
	% end
});

</script>
