%rebase outer_wrapper title_slogan=_("Create {0}").format(name), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<script src="{{rootPath}}static/d3/d3.min.js"></script>
<script src="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.js"></script>
<link rel="stylesheet" href="{{rootPath}}static/tree-layout-diagram/tree-layout-diagram.css"/>
<script>

function makeNetworkJson(i,levelInfo){
	if (i == (Object.getOwnPropertyNames(levelInfo).length - 1)){
		return {'name':levelInfo[i].n,'count':levelInfo[i].c,'focus':levelInfo[i].f};
	}
	else {
		return {'name':levelInfo[i].n,'count':levelInfo[i].c,'focus':levelInfo[i].f,'children':[makeNetworkJson(i+1,levelInfo)]};
	}
}
// This function updates the network diagram
function updateNetworkDiagram(){
	var levelInfo = {};
	for(var i = 0; i < $("#model_create_nlevels_input").val(); ++i){
		if (typeof $("#model_create_levelname_"+(i+1)).val() == "undefined")
			break;
		//levelNames.push($("#model_create_levelname_"+(i+1)).val());
		var focus = false;
		if($("#model_create_levelname_"+(i+1)).is(':focus')){
				focus = true;
				console.log("This has focus.... damnit");
		}
		levelInfo[i] = {'n':$("#model_create_levelname_"+(i+1)).val(),'c':0,'f':focus};
		if (typeof $("#model_create_lcounts_"+(i+1)).val() == "undefined"){
			levelInfo[i].c = 1;
		}
		else{
			var focus = false;
			if($("#model_create_lcounts_"+(i+1)).is(':focus'))
				focus = true;
			levelInfo[i].c = $("#model_create_lcounts_"+(i+1)).val();
			levelInfo[i].f = focus;
			//levelCount.push($("#model_create_lcounts_"+(i+1)).val());
		}
		
	}
	
	console.log("Levels");
	for(var level in levelInfo){
		console.log(levelInfo[level].n);
	}
	if (Object.getOwnPropertyNames(levelInfo).length == 0){
		nlevels = $("#model_create_nlevels_input").val();
		for (var i=0;i<nlevels;i++){
			levelInfo[i] = {'n':'Level '+i,'c':1,'f':false};
		}
	}
	
	jsonNet = makeNetworkJson(0,levelInfo);
	$("#tree-layout-diagram").remove();
	$("#model_create_diagram").append($("<div id='tree-layout-diagram' name='tree-layout-diagram'/>"));
	$("#tree-layout-diagram").diagram({
	        hasChildrenColor: "steelblue",
	        noChildrenColor: "#ccc",
	        jsonData:jsonNet,
	        minWidth: 768,
	        minHeight: 775,
	        resizable: false,
	        scrollable: true,
	        trant: {
	             "title": "{{_('Model')}}",
	        }
	});
	
	$("#tree-layout-diagram").diagram("zoomBy",0.25);
}
</script>
<h1>{{_('How are goods shipped between levels?')}}</h1>

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
  	    <td><input type="number" id="model_create_interl_howoften_{{i}}" value={{howoften}} min=1></td>
  	    <td>{{_("times per")}}</td>
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
%           prepopval = {3: [4], 4: [2,4], 5: [2,4,6]}
%           try:
%               val = prepopval[nlevels][i]
%           except:
%               val = 1
%           end
%           if i==(nlevels-2): val = 12
  	    <td><input type="number" id="model_create_interl_howoften_{{i+2}}" value="{{val}}" min=1></td>
  	    <td>{{_("times per")}}</td>
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
        <td width 10%><input type="button" id="back_button" value={{_("Previous Screen")}}></td>
        <td></td>
        <td width=10%><input type="button" id="expert_button" value={{_("Skip to Model Editor")}}></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next Screen")}}></td>
      </tr>
    </table>
</form>

<div id="dialog-modal" title={{_("Invalid Entry")}}>
  <p>{{_('One or more of the values are blank; please fix this.')}}</p>
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
 		    if (sval && parseInt(sval) > 0) {
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
 