/*
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
*/
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

function translate_phrases(phrases,rootPath){
	if(typeof rootPath === 'undefined') rootPath = ""
	return $.ajax({
				url:rootPath + 'json/translate',
				dataType:'json',
				data:phrases,
				type:'post'
			}).promise();
}
	
function get_existing_model_names(){
	return $.ajax({
		url:'json/get-existing-model-names',
		dataType:'json'
	}).promise();
}

function get_model_name_from_id(id){
	return $.ajax({
		url:'json/get-model-name?modelId='+id,
		dataType:'json'
	}).promise();
};
	
function get_alltypesmodelId(){
	return $.ajax({
		url:'json/get-alltypesmodel-id',
		data:'json'
	}).promise();
}

// objects that have the known types for HERMES

var typesAllowed = ['fridges','trucks','vaccines','people','staff','perdiems'];

var typeInfoUrls = {
		'fridges':'json/fridge-info',
		'trucks':'json/truck-info',
		'vaccines':'json/vaccine-info',
		'people':'json/people-info',
		'staff': 'json/staff-info',
		'perdiems':'json/perdiem-info'
	};
