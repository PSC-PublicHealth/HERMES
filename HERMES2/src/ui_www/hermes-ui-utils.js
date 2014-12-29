function check_developer_mode(rootpath){
	return $.ajax({
		url:rootpath + 'json/check-devel-mode',
		datatype:'json'
	}).promise();
};
	
