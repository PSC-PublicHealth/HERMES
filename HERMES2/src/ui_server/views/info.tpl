%rebase outer_wrapper title_slogan='About HERMES',_=_,inlizer=inlizer,breadcrumbPairs=breadcrumbPairs

<div id="help_accordion">
<!--<h3>External Resources</h3>
<div>
These will open in new windows.
<ul>
<li><a href="https://hermes.psc.edu/hermes/documentation/index.html" target="new">User Documentation</a> for the command line interface<br></li>
<li>Michelle Schmitz&#39;s <a href="https://hermes.psc.edu/hermes/documentation/tutorial/STARTHERE.html" target="new">
Tutorial</a> on running HERMES from the command line. (requires DAV login)</li>
</ul>
</div>-->
<h3>Overview</h3>
<div>
  <p>
  <p><strong>HERMES</strong>, or the Highly Extensible Resource for Modeling Event-Driven Supply Chains, is a software platform that allows users to generate a detailed discrete event simulation model of any vaccine supply chain. This simulation model can serve as a virtual laboratory for decision makers (e.g., policy makers, health officials, funders, investors, vaccine and other technology developers, manufacturers, distributors, logisticians, scientists, and researchers) to address a variety of questions such as:</p>

  <ul>
  <li>What will be the impact of introducing new technologies (e.g., vaccines, storage, or monitoring)?</li>
  <li>What the effects of altering the characteristics of vaccines and other technologies (e.g., vaccine vial size, vaccine thermostability, or cold device capacity)?</li>
  <li>How do the configuration and the operations of the supply chain (e.g., storage devices, shipping frequency, personnel, or ordering policy) affect performance and cost?</li>
  <li>What may be the effects of differing conditions and circumstances (e.g., power outages, delays, inclement weather, transport breakdown, or limited access)?</li>
  <li>How should one invest or allocate resources (e.g., adding refrigerators vs. increasing transport frequency)?</li>
  <li>How can vaccine delivery be optimized (e.g., minimize the cost per immunized child or maximize immunization availability)?</li>
  </ul>

  <p>The user feeds data on the supply chain of interest into HERMES&#39;s standard input deck, such as:</p>

  <ul>
  <li>Supply Chain Structure (e.g., storage locations and shipping routes)</li>
  <li>Storage Devices (e.g., capacity)</li>
  <li>Transport Devices</li>
  <li>Ordering Policies</li>
  <li>Vaccine Characteristics</li>
  <li>Vaccine Demand</li>
  </ul>

  <p>Since HERMES-generated models are detailed simulations (i.e., virtual representations), that the user can choose to pull nearly any type of measure. Examples of common model outputs include:</p>

  <ul>
  <li>Vaccine Availability (i.e., the percentage of clients arriving at an immunization location who are successfully vaccinated)</li>
  <li>Vaccine Wastage</li>
  <li>Storage Capacity Utilization (i.e., the percentage of available space used each day)</li>
  <li>Transport Capacity Utilization</li>
  <li>Number of Stockouts (i.e., the number of times a location runs out of a particular vaccine)</li>
  <li>Vaccine Doses Delivered or Administered</li>
  <li>Time-to-Patient (i.e., vaccine delivery time from top level down to the administration level)</li>
  <li>Costs (derived from Project OPTIMIZE's cost model)</li>
  </ul>

  <p>HERMES can also generate various visualizations, such as:</p>

  <ul>
  <li>A Google Earth storage or transport map</li>
  <li>Stock/inventory diagrams at a particular location</li>
  </ul>
  </p>
</div>
<h3>How It Works</h3>
<div>
  <p>
  <p>The HERMES graphical user interface (GUI) is a tool to help users input data into the HERMES model. It consists of a series of webpages dedicated to helping users input data into HERMES, running HERMES from a web-based platform and obtaining data from HERMES outputs.</p>

  <p>Currently, the <b>Models</b> page contains the majority of the functionality in developing a HERMES model. It is responsible for inputting data files into HERMES, through either guiding a user through a questionnaire, or helping users use an existing HERMES country model as a starting point.</p>

  <p>The Models page contains the following categories:</p>
  <ul>
  <li><b>Create A Model from Scratch</b>: This button will guide the user to an easy-to-user questionnaire, to help the user input their own country&#39;s data in a form accessible to the HERMES model.</li>
  <li><b>Copy An Existing Model</b>: This button will create a new copy of a model, selected from the menu on the right-hand side of the <b>Model</b> page. This new copy of the model can be edited by the user (see <b>Modify An Existing Model</b>).</li>
  <li><b>Modify An Existing Model</b>: With this feature, a user can modify features of either an existing country model, or a copy of an existing model, to allow for different scenarios to be implemented.</li>
  <li><b>Upload a Zip Model</b>: This feature allows a user to upload already-created model spreadsheets in HERMES, zipped up using the HERMES --use_zip feature, to be run in the GUI setting.</li>
  <li><b>Delete Selected Model</b>: Selecting a model, then clicking the button, will delete the selected model from the menu on the right-hand side of the Models page.</li>
  </ul>

  <p>Other pages that will be used in the GUI are either <b>Run HERMES</b> (used to run the selected model files in the HERMES program) or <b>Results</b> (where model outputs and reports will be displayed).</p>

  <em>How Does HERMES Work?</em>

  <p>The model can represent every storage location, immunization location, storage device, transport vehicle/device, personnel, vaccine vial, and vaccine accessory in a supply chain. The model represents each vaccine vial, diluent vial, or vaccine accessory with an entity, which can assume a variety of characteristics such as type, size, number of doses per vial, temperature profile, age, and expiration date.  Millions of different vaccine vials and accessories can flow through the model simultaneously just like a real supply chain. There is practically no limit to the number of vaccines, storage locations, devices, and vehicles that the model can simulate.</p>

  <p>At each immunization location, virtual people arrive each day when they are ready to receive a particular vaccine or set of vaccines. The policy at that location determines when the health workers open vaccine vials and, if necessary, reconstitute the vaccines. (The user can specify policies for each immunization location). The client arrival rates can come from either actual demand data or census plus birth data. If the correct vaccine is available at the immunization location then the person is successfully immunized. If the vaccine is not available, then the person counts as a missed vaccination opportunity. Once an immunization occurs, the remaining vial and accessories count as medical waste. Unused doses in open vaccine vials count as open vial wastage.</p>
</div>
<!--<h3>Notes: things not to forget</h3>
<div>
<ul>
<li>Some jqGrids should have 'show expert columns'</li>
<li>The function that initially recieves a request should check access privileges on incoming requests from the client.
<li>We need some consistent policy about what exception type to return when.
<li>Replace all instances of alert('Error:') with alert('{{_("Error:")}}')

</ul>
</div>-->
</div>

<script>
$( "#help_accordion" ).accordion({collapsible: true, heightStyle:"content"});
$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>
