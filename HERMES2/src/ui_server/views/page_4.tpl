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
<div id='tabs-4'>
<h2>{{_('This will be my table')}}</h2>

<body>	
	<table id="grid"></table>
	<div id="pager" </div>

<script>
/*
var mydata = [
    { id : {{_("one")}}, {{_("name")}} : {{_("row one")}} },
    { id : {{_("two")}}, {{_("name")}} : {{_("row two")}} },
    { id : {{_("three")}}, {{_("name")}} : {{_("row three")}} }
]; 
*/


$("#grid").jqGrid({ //set your grid id
   	url:'json/show-table',
	datatype: "json",
	//data: mydata, //insert data from the data object we created above
	//datatype: 'local',
	width: 500, //specify width; optional
	colNames:['Id','Name'], //define column names
	colModel:[
	{name:'id', index:'id', key: true, width:50},
	{name:'name', index:'name', width:100}
	], //define column models
	pager: '#pager', //set your pager div id
	sortname: 'id', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Zâ€� optional
	sortorder: "asc", //sort order; optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
    caption:{{_("JSON Example")}}
});
</script>
</body>

</div>