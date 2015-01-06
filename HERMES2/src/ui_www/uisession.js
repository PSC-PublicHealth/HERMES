var defaultNLevels = 4;               	
var defaultShippattern = ["false","false","true",12,'year'];
var defaultLevelCount = 1;
var defaultTransitTimes = 1;
var defaultTransitUnits = 'hour';
var defaultTransitDist = 5.0;

function defaultLevelName(i){
	return "Level " + i;
};

function defaultLevelNames(n){
	levelNames = [];
	for(var i=0;i<n;i++)
		levelNames.push(defaultLevelName(i+1));
	return levelNames;
};

function defaultLevelCounts(n){
	levelCounts = [];
	for(var i=0;i<n;i++)
		levelCounts.push(defaultLevelCount);
	return levelCounts;
};

function defaultShippatterns(n){
	shippatterns = [];
	for(var i=0;i<n;i++)
		shippatterns.push(defaultShippattern);
	
	return shippatterns;
};

function defaultShipTransitTimes(n){
	shiptimings = [];
	for(var i=0;i<n;i++)
		shiptimings.push(defaultTransitTimes);
	
	return shiptimings;
};

function defaultShipTransitUnits(n){
	shiptimeunits = [];
	for(var i=0;i<n;i++)
		shiptimeunits.push(defaultTransitUnits);
	
	return shiptimeunits;
};

function defaultShipTransitDist(n){
	shiptimedist = [];
	for(var i=0;i<n;i++)
		shiptimedist.push(defaultTransitDist);
	
	return shiptimedist;
}


function ModelInfo(name_,nLevels_,levelNames_,levelCounts_,shippatterns_,shiptransittimes_,
                   shiptransitunits_,shiptransitdist_,canonicalstoresdict_, canonicalroutesdict_, 
                   potrecdict_, pottable_, modelId_, firstTime_){
	this.name = name_;
	this.changed = false;
	this.firstTime = typeof firstTime_ !== 'undefined' ? firstTime_ : false;
	this.nlevels = typeof nLevels_ !== 'undefined' ? nLevels_ : defaultNLevels;
	this.levelnames = typeof levelNames_ !== 'undefined' ? levelNames_: defaultLevelNames(this.nlevels);
	this.levelcounts = typeof levelCounts_ !== 'undefined' ? levelCounts_ : defaultLevelCounts(this.nlevels);
	this.shippatterns = typeof shippatterns_ !== 'undefined' ? shippatterns_ : defaultShippatterns(this.nlevels-1);
	this.shiptransittimes = typeof shipttransittimes_ !== 'undefined' ? shiptransittimes_ : defaultShipTransitTimes(this.nlevels-1);
	this.shiptransitunits = typeof shiptranistunits_ !== 'undefined' ? shiptransitunits_ : defaultShipTransitUnits(this.nlevels-1);
	this.shiptransitdist = typeof shiptransitdist_ !== 'undefined' ? shiptransitdist_ : defaultShipTransitDist(this.nlevels-1);
	this.canonicalstoresdict =typeof canonicalstoresdict_ != 'undefined'? canonicalstoresdict_ :{};
	this.canonicalroutesdict = typeof canonicalroutesdict_ != 'undefined' ? canonicalroutesdict_ : {};
	this.potrectdict = typeof potrecdict_ != 'undefined' ? potrecdict_ : {};
	this.pottable = typeof pottable_ != 'undefined' ? pottable_ : [];
 	this.modelId = typeof modelId_ != 'undefined' ? modelId_ : -1;
	this.toJsonNetwork = function(){
		return makeNetworkJson(0,this);
	};
	
//	this.toJsonGrid = function(){
//		var json = {'total':1,'page':1,'records':this.nlevels,'rows':[]};
//		for(var i = 0; i < this.)
//		                                                             
//	}
//	
	this.changeNumberOfLevels = function(newNLevels){
		var difference = newNLevels - this.nlevels;
		console.log("Difference = " + difference);
		if (difference > 0){
			//alert("will add " + difference + " levels");
			this.addLevels(difference);
		}
		else if(difference < 0){
			//alert("will sub " + difference + " levels");
			this.subtractLevels(-difference);
		}
	};
	
	this.addLevels = function(n){
		for(var i=0;i<n;i++){
			this.levelnames.push(defaultLevelName(this.nlevels + i + 1));
			this.levelcounts.push(defaultLevelCount);
			this.shippatterns.push(defaultShippattern);
			this.shiptransittimes.push(defaultTransitTimes);
			this.shiptransitunits.push(defaultTransitUnits);
			this.shiptransitdist.push(defaultTransitDist);
		}
		this.nlevels += n;
	};
	
	this.subtractLevels = function(n){
		for (var i=0;i<n;i++){
			this.levelnames.pop();
			this.levelcounts.pop();
			this.shippatterns.pop();
			this.shiptransittimes.pop();
			this.shiptransitunits.pop();
			this.shiptransitdist.pop();
		}
		this.nlevels -= n;	
	};	
	
	this.updateSession = function(rootPath){
		if(this.changed){
			this.potrectdict = {};
			this.pottable = {};
			console.log("changed");
		}
		console.log(this);
		return $.ajax({
					url:rootPath + 'json/update-uisession-modelInfo',
					datatype:'json',
					type:'post',
					data:JSON.stringify(this)
				}).promise();
	};
		
};


