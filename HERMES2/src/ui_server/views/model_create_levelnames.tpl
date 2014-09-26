%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<h1>{{_("What are the names of the levels in your model?")}}</h1>
{{_('For example, a four level model might have levels named "Central", "Region", "District", and "Health Post".')}}
<p>
<form>
    <table>
%if defined('nlevels'):
%    if defined('levelnames') and len(levelnames)==nlevels:
%        for i,lname in enumerate(levelnames):
	  	<tr>
  			<td><label for="model_create_levelname_{{i+1}}">{{_("Name for level")}} {{i+1}}</label></td>
  			<td><input type="text" name="model_create_levelname_{{i+1}}" id="model_create_levelname_{{i+1}}" value="{{lname}}"></td>
  		</tr>
%        end
%    else:
%        for i in xrange(nlevels):
	  	<tr>
  			<td><label for="model_create_levelname_{{i+1}}">{{_("Name for level")}} {{i+1}}</label></td>
%           prepopval = {3: {1:_("District")}, 4: {1:_("Region"),2:_("District")}, 5: {1:_("Province"),2:_("Region"),3:_("District")}}
%           try:
%               val = prepopval[nlevels][i]
%           except:
%               val = _("Level") + " " + str(i+1)
%           end
%           if i==(nlevels-1): val = _("Health Post")
%           if i==0: val = _("Central")
  			<td><input type="text" name="model_create_levelname_{{i+1}}" id="model_create_levelname_{{i+1}}" value="{{val}}"></td>
  		</tr>
%        end
%    end
%end
    </table>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="expert_button" value={{_("Expert")}}></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title="Invalid Entry">
  <p>One or more level names is blank; please fix this.</p>
</div>

<script>
$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-create/back"
	});
});
$(function() {
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

function validate_inputs() {
		var parms = "";
		var valsOK = true;
		var first = true;
		for (var i=0; i<{{nlevels}}; i++) {
		   var s = "model_create_levelname_"+(i+1);
		   var sval = $("#"+s).val();
		   if (sval) {
		       if (first) {
		           parms = parms + s + "=" + sval;
		           first = false;
		       }
		       else {
		           parms = parms + "&" + s + "=" + sval;
		       }
		   }
		   else {
		       valsOK = false;
		   }
		}
		if (!valsOK) { parms = null; }
		return parms;
  }

  var btn = $("#expert_button");
  btn.button();
  btn.click( function() {
		var parms = validate_inputs();
		if (parms != null) {
			window.location = "{{rootPath}}model-create/next?"+parms+"&expert=true";
		}
		else {
			$("#dialog-modal").dialog("open");
		}
	})
  
	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		var parms = validate_inputs();
		if (parms != null) {
			window.location = "{{rootPath}}model-create/next?"+parms;
		}
		else {
			$("#dialog-modal").dialog("open");
		}
	});
});

</script>
 