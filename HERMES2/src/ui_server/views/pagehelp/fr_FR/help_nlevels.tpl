<h2>{{_('Model Creation Workflow')}}</h2>
<br>
<!--<h3>Introduction</h3>
<p>Most healthcare supply chains have a hierarchical structure. Products 
originate at one high-level location, where they are stored for some time 
before they are distributed sequentially to lower levels. 
Eventually when the products reach the lower-most level of the supply chain --
they are used or administered to patients (e.g. vaccines are often administered 
at health clinics, which comprise the lowest level of vaccine supply chains). 
The number of levels in a supply chain indicates the number of distinct groups of 
locations that can store or administer products, and varies depending on the system 
being modeled; higher-order levels supply products to lower-order levels. Often, 
supply chain levels reflect administrative or geographical boundaries of the country 
or region of interest. For example, a supply chain model of the vaccine supply chain 
of Benin would include four levels: National, Department, Commune, and Health Post. 
Vaccines originate at the National store and are transported to Department stores, 
then to Commune stores, and finally to Health Posts where they are administered to 
patients.</p>
<br>
<br>
<p>HERMES Model Creation Workflow uses levels to group locations into categories with similar characteristics. For example, shipping policies are initially set for all transport routes between adjacent levels (e.g. for Benin, all routes between the National and Department stores are identical). All of these settings can me modified after the basic model structure is created via the Optionally Make Adjustments Page or in even further detail via the HERMES Edit-a-model workflow.</p>
<br><br>-->

<p>{{_('On this page, you will be asked to answer three basic questions that will define the structure of your supply chain. Please answer each question and click next to progress to the next question.  You will be able to come back here later and alter any informationyou have entered.')}}</p>
<br>
{{_('How many levels does the supply chain have?')}}
<br>{{_('Each supply chain is made up of a number of levels.  The number of levels in a supply chain is the the number of storage locations that a vaccine or health product passes through from entering the supply chain to location in which it is used.')}}
<br><br>

{{_('What are the names of the supply chain levels?')}}
<br>
{{_('This is generally dependent on the supply chain your are modeling.  Some example names are already given and you should change them to match the supply chain you are modeling. (e.g. in Benin, what is commonly referred to as the Distict level in many countries is called Commune due to their naming of administration units in the country.')}}
<br><br>
{{_('How many locations are at each level?')}} 
<br>
{{_('This number should indicate the total number of storage, administration, and outreach locations at each level in the supply chain.  HERMES will attempt to automatically distribute these amongst the locations.  For example, if you declare there are 2 locations in the second level and 9 locations in the third level, HERMES will assign 4 of locations at the lower level to be connected to the first location in the second level, and the other 5 to be connected to the second.  You will have a chance to alter this in a later step through the Make Adjustments table.')}}
			