//	function changeLevels
//};

function ModelInfoFromJson(json){
	var modelInfo = new ModelInfo(json.name,json.nlevels);
	
	modelInfo.firstTime = false;
	if(json.hasOwnProperty('firstTime'))
		modelInfo.firstTime = json.firstTime == "T" ? true: false;
		//typeof json.firstTime !== 'undefined' ? firstTime_ == "T" ? true: false : false;
	
	if ( json.hasOwnProperty('levelnames'))
		modelInfo.levelnames = json.levelnames;
	//else 
	//	delete modelInfo.levelnames;

	if ( json.hasOwnProperty('levelcounts'))
		modelInfo.levelcounts = json.levelcounts;
	//else 
	//	delete modelInfo.levelcounts;
	
	if ( json.hasOwnProperty('shippatterns')){
		if (json.shippatterns[0].length == 0){
			json.shippatterns.shift();
			//alert("ill formed shippattern");
		}
		
		modelInfo.shippatterns = json.shippatterns;
	}
	//else 
	//	delete modelInfo.shippatterns;
		
	if ( json.hasOwnProperty('shiptransittimes'))
		modelInfo.shiptransittimes = json.shiptransittimes;
	//else 
	//	delete modelInfo.shiptransittimes;
	
	if ( json.hasOwnProperty('shiptransitunits'))
		modelInfo.shiptransitunits = json.shiptransitunits;
		
	if ( json.hasOwnProperty('shiptransitdist'))
		modelInfo.shiptransitdist = json.shiptransitdist;
	//else 
	//	delete modelInfo.shiptransitunits;

	if ( json.hasOwnProperty('canonicalStoresDict'))
		modelInfo.canonicalstoresdict = json.canonicalStoresDict;
		
	if ( json.hasOwnProperty('canonicalRoutesDict'))
		modelInfo.canonicalroutesdict = json.canonicalRoutesDict;
	
	if ( json.hasOwnProperty('potrecdict'))
		modelInfo.potrecdict = json.potrecdict;
		
	if ( json.hasOwnProperty('pottable'))
		modelInfo.pottable = json.pottable;
	
	if ( json.hasOwnProperty('modelId'))
		modelInfo.modelId = json.modelId;
	return modelInfo;
};



function makeNetworkJson(i,modelInfo){
	console.log(i);
	if (i == modelInfo.nlevels-1){
		return {'name': modelInfo.levelnames[i],'count':modelInfo.levelcounts[i]};
				//'isfixedam':modelInfo.shippatterns[i][0],'isfetch':modelInfo.shippatterns[i][1],
				//"issched":modelInfo.shippatterns[i][2],"interv":modelInfo.shippatterns[i][3],"ymw":modelInfo.shippatterns[i][4]};
	}
	else {
		return {'name': modelInfo.levelnames[i],'count':modelInfo.levelcounts[i],
				'isfixedam':modelInfo.shippatterns[i][0],'isfetch':modelInfo.shippatterns[i][1],
				"issched":modelInfo.shippatterns[i][2],"interv":modelInfo.shippatterns[i][3],"ymw":modelInfo.shippatterns[i][4],
				"time":modelInfo.shiptransittimes[i],'timeunit':modelInfo.shiptransitunits[i],'distance':modelInfo.shiptransitdist[i],
				'children':[makeNetworkJson(i+1,modelInfo)]};
	}
}

function ajax_update_modelInfoSession(modelInfo, rootPath){
	return $.ajax({
		url:rootPath + 'json/update-uisession-modelInfo',
		datatype:'json',
		type:'post',
		data:JSON.stringify(modelInfo)
	}).promise();
};





