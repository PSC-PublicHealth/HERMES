%rebase outer_wrapper title_slogan=_("Create A Model"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<h1>{{_('Creating Your Model')}}</h1>
{{_("We will want a lot of comforting notes here.  As you finish each page, select the 'Next' button at the bottom right.  Once you have finished this short set of pages, your model will appear in the Models table and you can edit it to add details.  If you leave this sequence of screens too early, your model may not appear in the table but you will be able to return to the sequence where you left off by selecting 'Create A Model From Scratch' again.")}}
<p>
<form>
  	<table>
	  	<tr>
  			<td><label for="model_create_model_name">{{_('Name Your Model')}}</label></td>
  			<td><input type="text" name="model_create_model_name" id="model_create_model_name" 
%if defined('name'):
value={{name}}
%end
  			></td>
  		</tr>
	  	<tr>
  			<td><label for="model_create_nlevels">{{_('How Many Levels In Your Model?')}}</label></td>
  			<td><select name="model_create_nlevels" id="model_create_nlevels">
%if defined('nlevels') and nlevels<=6:
%    for i in xrange(6):
%        if i+1 == nlevels:
  			<option value={{i+1}} selected>{{i+1}}</option>
%        else:
  			<option value={{i+1}}>{{i+1}}</option>
%        end
%    end
%else:
%    for i in xrange(6):
%        if i==3:
  			<option value={{i+1}} selected>{{i+1}}</option>
%        else:
  			<option value={{i+1}}>{{i+1}}</option>
%        end
%    end
%end
  			</select></td>
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
  <p>{{_("The name of the model must not be blank.")}}</p>
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
		var modelName = $("#model_create_model_name").val();
		var modelNLevels = $("#model_create_nlevels").val();
		if (modelName) {
			window.location = "{{rootPath}}model-create/next?name="+modelName+"&nlevels="+modelNLevels;
		}
		else {
			$("#dialog-modal").dialog("open");
		}
	});
});

</script>
 