<h3>Model Creation</h3>
<p>Most healthcare supply chains have a hierarchical structure. Products 
originate at one high-level location, where they are stored for some time 
before they are distributed sequentially to lower levels. 
Eventually -- when the products reach the lower-most level of the supply chain --
they are used or administered to patients (e.g. vaccines are often administered 
at clinics comprising the lowest level of a vaccine supply chain). 
The number of levels in a supply chain indicates the number of distinct groups of 
locations that can store or administer products, and varies depending on the system 
being modeled; higher-order levels supply products to lower-order levels. Often, 
supply chain levels reflect administrative or geographical boundaries of the country 
or region of interest. For example, a model of the vaccine supply chain 
in Benin would include four levels: National, Department, Commune, and Health Post. 
Vaccines originate at the National store and are transported to Department stores, 
then to Commune stores, and finally to Health Posts where they are administered to 
patients.

<p>HERMES model creation uses levels to group locations into categories with similar 
characteristics. For example, shipping policies are initially set for all transport
routes between adjacent levels (e.g. for Benin, all routes between the National and 
Department stores would initially be assigned identical policies). 
All of these settings can me modified after the basic model structure is created via 
the <b>Make Adjustments</b> table or in even further detail via the <b>Advanced Model Editor</b>.</p>