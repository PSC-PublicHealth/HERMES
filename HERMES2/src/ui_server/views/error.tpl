%rebase outer_wrapper title_slogan=_("Bug!"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer

<!---
-->

<h1>{{_('You Have Found A Bug')}}</h1>
{{_("We're sorry - you have found a bug.  The details are below.  Please use your browser's 'back' button.")}}
<p>
<div>
{{bugtext}}
</div>

<script>
$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>
