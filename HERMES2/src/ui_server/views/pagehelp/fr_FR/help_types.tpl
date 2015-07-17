<p>{{_('Select the components to include in this model. These components will later be assigned to locations and routes: This will occur in a later step if using the Model Creation workflow, or in the Advanced Model Editor if editing an existing model. Toggle between component categories (vaccines, transport equipment, storage equipment, population types, per diem policies, and staff types) using the buttons on the left.')}} 
</p>
<br><br>
<p>
{{_('Selecting a Source')}}:
</p><br> 
<p>
{{_('Items in the currently open model appear in the box on the left, and items available to add to this model appear in the Source box on the right. Use the dropdown menu to select a Source. Available sources include the HERMES Database as well as other models in your database. The HERMES Database includes WHO prequalified items where available, as well as examples of commonly used items.')}}
</p>
<br><br>
<p>
{{_('Adding and Removing Items in the Current Model')}}:
</p><br> 
<p>
{{_('To add an item from a Source, click the item in the Source to select it and click the arrow button in the middle to copy the item to the current model. To add an item not available in any Source, begin with an item of the same component category in the current model (if there are currently no items in that category, add one from any Source). Use the Edit button to modify the item as necessary. Unless the name of the item is modified, any changes will replace the original item in the current model. Modifying the name of the item will add the modified version to the current model while also keeping the original item in the model. Remove any item from the current model using the Del button.')}}
</p>
<br><br>
<p>
{{_('Vaccines')}}: 
</p>
<br>
<p>
{{_('The HERMES Database lists WHO prequalified vaccines by antigen, followed by manufacturer and primary container size (doses per vial). Vaccines with WHO listed as the manufacturer indicate WHO International Shipping Guidelines. These guidelines indicate the maximum recommended packaged volume per dose for various types of vaccines, and these can be used when the actual manufacturer supplying vaccines is not known. Vaccine characteristics in HERMES include the doses per vial, presentation (such as liquid or lyophilized), potent lifetimes (frozen, refrigerated, at room temperature, and after opening), packaged volume per dose (for vaccine and diluent), and price per vial. All vaccine types to be administered at any location should be added to the model in this step.')}}
</p>
<br><br>
<p>
{{_('Transport')}}: 
</p>
<br>
<p>
{{_('The HERMES Database includes commonly used vehicle types. These examples include a refrigerated truck, which has a net cold storage capacity. Other vehicles that lack refrigeration include cold boxes and vaccine carriers. Transport device characteristics in HERMES include the storage capacity (either net volume or devices), purchase price, expected lifetime mileage, fuel type, and fuel consumption rate. Transportation methods such as public transit and walking can also be added here. For transit types that have a fixed fare associated with them (such as bus fare for public transportation), the Fuel specified should be Fixed Fare and the round-trip fare should be entered in Fuel Consumption. For transit types that incur no transportation cost, such as walking, the Fuel Type specified should be No Fuel. All transport methods used to move vaccines at any location should be added to the model in this step.')}}
</p>
<br><br>
<p>
{{_('Storage')}}: 
</p>
<br>
<p>
{{_('The HERMES Database includes WHO prequalified storage equipment, as well as commonly used devices. WHO prequalified equipment is listed by model, with a prefix of "CB" for cold boxes and "VC" for vaccine carriers. Commonly used devices include a 30 cubic meter walk-in cold room and a freezer room of the same size. Storage device characteristics in HERMES include the make, model, net volume for storing vaccines (cooler or 2-8C, freezer, and room temperature), type of equipment, purchase price, expected lifetime, energy type, energy usage rate, and holdover time during a power outage. All storage devices used at any location to store vaccines should be added to the model in this step.')}}
</p>
<br><br>
<p>
{{_('Population')}}: 
</p>
<br>
<p>
{{_('The HERMES Database includes commonly used population groups, typically based on age. All individuals in a population group require the same vaccines. The population at each immunizing location is also entered (in a different step) in terms of these population groups. While an actual vaccine schedule may specify doses at specific weeks or months of age, population groups should be specified based on the level of detail of available population data. For example, assume doses of one particular vaccine are recommended at 2 months and 8 months of age. In most cases, data is not available on the size of the population at each immunizing location at each of those specific ages, so there is no benefit to entering these as separate population groups. However, data may be available on the number of infants under 1 year of age, so one population type for that broader age group can be assigned to receive all vaccine doses scheduled for those infants. All population groups who are immunized at any location should be added to the model in this step.')}}
</p>
<br><br>
<p>
{{_('Per Diem Rules: 
</p>
<br>
<p>
{{_('The HERMES Database includes one example per diem rule for routes, which specifies that no per diem be paid for trips that occur. In any given system, there may be multiple per diem policies across different levels of the supply chain. For example, drivers on routes at higher levels may be paid per diems, while drivers on routes at lower levels may not. All per diem policies used in any route should be added to the model in this step.  Per diem policies in HERMES are specified based on the amount paid per day, whether a trip must take longer than one day in order for a per diem to be paid, whether a per diem is paid for the first day of a trip or only for the additional days, and any minimum one-way distance required for a per diem to be paid.')}}
</p>
<br><br>
<p>
{{_('Staff')}}: 
</p>
<br>
<p>
{{_("The HERMES Database includes examples of commonly used staff types. In HERMES, staff only affect cost outcomes. Thus, the same model run with and without staff will produce results that only differ in labor/personnel costs. Staff type characteristics in HERMES include annual salary and the fraction of that salary that should be counted toward the costs of the immunization program modeled. For example, if only including costs related to EPI logistics, then the percentage of each staffmember's time that is dedicated toward EPI logistics would be reported. All staff types to be included in labor costs at any location should be added to the model in this step.")}}
</p>