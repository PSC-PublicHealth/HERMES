;(function($){
	$.widget("results_widgets.vsgrid",{
		options:{
			resultsId:-1,
			modelId:-1,
			scrollable:false,
			resizable:true,
			trant:{
				title:"Vaccine Summary Grid"
			}
		},
		
		hideMinor:function(){
			this.containerID = $(this.element).attr('id');
			console.log("Cont: "+this.containerID);
			$("#"+this.containerID).jqGrid('hideCol',["percooler",'perfreezer','dosespervial']);
		},
		showMinor:function(){
			this.containerID = $(this.element).attr('id');
			console.log("Cont: "+this.containerID);
			$("#"+this.containerID).jqGrid('showCol',["percooler",'perfreezer','dosespervial']);
		},
		_create:function(){
			
			trant = this.option.trant;

			this.containerID = $(this.element).attr('id');
			var containerID = this.containerID;
			
			var resultsId = this.options.resultsId;
			var modelId = this.options.modelId;
			
			var chartData = this.options.jsonData;
			
			var phrases = {0:'Vaccine',
			               1:'Availability',
			               2:'Vials Used',
			               3:'Doses Per Vial',
			               4:'Doses Demanded',
			               5:'Doses Administered',
			               6:'Open Vial Waste',
			               7:'Percent Stored 2 to 8 C',
			               8:'Percent Stored Below 2C',
			               9:'Vials Spoiled',
			               10:'Vaccine Results'};
			
			 translate_phrases(phrases)
			 	.done(function(tphrases){
			 		console.log("summary");
			 		console.log(tphrases);
			 		var tp = tphrases.translated_phrases;
			 		console.log(modelId + " " + resultsId);
			 		$("#"+containerID).jqGrid({ //set your grid id
				 	   	url:'json/results-summary?modelId='+modelId+'&resultsId='+resultsId+'&resultType=vaccines',
				 		datatype: "json",
				 		jsonReader: {
				 			root:'rows',
				 			repeatitems: false,
				 			id:'vaccid'
				 		},
                        // set sortable to false until either servier-side or client-side data model supports it
				 		sortable: false, 
				 	    caption:tp[10],
				 		width: 'auto', //specify width; optional
				 		height:'auto',
				 		autowidth:'true',
				 		colNames:[
				 			"ID",
				 			tp[0],
				 			tp[1],
				            tp[2],
				            tp[3],
				            tp[4],
				            tp[5],
				            tp[6],
				            tp[7],
				            tp[8],
				            tp[9]
				 		], //define column names
				 		colModel:[	
				 		          {
				 		        	  name:'vaccid',
				 		        	  index:'vaccid',
				 		        	  jsonmap:'vaccid',
				 		        	  hidden:true, 
				 		        	  key:true
				 		          },
				 		          {
				 		        	  name:'name',
				 		        	  index:'name',
				 		        	  jsonmap:'DisplayName',
				 		        	  width:150,
				 		        	  sortable:true,
				 		        	  sorttype:'text'
				 		          },
				 		          {
				 		        	  name:'availability',
				 		        	  index:'availability',
				 		        	  jsonmap:'SupplyRatio',
				 		        	  width:75,
				 		        	  formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; if(value < 0.0){ value=0.0;}; return value.toFixed(2) + "%"},
				 		        	  align:'right'
				 		          },
				 		          {
				 		        	  name:'vialsused',
				 		        	  index:'vialsused',
				 		        	  jsonmap:'VialsUsed',
				 		        	  width:75,
				 		        	  formatter:'number',
				 		        	  align:'right',
				 		        	  formatoptions:{decimalPlaces:0}
				 		          },
				 		          {
				 		        	  name:'dosespervial',
				 		        	  index:'dosespervial',
				 		        	  jsonmap:'DosesPerVial',
				 		        	  width:50,formatter:'number',
				 		        	  align:'right',
				 		        	  formatoptions:{decimalPlaces:0}
				 		          },
				 		          {
				 		        	  name:'dosesrequested',
				 		        	  index:'dosesrequested',
				 		        	  jsonmap:'Applied',
				 		        	  width:75,
				 		        	  formatter:'number',
				 		        	  align:'right',
				 		        	  formatoptions:{decimalPlaces:0}
				 		          },
				 		          {
				 		        	  name:'dosesadmin',
				 		        	  index:'dosesadmin',
				 		        	  jsonmap:'Treated',
				 		        	  width:85,
				 		        	  formatter:'number',
				 		        	  align:'right',
				 		        	  formatoptions:{decimalPlaces:0}
				 		          },
				 		          {
				 		        	  name:'ovw',
				 		        	  index:'ovw',
				 		        	  jsonmap:'OpenVialWasteFrac',
				 		        	  width:75,
				 		        	  formatter: function(cellvalue,options,rowObject){
				 		        	  					value = cellvalue*100.0; 
				 		        	  					if(value < 0.0){ value=0.0;}; 
				 		        	  					return value.toFixed(2) + "%";
				 		        	  			},
				 		        	  align:'right'
				 		          },
				 		          {
				 		        	  name:'percooler',
				 		        	  index:'percooler',
				 		        	  jsonmap:'coolerStorageFrac',
				 		        	  width:75,
				 		        	  formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; return value.toFixed(2) + "%";},
				 		        	  align:'right'
				 		          },
				 		          {
				 		        	  name:'perfreezer',
				 		        	  index:'perfreezer',
				 		        	  jsonmap:'freezerStorageFrac',
				 		        	  width:75,
				 		        	  formatter: function(cellvalue,options,rowObject){value = cellvalue*100.0; return value.toFixed(2) + "%"},
				 		        	  align:'right'
				 		          },
				 		          {
				 		        	  name:'vialspoiled',
				 		        	  index:'vialsspoiled',
				 		        	  jsonmap:'VialsExpired',
				 		        	  width:75,
				 		        	  formatter:'number',
				 		        	  align:'right',
				 		        	  formatoptions:{decimalPlaces:0}
				 		          }
				 		], //define column runs
				 		gridview: true // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
			 	}).jqGrid('hermify',{debug:true, resizable_hz:true});
			 });
		}
	});
})(jQuery);
	

			
			
