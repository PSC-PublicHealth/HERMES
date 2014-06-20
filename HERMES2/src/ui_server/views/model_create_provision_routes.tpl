%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs, _=_, inlizer=inlizer

<h1>{{_('What Are The Details Of Each Transport Route?')}}</h1>
{{_('The shipping network for {0} has been created, but details must be specified for shipping between levels.').format(name)}}
{{_('All routes at a given level will be equipped as you describe below.  You can modify individual routes by editing the model.')}}
<p>
<form>
  	<table>

		% for i,(l1name,l2name) in enumerate(zip(levelnames[:-1],levelnames[1:])):
	  	<tr>
	  		<td>{{_("For routes between levels")}}</td>
	  		<td>
			<button id="model_create_provroute_b_{{i}}">{{_("{0} and {1}").format(l1name,l2name)}}</button>
			<div id="model_create_dlg_{{i}}">
				<div id="model_create_div_{{i}}"></div>
			</div>
			</td>
  		</tr>
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
		window.location = "{{rootPath}}model-create/next?provisionroutes=true";  // settings already sent via ajax
	});
});

$(function () {
	var btn;
	% i = 0
	% for i,(l1name,l2name) in enumerate(zip(levelnames[:-1],levelnames[1:])):
		$("#model_create_provroute_b_{{i}}").button()
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
				'title':'{{_("Editing prototype for all routes between levels {0} and {1} of model {2}").format(l1name,l2name,name)}}'				
			});
			$('#model_create_div_{{i}}').hrmWidget({
				widget:'routeEditor',
				modelId:{{modelId}},
				routename:'{{canonicalRoutesDict[(l1name,l2name)].RouteName}}',
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
