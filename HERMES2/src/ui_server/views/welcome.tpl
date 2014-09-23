%rebase outer_wrapper _=_,title_slogan=_('HERMES Graphical User Inferface Start'),inlizer=inlizer

<style>
#sp_top_div{
	position: relative;
	width:"100%";
	top: 0px;
	left: 0px;
	border-style: none;
	border-width: 2px;
	text-align: center;
}
#sp_content_div{
	position: relative;
	width:80%;
	float:none;
	margin: 0 auto;
}

</style>

<div id="sp_top_div" class="sp_top_div">
	<div id="sp_content_div" class="content_div">
		<div class = "options_div">
			<p><h1 style="text-align:left">{{_("Choose Your Desired Action")}}</h1></p>
			<table width = "100%" border = 0>
				<tr>
					<td rowspan=2 width=90><a href="{{rootPath}}model-create" ><img src='{{rootPath}}static/icons/pencil.png' width=80></a></td>
					<td><h2 style="margin-bottom:0px;"><a href="{{rootPath}}model-create" >{{_("Create a New Model")}}</a></h2></td>
				</tr>
				<tr>
					<td><h3 style="margin-top:0px;">{{_("Walk through and enter data through designated steps to create a set of inputs that can create a simulated supply chain.")}}</h3></td>
				</tr>
				<tr height=20><td></td></tr>
				<tr>
					<td rowspan=2 width=90><a href="{{rootPath}}models-top"><img src='{{rootPath}}static/icons/network.png' width=80></a></td>
					<td><h2 style="margin-bottom:0px;"><a href="{{rootPath}}models-top">{{_("Work with a Previously Created Model")}}</a></h2></td>
				</tr>
				<tr>
					<td><h3 style="margin-top:0px;">{{_("Edit, Create Scenarios, and/or Run a previously saved model.")}}</h3></td>
				</tr>
				<tr height=20><td></td></tr>
				<tr>
					<td rowspan=2 width=90><img src='{{rootPath}}static/icons/users.png' width=80></td>
					<td><h2 style="margin-bottom:0px;">{{_("HERMES Tutorials")}}</h2></td>
					</tr>
				<tr>
					<td><h3 style="margin-top:0px;">{{_("Learn how to use HERMES")}}</h3></td>
				</tr>
				<tr height=20><td></td></tr>
				<tr>
					<td rowspan=2 width=90><a href="{{rootPath}}results-top"><img src='{{rootPath}}static/icons/stats.png' width=80></a></td>
					<td><h2 style="margin-bottom:0px;"><a href="{{rootPath}}results-top">{{_("Compare Results from Previous Models")}}</a></h2></td>
				</tr>
				<tr>
					<td><h3 style="margin-top:0px;">{{_("View and compare results. <Need better wording>")}}</h3></td>
				</tr>
				<tr height=20><td></td></tr>
				<tr>
					<td rowspan=2 width=90><img src='{{rootPath}}static/icons/folders.png' width=80></td>
					<td><h2 style="margin-bottom:0px;">{{_("Explore Information Databases")}}</h2></td>
				</tr>
				<tr>
					<td><h3 style="margin-top:0px;">{{_("Browse through HERMES database of vaccines, refrigerators, freezers, cold boxes and transport vehicles.")}}</h3></td>
				</tr>
				<tr height=20><td></td></tr>
			</table>
		</div>
	</div>
</div>
<!--<div class="art-postcontent art-postcontent-0 clearfix">
  <div class="art-content-layout">
	<div class="art-content-layout-row">
	  <div class="art-layout-cell layout-item-0" style="width: 33%" >
	    <p style="text-align: center; font-size: 16px; font-weight: bold; color: #FB8B13;"><span style="color: #303269;">{{_('Vision')}}</span></p>
	    <p style="text-align: center;"><img width="166" height="127" alt="" class="art-lightbox" src="static/images/tmpF14D.png"><br></p>
	    <p style="text-align: center;"><a href="http://hermes.psc.edu/vision.html" class="art-button">{{_('Read more')}}</a></p>
	  </div>
	  <div class="art-layout-cell layout-item-0" style="width: 34%" >
        <p style="text-align: center; font-size: 16px; font-weight: bold; color: #1864C9;"><span style="color: #303269;">{{_('Team')}}</span></p>
        <p style="text-align: center;"><img width="185" height="63" alt="" class="art-lightbox" src="static/images/HERMESTeam.png" style="margin-top: 38px; margin-bottom: 39px;"><br></p>
        <p style="text-align: center;"><a href="http://hermes.psc.edu/team.html" class="art-button">{{_('Read more')}}</a></p>
      </div>
      <div class="art-layout-cell layout-item-0" style="width: 33%" >
	    <p style="font-size: 16px; font-weight: bold; text-align: center; color: #878787;"><span style="color: #303269;">{{_('Publications')}}</span></p>
	    <p style="text-align: center;"><img width="180" height="124" alt="" class="art-lightbox" src="static/images/Benin_ZS_Rota_Util_sm.jpg"><br></p>
	    <p style="text-align: center;"><a href="http://hermes.psc.edu/publications.html" class="art-button">{{_('Read more')}}</a></p>
	  </div>
    </div>
  </div>
  <div class="art-content-layout">
    <div class="art-content-layout-row">
	  <div class="art-layout-cell layout-item-1" style="width: 100%" >
	    <h3><span style="vertical-align: sub; color: #303269;">{{_('A Computational Tool to Design, Plan and Improve Supply Chains')}}</span></h3>
	    <p>{{_('Supply chains are the series of steps involved in transporting vaccines from manufacturers all the way to patients.&nbsp; Distributing vaccines (and other health care products) can be a complex process, integrating many steps, locations, personnel, and equipment.&nbsp; HERMES (Highly Extensible Resource for Modeling Supply-chains) is a computational framework for modeling and optimizing supply chains.')}}</p>
	    <p style="text-align: center;">{{_('The HERMES Project is a collaboration involving...')}}<br></p>
	    <p style="text-align: center;"><img width="79" height="79" alt="" class="art-lightbox" src="static/images/pitt_bluegold_seal1.gif">&nbsp; &nbsp;&nbsp;<img width="211" height="79" alt="" class="art-lightbox" src="static/images/PSClogo_secondary.png"><br></p>
	    <p style="text-align: center;">{{_('Funded through grants from the Bill and Melinda Gates Foundation and the National Institutes of Health.')}}</p>
	  </div>
    </div>
  </div>
</div>-->
