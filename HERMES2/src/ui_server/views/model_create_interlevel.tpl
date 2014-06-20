%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<h1>{{_('How are goods shipped from level to level?')}}</h1>

<p>
<form>
  	<table>
  	    <tr>
  	    <th>{{_('Level')}}</th>
  	    <th colspan=2>{{_('How are vaccines obtained?')}}</th>
  	    <th colspan=3>{{_('How often?')}}</th>
  	    </tr>
%if defined('levelnames'):
%    if  defined('shippatterns') and len(shippatterns) == len(levelnames):
%        i = 2
%        for lname,ptuple in zip(levelnames[1:],shippatterns[1:]):
%            isfetch,issched,howoften,ymw = ptuple
  	    <tr>
  	    <td>{{lname}}</td>
  	    <td><select id="model_create_interl_isfetch_{{i}}">
%            if isfetch:
  	        <option value="false">{{_('Receives Deliveries')}}</option><option value="true" selected>{{_('Picks Up Vaccines')}}</option>
%            else:
  	        <option value="false" selected>{{_('Receives Deliveries')}}</option><option value="true">{{_('Picks Up Vaccines')}}</option>
%            end
  	    </select></td>
  	    <td><select id="model_create_interl_issched_{{i}}">
%            if issched:
  	        <option value="true" selected>{{_('On A Fixed Schedule')}}</option><option value="false">{{_('As Needed')}}</option></select></td>
%            else:
  	        <option value="true">{{_('On A Fixed Schedule')}}</option><option value="false" selected>{{_('As Needed')}}</option></select></td>
%            end
  	    <td><input type="number" id="model_create_interl_howoften_{{i}}" value={{howoften}}></td>
  	    <td>times per</td>
  	    <td><select id="model_create_interl_ymw_{{i}}">
%            if ymw == 'year':
  	        <option value="year" selected>{{_('Year')}}</option><option value="month">{{_('Month')}}</option><option value="week">{{_('Week')}}</option>
%            elif ymw == 'month':
  	        <option value="year">{{_('Year')}}</option><option value="month" selected>{{_('Month')}}</option><option value="week">{{_('Week')}}</option>
%            else:
  	        <option value="year">{{_('Year')}}</option><option value="month">{{_('Month')}}</option><option value="week" selected>{{_('Week')}}</option>
%            end
  	    </select></td>
  	    </tr>
%            i += 1
%        end
%    else:
%        for i,lname in enumerate(levelnames[1:]):
  	    <tr>
  	    <td>{{lname}}</td>
  	    <td><select id="model_create_interl_isfetch_{{i+2}}">
  	        <option value="false">{{_('Receives Deliveries')}}</option><option value="true">{{_('Picks Up Vaccines')}}</option>
  	    </select></td>
  	    <td><select id="model_create_interl_issched_{{i+2}}">
  	        <option value="true">{{_('On A Fixed Schedule')}}</option><option value="false">{{_('As Needed')}}</option></select></td>
  	    <td><input type="number" id="model_create_interl_howoften_{{i+2}}" value=1></td>
  	    <td>times per</td>
  	    <td><select id="model_create_interl_ymw_{{i+2}}">
  	        <option value="year">{{_('Year')}}</option><option value="month">{{_('Month')}}</option><option value="week">{{_('Week')}}</option>
  	    </select></td>
  	    </tr>
%        end
%    end
%end
  		</tr>
    </table>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_('One or more of the values are blank; please fix this.')}}</p>
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

	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		var parms = "";
		var valsOK = true;
		var first = true;
		for (var i=0; i<{{nlevels-1}}; i++) {
		    var s = "model_create_interl_isfetch_"+(i+2);
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
		    s = "model_create_interl_issched_"+(i+2);
		    sval = $("#"+s).val();
 		    if (sval) {
		        parms = parms + "&" + s + "=" + sval;
		    }
		    else {
		        valsOK = false;
		    }
		    s = "model_create_interl_howoften_"+(i+2);
		    sval = $("#"+s).val();
 		    if (sval) {
		        parms = parms + "&" + s + "=" + sval;
		    }
		    else {
		        valsOK = false;
		    }
		    s = "model_create_interl_ymw_"+(i+2);
		    sval = $("#"+s).val();
 		    if (sval) {
		        parms = parms + "&" + s + "=" + sval;
		    }
		    else {
		        valsOK = false;
		    }
		}
		if (valsOK) {
			window.location = "{{rootPath}}model-create/next?"+parms;
		}
		else {
			$("#dialog-modal").dialog("open");
		}
	});
});

</script>
 