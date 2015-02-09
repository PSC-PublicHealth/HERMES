%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs, _=_, inlizer=inlizer
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
<h1>{{_('How Many Locations At Each Level?')}}</h1>
{{_('How many locations exist at each of the following levels?  We will distribute them evenly between suppliers at the level above, and then give you a chance to make adjustments.')}}
<p>
<form>
  	<table>
	  	<tr>
  			<td><label for="model_create_lcounts_1">{{levelnames[0]}}</label></td>
  			<td><input type="number" name="model_create_lcounts_1" id="model_create_lcounts_1" value=1 disabled></td>
  		</tr>

%if defined('levelnames'):
%    if defined('levelcounts') and len(levelcounts)==len(levelnames):
%        i = 2
%        for lname,lcount in zip(levelnames[1:],levelcounts[1:]):
	  	<tr>
  			<td><label for="model_create_lcounts_{{i}}">{{lname}}</label></td>
  			<td><input type="number" name="model_create_lcounts_{{i}}" id="model_create_lcounts_{{i}}" value={{lcount}} min="1"></td>
  		</tr>
%            i += 1
%        end
%    else:
%        for i,lname in enumerate(levelnames[1:]):
	  	<tr>
  			<td><label for="model_create_lcounts_{{i+2}}">{{lname}}</label></td>
  			<td><input type="number" name="model_create_lcounts_{{i+2}}" id="model_create_lcounts_{{i+2}}" value="1" min="1"></td>
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

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_('One or more level values is blank or lower than 1; please fix this.')}}</p>
</div>

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
		   var s = "model_create_lcounts_"+(i+1);
		   var sval = $("#"+s).val();
		   if (sval && parseInt(sval) > 0) {
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
	});

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
 