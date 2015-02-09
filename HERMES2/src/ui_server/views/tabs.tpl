%rebase outer_wrapper title=_('Look! This page has tabs!'),title_slogan=_('UI Experiments'),_=_,inlizer=inlizer
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
