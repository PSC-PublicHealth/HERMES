%rebase outer_wrapper title=_('Look! This page has tabs!'),title_slogan=_('UI Experiments'),_=_,inlizer=inlizer
<!---
-->

<div id='toptabs'>
<ul>
%for ref,lbl in topLevelTabPairs:
<li><a href="{{rootPath}}{{ref}}">{{lbl}}</a></li>
%end
</ul>
</div> <!-- closes toptabs -->

<script>
  /*
  * Create top-level tabs.  Produce an error if we can't get the page associated with a tab
  */
  $(function() {
    $( "#toptabs" ).tabs({
      beforeLoad: function( event, ui ) {
        ui.jqXHR.error(function() {
          ui.panel.html("Couldn't load this tab. We'll try to fix this as soon as possible.");
        });
      }
    });
  });
</script>
