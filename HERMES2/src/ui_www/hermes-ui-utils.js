function check_developer_mode(rootpath){
	return $.ajax({
		url:rootpath + 'json/check-devel-mode',
		datatype:'json'
	}).promise();
};
	
function new_model_copy_name(name){
	// first match if there is a paratheses number at the en
	var namePar = name.match(/\(([^)]+)\)$/);
	if(namePar){
		var nameInv = name.replace(namePar[0],'');
		console.log(nameInv);
		console.log(namePar[0]);
		var number = parseInt(namePar[0].replace('(',''));
		return nameInv + "("+(number+1) + ")";
	}
	else{
		return name + "(1)";
	}
}

function translate_phrases(phrases){
	return $.ajax({
				url:'json/translate',
				dataType:'json',
				data:phrases,
				type:'post'
			}).promise();
}
	
