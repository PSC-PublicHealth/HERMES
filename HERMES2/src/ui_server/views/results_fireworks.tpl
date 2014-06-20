%rebase outer_wrapper title_slogan=_('Examine Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<table>
<tr>
<td  style="border-style:solid">
<h1 align='center'>{{modelName}} {{resultsGroupName}} {{_("run")}} {{runNum}}</h1>
<div id="results_fireworks_div" style="width:600px;height:600px"></div>
</td>

<td  style="border-style:solid">
<h3>{{_('Drag to pan; use mouse wheel to zoom.')}}</h3>
<table>
<tr><td><button id="reset_button" style="width:100%" >{{_('Click to Reset')}}</button></td></tr>
<tr>
  <td>
    <form id="show_what_form">
    	<table>
    		<tr><th>{{_("Color by which value?")}}</th></tr>
    		<tr><td><input type="radio" name="show" value="fill">{{_("Storage Fill Levels")}}</input></td></tr>
		    % for v in vaccineList:
    			<tr><td><input type="radio" name="show" value="{{v}}">{{_("{0} Supply Ratio").format(v)}}</input></td></tr>
    		% end
    	</table>
    </form>
  </td>
</tr>
</table>
</td>
</tr>
</table>

<script src="{{rootPath}}static/jquery-migrate-1.2.1.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery-svg-1.4.5/jquery.svg.js"></script>
<script src="{{rootPath}}static/jquery-svgpan.js"></script>

<script>

$(function() {
	var $radios = $("input:radio[name=show]");
	if ($radios.is(':checked') === false) {
		$radios.filter('[value=fill]').prop('checked', true);
	}
	
});

$(function() {
	function nodeClick(evt, elt) {
		var titleElt = elt.getElementsByTagName('title')[0];
		var titleTxt = titleElt.childNodes[0].nodeValue;
		alert('click on node with id '+titleTxt.substring(2,titleTxt.length));
	}

	function edgeClick(evt, elt) {
		var titleElt = elt.getElementsByTagName('title')[0];
		var titleTxt = titleElt.childNodes[0].nodeValue;
		var arrow = titleTxt.indexOf('>');
		var fromN = titleTxt.substring(2,arrow-1);
		var toN = titleTxt.substring(arrow+3,titleTxt.length);
		alert('click on edge with ids '+fromN+' and '+toN);
	}

	function addClicksRecursively(elt) {
		if (elt.id) {
			if (elt.id.substring(0,4)=='node') {
				if (elt.addEventListener) {
					elt.addEventListener('click', function(event) { nodeClick(event, elt); });
				} else {
					elt.attachEvent('onclick', function(event) { nodeClick(event, elt); })
				}
			}
			else if (elt.id.substring(0,4)=='edge') {
				if (elt.addEventListener) {
					elt.addEventListener('click', function(event) { edgeClick(event, elt); });
				} else {
					elt.attachEvent('onclick', function(event) { edgeClick(event, elt); })
				}
			}
		}
		for (var i = 0; i<elt.children.length; i++) {
			var kid = elt.children[i];
			if ($.svg.isSVGElem(kid) && kid.tagName == 'g') { 
				addClicksRecursively(kid);
			}
		}
	}

	var originalCTM;
	var curCTM = null;

	function drawIntro(svg) { 
		$(svg.root()).svgPan('graph1',true,true,false,0.1);
		addClicksRecursively(svg.root());
		var g = $(svg.root()).find('#graph1')[0];
		originalCTM = g.getCTM();
		if (curCTM) setCTM(g,curCTM);
	}

	function setCTM(element, matrix) {
		element.transform.baseVal.consolidate();

    	// The goal is to set element.transform to some matrix T='mat2' such that the new CTM is equal to the
    	// given input matrix.  The expression we need for 'mat2' is T=(newCTM)*(inverse(oldCTM))*oldT .
    	var mat2 = element.transform.baseVal.getItem(0).matrix.multiply(element.getCTM().inverse()).multiply(matrix);
    	element.transform.baseVal.replaceItem(element.transform.baseVal.createSVGTransformFromMatrix(mat2), 0);
	};

	function reloadGraph() {
		var value = $('input:radio[name=show]:checked').val();
		var vaxStr;
		if (value && value!='fill') {
			vaxStr="&vax="+value;
		}
		else {
			vaxStr="";
		}
		if ($('#results_fireworks_div').svg('get')) {
			var g = $($('#results_fireworks_div').svg('get').root()).find('#graph1')[0];
			curCTM = g.getCTM();
			$('#results_fireworks_div').svg('get').load(
				'{{rootPath}}svg/fireworks?resultsId={{resultsId}}'+vaxStr,
				{ onLoad: drawIntro }
			);
		}
		else {
			$('#results_fireworks_div').svg({
				onLoad: drawIntro,
				loadURL: '{{rootPath}}svg/fireworks?resultsId={{resultsId}}'+vaxStr,
			});
		}
	};

	reloadGraph();

	var btn = $("#reset_button");
	btn.button();
	btn.click( function() {
		var g = $($('#results_fireworks_div').svg('get').root()).find('#graph1')[0];
		setCTM(g,originalCTM);
	});
	
	$('#show_what_form').change( function() { reloadGraph(); } );
});

  
</script>
 