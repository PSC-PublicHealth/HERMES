%rebase outer_wrapper title_slogan='About HERMES',_=_,inlizer=inlizer,breadcrumbPairs=breadcrumbPairs
<!---
-->

<style>
.bulletted_list{
	margin-left: 5em;
	margin-right:5em;
	list-style-type: circle;
}
.ui-tabs.ui-tabs-vertical {
    padding: 0;
    width: 90%
}
.ui-tabs.ui-tabs-vertical .ui-widget-header {
    border: none;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav {
    float: left;
    width: 15em;
    background: #CCC;
    border-radius: 4px 0 0 4px;
    border-right: 1px solid gray;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li {
    clear: left;
    width: 100%;
    margin: 0.2em 0;
    border: 1px solid gray;
    border-width: 1px 0 1px 1px;
    border-radius: 4px 0 0 4px;
    overflow: hidden;
    position: relative;
    right: -2px;
    z-index: 2;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li a {
    display: block;
    width: 100%;
    padding: 0.6em 1em;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li a:hover {
    cursor: pointer;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li.ui-tabs-active {
    margin-bottom: 0.2em;
    padding-bottom: 0;
    border-right: 1px solid white;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li:last-child {
    margin-bottom: 10px;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-panel {
    float: left;
    width: 75%;
    border-left: 1px solid gray;
    border-radius: 0;
    position: relative;
    left: -1px;
}
.option_em{
	font-weight:bold;
	color:#5053AF;
}
</style>
<div id="main_help_tabs">
	<ul>
		<li><a href="#help_overview">{{_("Overview")}}</a></li>
		<li><a href="#help_user_guide">{{_("User Guide")}}</a></li>
		<li><a href="#help_tutorials">{{_("Tutorials")}}</a></li>
		<li><a href="#help_license">{{_("License")}}</a></li>
	</ul>
	<div id="help_overview">
		<p>
			<h2>Overview of HERMES</h2>
			<hr>
		  	<strong>HERMES</strong>, or the Highly Extensible Resource for Modeling Event-Driven Supply Chains, 
		  	is a software platform that allows users to generate a detailed discrete event simulation model of any vaccine 
		  	supply chain. This simulation model can serve as a "virtual laboratory" for decision makers (e.g., policy makers, 
		  	health officials, funders, investors, vaccine and other technology developers, manufacturers, distributors, 
		  	logisticians, scientists, and researchers) to address a variety of questions such as:
		  </p>
	
		  <ul class="bulletted_list">
			  <li>{{_('What will be the impact of introducing new technologies (e.g., vaccines, storage, or monitoring)?')}}</li>
			  <li>{{_('What the effects of altering the characteristics of vaccines and other technologies (e.g., vaccine vial size, vaccine thermostability, or cold device capacity)?')}}</li>
			  <li>{{_('How do the configuration and the operations of the supply chain (e.g., storage devices, shipping frequency, personnel, or ordering policy) affect performance and cost?')}}</li>
			  <li>{{_('What may be the effects of differing conditions and circumstances (e.g., power outages, delays, inclement weather, transport breakdown, or limited access)?')}}</li>
			  <li>{{_('How should one invest or allocate resources (e.g., adding refrigerators vs. increasing transport frequency)?')}}</li>
			  <li>{{_('How can vaccine delivery be optimized (e.g., minimize the cost per immunized child or maximize immunization availability)?')}}</li>
		  </ul>
		
		  <p>
		  	The model can represent every storage location, immunization location, storage device, transport vehicle/device,
		  		personnel, vaccine vial, and vaccine accessory in a supply chain. The model represents each vaccine vial, diluent vial, 
			  or vaccine accessory with an entity, which can assume a variety of characteristics such as type, size, number of doses per 
			  vial, temperature profile, age, and expiration date.  Millions of different vaccine vials and accessories can flow through 
			  the model simultaneously just like a real supply chain. There is practically no limit to the number of vaccines, storage 
			  locations, devices, and vehicles that the model can simulate.
		  </p>
		
		 
		  <p>
		  	At each immunization location, virtual people arrive each day when they are ready to 
			  receive a particular vaccine or set of vaccines. The policy at that location determines when the health workers 
			  open vaccine vials and, if necessary, reconstitute the vaccines. (The user can specify policies for each immunization 
			  location). The client arrival rates can come from either actual demand data or census plus birth data. If the 
			  correct vaccine is available at the immunization location then the person is successfully immunized. If the vaccine 
			  is not available, then the person counts as a missed vaccination opportunity. Once an immunization occurs, the remaining 
			  vial and accessories count as medical waste. Unused doses in open vaccine vials count as open vial wastage.
		  </p>
	 </div>

	 <div id="help_user_guide">
	      <embed src="{{rootPath}}static/HERMES_User_Guide_3.12.18.pdf" type="application/pdf" width="100%" height=1000 alt="pdf" pluginspage="http://www.adobe.com/products/acrobat/readstep2.html"/>
	      <p>This document is also available <a target=_blank href="http://hermes.psc.edu/release/HERMES_User_Guide_3.12.18.pdf">online</a>.</p>
	 </div>

	 <div id="help_tutorials">
	      <embed src="{{rootPath}}static/HERMES_Tutorials_1-7.pdf" type="application/pdf" width="100%" height=1000 alt="pdf" pluginspage="http://www.adobe.com/products/acrobat/readstep2.html"/>
	      <p>This document is also available <a target=_blank href="http://hermes.psc.edu/release/HERMES_Tutorials_1-7.pdf">online</a>.</p>
	 </div>

	 <div id="help_license">
                <p class='lictitle'>END-USER AGREEMENT</p>
                <p class='licheading'>15 June 2018</p>

                <p class='lictext'>
This End-User Agreement (the Agreement) is between you (User) and The Johns Hopkins University, a Maryland non-stock non-profit corporation (JHU). By purchasing, downloading, accessing, viewing and/or using the HERMES VACCINE LOGISTICS PROGRAM (the Program), User attests that it is over the age of 13, acknowledges that User has read and understands this Agreement in its entirety, and hereby accepts and agrees to be bound by all of its terms and conditions. With respect to this Agreement, the term Program includes all data, information, functions, calculations, and other content in, on, output from or performed by the Program, including, without limitation, all educational, literary, and scientific materials, programs, codes, user interfaces and other software, audio and video content, text, illustrations, photographs, designs, marks and logos, in, on, output from or performed by the Program.
                </p>

                <p class='lictext'>
                    1. <b>License</b>. Upon User窶冱 acceptance of all of the terms and conditions herein, <b>Permission is hereby granted, free of charge, to any User obtaining a copy of this software and associated documentation files (the Software), to deal in the Software without restriction</b>, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  The copyright notice below and this permission notice shall be included in all copies or substantial portions of this software:
</p>
                <p class='lictext' style='text-align:center'>               Copyright © 2018 The Johns Hopkins University, Carnegie Mellon University, The University of Pittsburgh</p>
                <p class='lictext'>
AS FURTHER DESCRIBED BELOW, THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
</p>
                <p class='lictext'>2. <b>Disclaimer of Warranties and Users Assumption of Risk.  </b></p>

                <p class='lictext'> <b>
(a) USER HEREBY AGREES THAT THE USE OF OR INABILITY TO USE, OR RELIANCE ON, THE PROGRAM BY OR ON BEHALF OF USER IS AT USERS SOLE RISK. USER ACKNOWLEDGES THAT THE PROGRAM IS PROVIDED ON AN AS IS AND AS AVAILABLE BASIS. JHU (REFERRED TO HEREINAFTER AS UNIVERSITY OR UNIVERSITIES) MAKES NO GUARANTEES, REPRESENTATIONS OR WARRANTIES WHATSOEVER, AND TO THE FULLEST EXTENT PERMITTED BY LAW, EXPRESSLY DISCLAIMS ALL REPRESENTATIONS AND WARRANTIES, EXPRESS OR IMPLIED OR STATUTORY, WITH RESPECT TO THE PROGRAM, INCLUDING, WITHOUT LIMITATION, REPRESENTATIONS AND WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT OF THIRD-PARTY RIGHTS, QUIET ENJOYMENT, QUALITY, RELIABILITY, ACCURACY, CURRENCY, TIMELINESS, USEFULNESS, COMPLETENESS, SUITABILITY, SATISFACTORY QUALITY, SECURITY AND/OR FUNCTIONALITY. UNIVERSITY MAKES NO GUARANTEES, REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED, THAT THE USE OF THE PROGRAM WILL BE ERROR FREE OR UNINTERRUPTED OR THAT THE PROGRAM WILL BE FREE FROM LOSS, CORRUPTION, INTERFERENCE, HACKING, ATTACK, VIRUSES, OR OTHER SECURITY INTRUSION. UNIVERSITY HEREBY SPECIFICALLY DISCLAIMS ANY LIABILITY RELATING TO THE F
OREGOING AND USER HEREBY ASSUMES AND BEARS THE ENTIRE RISK WITH RESPECT THERETO. BECAUSE SOME JURISDICTIONS DO NOT ALLOW THE EXCLUSION OF IMPLIED WARRANTIES, PORTIONS OF THE ABOVE EXCLUSIONS MAY NOT APPLY TO USER. IN SUCH JURISDICTIONS, THE DURATION AND SCOPE OF THE APPLICABLE WARRANTY WILL BE THE MINIMUM PERMITTED UNDER APPLICABLE LAW.
</b>
</p>

                <p class='lictext'>
(b)User acknowledges that updates to the Program are at the sole discretion of UNIVERSITY and that UNIVERSITY undertakes no obligation to supplement or update the Program. UNIVERSITY makes no guarantees, representations or warranties whatsoever, express or implied, with respect to the compatibility of the Program, or future releases thereof, if any, with any hardware or software, or with respect to the continuity of the features or facilities provided by or through the Program as between various releases thereof, if any.
</p>
                <p class='lictext'><b>
(c) UNIVERSITY SHALL NOT BE LIABLE TO USER OR ANY OTHER INDIVIDUAL OR ENTITY FOR ANY COSTS, EXPENSES, LIABILITIES, PENALTIES, FINES, LOSSES, DAMAGES, DEMANDS, THIRD-PARTY CLAIMS, JUDGMENTS AND/OR OTHER FORMS OF LIABILITY, WHETHER ARISING FROM CONTRACT, PERSONAL OR BODILY INJURY, ILLNESS, OR DEATH, OR TANGIBLE OR INTANGIBLE PROPERTY DAMAGE OR LOSS, OR OTHERWISE (COLLECTIVELY, CLAIMS) IN CONNECTION WITH, ARISING OUT OF OR RELATING TO: (A) ANY USE OF OR INABILITY TO USE, OR RELIANCE ON, THE PROGRAM BY OR ON BEHALF OF USER; (B) ANY MISSTATEMENTS, INACCURACIES, ERRORS, OMISSIONS, DELAYS OR INTERRUPTIONS IN CONNECTION WITH THE PROGRAM; AND/OR (C) ANY DIAGNOSIS, RECOMMENDATION, ADVICE, TREATMENT, PROCEDURE OR OTHER ACTION BY OR ON BEHALF OF USER IN CONNECTION WITH VIEWING, USING OR RELYING ON THE PROGRAM WITH RESPECT TO ANY INDIVIDUAL(S), REGARDLESS OF THE LEGAL BASIS FOR THE CLAIM(S). USER HEREBY ASSUMES AND BEARS THE ENTIRE RISK WITH RESPECT TO THE FOREGOING, AND TO THE FULLEST EXTENT PERMITTED BY LAW, USER RELEASES UNIVERSITIES AND EACH UNIVERSITIES MEMBER (AS HEREINAFTER DEFINED) FROM ANY LIABILITY RELATING TO THE FOREGOING.
</b>
</p>

                <p class='lictext'>3. <b>Limitation of Liability</b>. IN NO EVENT SHALL UNIVERSITY BE LIABLE TO USER OR ANY THIRD-PARTY FOR ANY SPECIAL, INCIDENTAL, CONSEQUENTIAL, PUNITIVE OR INDIRECT DAMAGES IN CONNECTION WITH, ARISING OUT OF, OR RELATING TO THIS AGREEMENT OR THE PROGRAM EVEN IF UNIVERSITY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. BECAUSE SOME JURISDICTIONS DO NOT ALLOW THE EXCLUSION OF OR LIMITATION OF LIABILITY FOR CERTAIN TYPES OF DAMAGES, IN SUCH JURISDICTIONS, UNIVERSITY'S LIABILITY SHALL BE LIMITED TO THE EXTENT PERMITTED BY LAW. NOTWITHSTANDING ANYTHING TO THE CONTRARY HEREIN, UNDER NO CIRCUMSTANCES WILL UNIVERSITY BE LIABLE TO USER OR ANY THIRD-PARTY FOR ANY REASON FOR ANY AMOUNT IN EXCESS OF THE GREATER OF: (A) FIFTY UNITED STATES DOLLARS (US $50); AND (B) THE TOTAL FEES PAID BY USER TO UNIVERSITY, IF ANY, UNDER THIS AGREEMENT (REGARDLESS OF THE LEGAL BASIS FOR THE CLAIM(S)).
</p>
                <p class='lictext'>4. <b>Agreement</b>. This Agreement constitutes the entire agreement between User and JHU regarding the subject matter hereof and supersedes all previous oral or written communications, proposals, agreements and representations, if any, relating to the subject matter hereof. JHU reserves the right to modify this Agreement and to impose new or additional terms or conditions on the access, viewing and use of the Program at any time and in its sole discretion. Such modifications and additional terms and conditions will be effective immediately and incorporated into this Agreement. The continued use of the Program by or on behalf of User will be deemed acceptance thereof. The failure of any party to require the performance of any term or obligation of this Agreement, or the waiver by any party of any breach of this Agreement, will not act as a bar to subsequent enforcement of such term or obligation or be deemed a waiver of any subsequent breach. The provisions of this Agreement will be considered severable, so that the invalidity or unenforceability of any provisions will not affect the validity or enforceability of the remaining provisions; provided that no such severability will be effective if it materially changes the agreement contained herein. The headings contained in this Agreement are for reference purposes only and will not affect in any way the meaning and interpretation of this Agreement. All terms and conditions that by their nature should survive the termination or expiration of this Agreement, including, without limitation, Sections 2, 3, and 4 hereof, will survive. If applicable, User hereby agrees that User will not use or otherwise export the Program in violation or prohibition of United States and any other applicable laws, statutes and regulations.
</p>

                <p class='lictext'>5. <b>Governing Law and Jurisdiction; Waiver of Trial by Jury</b>.  The validity, construction and enforcement of this Agreement, and the use of the Program, will be determined in accordance with the laws of the State of Maryland, without reference to conflicts of laws principles. User and University hereby irrevocably and unconditionally: (i) consent to submit to the exclusive jurisdiction of the courts of the State of Maryland for any proceeding arising in connection with this Agreement and each such party agrees not to commence any such proceeding except in such courts, and (ii) waives any objection to the laying of venue of any such proceeding in the courts of the State of Maryland. <b>EACH OF UNIVERSITY AND USER, KNOWINGLY, FOR ITSELF, ITS SUCCESSORS AND ASSIGNS, WAIVES ALL RIGHT TO TRIAL BY JURY OF ANY CLAIM ARISING WITH RESPECT TO THIS AGREEMENT OR ANY MATTER RELATED IN ANY WAY THERETO.</b>
</p>

                <p class='lictext'><b>BY PURCHASING, DOWNLOADING, ACCESSING, VIEWING AND/OR USING THE PROGRAM, USER ACKNOWLEDGES THAT USER HAS READ AND UNDERSTANDS THIS AGREEMENT IN ITS ENTIRETY, AND HEREBY ACCEPTS AND AGREES TO BE BOUND BY ALL OF THE TERMS AND CONDITIONS SET FORTH HEREIN FOR THE PERMISSION HEREBY GRANTED.</b>
</p>
        </div>




	 </div>
</div>

<script>
$(document).ready(function(){
	$("#main_help_tabs").tabs()
		.addClass('ui-tabs-vertical ui-helper-clearfix');
	
	$('.open-tab').click(function (event) {
	    var tab = $(this).attr('href');
	    var index = $(tab).parent().index();
	    console.log(tab.attr('tabindex'));
	    console.log(navigator.onLine);
	    $('#main_help_tabs').tabs('option','active',index);
	});
});
</script>
